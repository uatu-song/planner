**PSAT Adaptive Practice**

Reading & Writing — System Handoff Document

*Plymouth Scholars Charter Academy  ·  ELA Department  ·  {{SCHOOL_YEAR}}*

| **Purpose of This Document** This document captures the complete architecture, setup, and maintenance procedures for the PSAT Adaptive Practice system built for 8th grade ELA at PSCA. It is intended as a reference for ongoing maintenance, question bank expansion, and future onboarding. |
| --- |

Built with

Google Apps Script  ·  Google Sheets  ·  HTML / CSS / JavaScript

*Designed for Google Sites embedding and direct URL access*

> **Live deployment values (URLs / deploy IDs) are not in this document.** They live in `private/deployment-ids.md` (gitignored). Fill that file with real values; this committed doc stays free of secrets.

# **1. System Overview**

The PSAT Adaptive Practice tool is a web-based quiz application that serves Reading & Writing practice questions to students using an adaptive difficulty engine. It is designed to mirror the logic of the NWEA MAP assessment — difficulty rises as students answer correctly, and skill areas are weighted based on performance.

## **How It Works**

When a student opens the quiz, it silently runs a 4-question calibration round — one question per skill area — to establish a performance baseline. The results are never shown to the student. Based on those results, weaker skill areas receive 3x the question pull weight in the remaining 6 questions. Difficulty scales up every 2 correct answers in a row.

## **Skill Areas**

| **Skill** | **Key Question Types** | **Tag in Spreadsheet** |
| --- | --- | --- |
| Vocabulary in Context | What does the word mean as used here? | vocab |
| Main Idea | What is the central claim or idea? | main |
| Text Structure & Purpose | How is it organized? Why did the author do this? | struct |
| Command of Evidence | Which detail supports / weakens / tests this claim? | evid |

## **Difficulty Tiers**

| **Tier** | **Tag** | **Description** |
| --- | --- | --- |
| Easy | easy | Common vocabulary, direct context, clear signal words. Accessible entry point. |
| Medium | medium | Requires synthesis, strong distractors, belief-vs-reality structures. |
| Hard | hard | Ceiling-level words, causal reasoning, mechanism vs. outcome distinctions. |

## **Adaptive Logic**

| **Condition** | **Result** |
| --- | --- |
| First 4 questions (silent calibration) | One medium question per skill, randomized order |
| Wrong answer on calibration | That skill gets 3x pull weight in adaptive round |
| Correct answer on calibration | That skill gets 1x pull weight (standard) |
| 2 correct in a row (adaptive round) | Difficulty advances one tier |
| Wrong answer (adaptive round) | Streak resets, difficulty holds (does not drop) |
| Reached Hard with no more questions | Falls back to unused questions in any tier |

# **2. Technical Architecture**

The system is built as a standalone Google Apps Script Web App, separate from the Gradebook Hub. It consists of two files in the Apps Script editor and one Google Spreadsheet.

## **Files**

| **File** | **Type** | **Purpose** |
| --- | --- | --- |
| Code.gs | Apps Script | Server-side logic: routing, question reading, submission handling |
| PSATAdaptive.html | HTML Template | The entire quiz UI — styles, markup, and JavaScript |
| PSAT Practice Spreadsheet | Google Sheet | Questions bank (Questions tab) and response log (Responses tab) |

## **How Data Flows**

- Student opens the URL (direct or via Google Sites embed)

- Apps Script serves PSATAdaptive.html, injecting the scriptUrl and userEmail as template variables

- HTML loads in browser; JavaScript calls fetch(scriptUrl + "?action=questions") to get the question bank

- Apps Script reads the Questions sheet and returns all active questions as JSON

- Quiz runs entirely in the browser — no server calls until submission

- On submit, JavaScript POSTs results to scriptUrl using no-cors mode (required for Google Sites iframes)

- Apps Script's doPost() receives the data and appends a row to the Responses sheet

## **Why no-cors?**

Google Sites embeds the quiz in an iframe with cross-origin restrictions. Standard fetch() with CORS fails silently. The no-cors flag bypasses this — the data still reaches the server and gets written to the sheet, but the browser cannot read the response back. This is why the quiz shows an optimistic "Submitted!" message without waiting for confirmation. This is the correct pattern for Apps Script embedded in Sites.

## **Why fetch() Instead of google.script.run?**

google.script.run only works when the page is served directly by Apps Script in its own tab. When embedded in Google Sites, the iframe context breaks it. fetch() with the injected scriptUrl works in both contexts — direct URL and Sites embed.

## **scriptUrl Injection**

The HTML file contains this line near the top of the script:

var SCRIPT_URL = '<?= scriptUrl ?>';

Apps Script's template engine replaces <?= scriptUrl ?> with the live deployment URL at serve time. This means the HTML never has a hardcoded URL — it always points to whatever deployment is currently active. You never need to manually update a URL in the HTML.

# **3. Deployment**

## **Current Deployment**

| **Web App URL** | See `private/deployment-ids.md` (PSAT quiz URL) |
| --- | --- |
| **Execute as** | Me (Joe Song) |
| **Who has access** | Anyone with a Google account |
| **Email collection** | Enabled via Session.getActiveUser().getEmail() |

| **Important: Access Setting** "Anyone with a Google account" is required for email collection. If this is changed to "Anyone," getEmail() returns an empty string and the Email column will be blank in the Responses sheet. |
| --- |

## **How to Deploy a New Version**

You must deploy a new version every time Code.gs or PSATAdaptive.html is changed. The URL does not change between versions.

- Open the Apps Script project

- Click Deploy → Manage Deployments

- Click the pencil (edit) icon on the current deployment

- Change Version to "New version"

- Click Deploy

- The URL remains the same — no changes needed anywhere else

## **Embedding in Google Sites**

- In Google Sites, click Insert → Embed

- Paste the Web App URL

- Click Insert

The quiz will load inside the Sites page. Students must be signed into a Google account — they will be prompted if they are not.

# **4. Question Bank**

## **Spreadsheet Structure**

The question bank lives in the Questions tab of the PSAT Practice spreadsheet. Each row is one question. The spreadsheet has 11 columns:

| **Column** | **Header** | **Valid Values / Notes** |
| --- | --- | --- |
| A | Skill | vocab │ main │ struct │ evid — must match exactly (lowercase) |
| B | Difficulty | easy │ medium │ hard — must match exactly (lowercase) |
| C | Passage | Optional. Leave blank for evidence questions with no passage. |
| D | Question | The full question stem. |
| E | Choice A | First answer choice. |
| F | Choice B | Second answer choice. |
| G | Choice C | Third answer choice. |
| H | Choice D | Fourth answer choice. |
| I | Correct | A, B, C, or D — uppercase letter only. |
| J | Rationale | Explanation shown to student after answering. |
| K | Active | Leave blank to include. Type "no" to exclude without deleting. |

## **Adding Questions**

Adding a question is as simple as adding a row. No code changes, no redeployment required. The quiz reads the spreadsheet fresh on every page load.

- Open the PSAT Practice spreadsheet

- Click the Questions tab

- Scroll to the bottom row with data

- Add a new row with all required columns filled in

- Leave column K (Active) blank

- Reload the quiz — the new question is live immediately

| **Validation Rules** If a row has an invalid skill, difficulty, or correct answer value, or if any required field is blank, the Apps Script silently skips that row. The question will not appear in the quiz and no error will be shown. Always double-check these fields when adding new questions. |
| --- |

## **Deactivating a Question**

To remove a question from the pool without deleting it, type "no" in column K (Active). It will be excluded on the next page load. To reactivate, clear the cell.

## **Current Question Bank — Round 1 (50 Questions)**

| **Skill** | **Easy** | **Medium** | **Hard** | **Total** |
| --- | --- | --- | --- | --- |
| Vocabulary in Context | 4 | 4 | 4 | 12 |
| Main Idea | 4 | 4 | 4 | 12 |
| Text Structure & Purpose | 4 | 5 | 4 | 13 |
| Command of Evidence | 4 | 5 | 4 | 13 |
| TOTAL | 16 | 18 | 16 | 50 |

## **Round 2 — In Progress**

A second set of 10 Vocabulary in Context questions (4 easy, 3 medium, 3 hard) has been written and approved. The CSV file PSAT_QuestionBank_Vocab_Round2.csv contains these rows ready to append to the Questions tab. Main Idea, Text Structure & Purpose, and Command of Evidence rounds are pending.

| **To Import Round 2 Vocab Questions** Open the Questions tab. Copy the 10 rows from PSAT_QuestionBank_Vocab_Round2.csv and paste them at the bottom of the existing data. No header row is included in the file — paste data rows only. |
| --- |

# **5. Responses Sheet**

Every student submission appends one row to the Responses tab. The sheet is created automatically on the first submission if it does not exist.

## **Column Map**

| **Col** | **Header** | **Notes** |
| --- | --- | --- |
| A | Timestamp | ISO 8601 datetime of submission |
| B | Email | Student Google account email — requires "Anyone with a Google account" deployment setting |
| C | Student Name | Self-reported name entered on the start screen |
| D | Score | Raw correct count (e.g. 7) |
| E | Total Questions | Always 10 |
| F | Percent Correct | e.g. "70%" |
| G | Peak Difficulty | Highest difficulty tier reached: easy, medium, or hard |
| H | Total Time (sec) | Raw seconds for the full session |
| I | Total Time (m:ss) | Formatted time e.g. "4:32" |
| J | Vocab Correct |  |
| K | Vocab Total |  |
| L | Vocab Pct |  |
| M | Main Idea Correct |  |
| N | Main Idea Total |  |
| O | Main Idea Pct |  |
| P | Text Structure Correct |  |
| Q | Text Structure Total |  |
| R | Text Structure Pct |  |
| S | Command of Evidence Correct |  |
| T | Command of Evidence Total |  |
| U | Command of Evidence Pct |  |
| V | Question Log (JSON) | Full per-question detail — see below |

## **Question Log (Column V)**

Column V contains a JSON string with one object per question. This is the raw data source for deep per-question analysis. Each object contains:

| **Field** | **Example** | **Notes** |
| --- | --- | --- |
| qNum | 3 | Question number 1–10 |
| skill | Vocabulary in Context | Full skill name |
| skillKey | vocab | Short key used internally |
| difficulty | medium (diag) | "diag" suffix = silent calibration question |
| chosen | B | What the student selected |
| correct | C | The correct answer |
| isCorrect | false | Boolean |
| timeOnQuestion | 14 | Seconds spent on this question |

This data can be parsed with a Google Sheets formula, a Python script, or a future dashboard to answer questions like: which question trips up the most students, which skill takes the longest, what is the average difficulty reached by class.

# **6. Maintenance ****&**** Operations**

## **Routine Tasks**

| **Task** | **How Often** | **Steps** |
| --- | --- | --- |
| Add new questions | Ongoing | Add rows to Questions tab. No redeployment needed. |
| Deactivate a bad question | As needed | Type "no" in column K. Takes effect on next page load. |
| Deploy code changes | After any Code.gs or HTML edit | Deploy → Manage Deployments → Edit → New version → Deploy. |
| Check Responses sheet | Weekly or after test prep sessions | Open spreadsheet → Responses tab. |
| Verify email collection | After any deployment change | Submit a test entry and confirm column B is populated. |

## **Troubleshooting**

| **Symptom** | **Likely Cause** | **Fix** |
| --- | --- | --- |
| "Question bank is empty" on load | Questions sheet name is wrong, or sheet is empty | Confirm tab is named exactly "Questions" (capital Q). Confirm data rows exist below the header. |
| Email column (B) is blank | Deployment access is set to "Anyone" instead of "Anyone with a Google account" | Redeploy with correct access setting. |
| "Submitted!" but no row in Responses | Sheet not created yet, or submission failed silently | Submit a test entry. If Responses tab doesn't appear, check Code.gs for syntax errors. |
| New questions not showing up | Old deployment still cached | Hard refresh the page (Ctrl+Shift+R). If still missing, deploy a new version. |
| Quiz loads but shows wrong questions | Active column has unexpected values | Check column K — only "no" or "false" excludes. Any other value (including "yes") is treated as active. |
| Students can't access the URL | Deployment access changed, or account restriction | Verify deployment is set to "Anyone with a Google account." Check school domain restrictions. |

# **7. Question Writing Standards**

All questions are written following PSAT 8/9 conventions. These standards exist to ensure the bank maintains its integrity as the bank grows through April.

## **General Rules**

- One question per row. Never combine two questions in one stem.

- The correct answer must be provable from the passage or claim — never based on outside knowledge.

- Every distractor must be plausibly wrong, not obviously wrong. Each should exploit a specific common misreading.

- The rationale must explain why the correct answer is right AND why the strongest distractor is wrong.

- No two questions in the same skill/difficulty tier should use the same word or test the same concept.

- Passages should be 1–3 sentences. Longer passages belong in the Text Structure or Evidence skills.

## **Difficulty Calibration Guide**

| **Tier** | **Vocabulary** | **Main Idea** | **Text Structure** | **Command of Evidence** |
| --- | --- | --- | --- | --- |
| Easy | Common words; context confirms directly | Short passage, one clear point | Signal words present (first/next/because) | One detail clearly matches the claim |
| Medium | Words students half-know; strong distractors | Passage requires synthesis across sentences | Author purpose questions; concession/rebuttal structures | Distractor shares topic but misses the specific claim variable |
| Hard | Rare or nuanced words; surface-vs-reality types | Passages that reframe or challenge assumptions | Function of a structural element within a larger argument | Mechanism vs. outcome; two-part evaluative claims |

## **Words Already Used — Vocabulary Bank**

Do not reuse any of the following words in new Vocabulary in Context questions. This list covers all rounds written to date.

**Round 1: **jovial, frugal, respite, vivid, tactful, opaque, lucid, conjecture, equivocal, acerbic, anomalous, ostensibly

**Round 2: **somber, diligent, scarce, tranquil, ambivalent, pragmatic, tenuous, circumspect, perfunctory, inscrutable

# **8. File Inventory**

All files produced during development are documented here.

## **Active Files (in use)**

| **File** | **Location** | **Description** |
| --- | --- | --- |
| Code.gs | Apps Script editor | Server logic. Replace entire contents when updating. |
| PSATAdaptive.html | Apps Script editor | Quiz UI. Replace entire contents when updating. |
| PSAT_QuestionBank.csv | Reference file | All 50 original questions. Import into Questions tab on setup. |
| PSAT_QuestionBank_Vocab_Round2.csv | Reference file | 10 Round 2 vocab questions. Append to Questions tab (no header row). |

## **Companion Tools (separate system)**

| **File** | **Description** |
| --- | --- |
| PSAT_RW_Adaptive.html | Original standalone adaptive quiz — now superseded by the Apps Script version. |
| PSAT_RW_Review.html | 12-question interactive quiz with instant feedback. Dark theme, skill tags, score screen. |
| PSAT_RW_SkillDrills.html | Skill-by-skill drill tool. 4 questions per skill, sidebar navigation, retry per section. |
| PSAT_RW_Blooket.csv | Original 12-question Blooket set (longer stems). Import to Blooket directly. |
| PSAT_RW_Blooket_Short.csv | Shorter Blooket-friendly stems. Correct answers distributed A–D evenly. |
| PSAT_RW_Blooket_Set2.csv | Second Blooket set, variety of skill areas, even A–D distribution. |

## **Development Reference Files**

| **File** | **Description** |
| --- | --- |
| bank_vocab.txt | Original 12 vocab questions with full rationale notes (development reference). |
| bank_main.txt | Original 12 main idea questions with full rationale notes. |
| bank_struct.txt | Original 13 text structure questions with full rationale notes. |
| bank_evid.txt | Original 13 command of evidence questions with full rationale notes. |
| vocab_round2.txt | Round 2 vocab questions with review notes (pre-CSV development file). |

# **9. Roadmap to April PSAT**

## **Question Bank Expansion Plan**

The goal is 10 new questions per skill area per round, written one skill at a time with review before moving to the next. This pace produces 40 new questions per round and allows quality control at each step.

| **Round** | **Status** | **Questions Added** | **Running Total** |
| --- | --- | --- | --- |
| Round 1 (original bank) | Complete | 50 | 50 |
| Round 2 — Vocab | Complete | 10 | 60 |
| Round 2 — Main Idea | Pending | 10 | 70 |
| Round 2 — Text Structure | Pending | 10 | 80 |
| Round 2 — Command of Evidence | Pending | 10 | 90 |
| Round 3 (all skills) | Planned | 40 | 130 |
| Round 4 (all skills) | Planned | 40 | 170 |

## **Planned Enhancements**

- Question Log parser — expand column V JSON into per-question rows in a separate analysis tab

- Class-level dashboard — aggregate Responses data by email domain / class period

- Difficulty distribution report — show which tier each student is reaching on average

- Retake tracking — flag students who have taken the quiz 3+ times for teacher follow-up

- Math section expansion — separate question bank for PSAT Math if demand exists

## **Key Dates**

| **Date** | **Event** |
| --- | --- |
| April 2026 | PSAT 8/9 — target assessment date for all prep materials |
| Ongoing through April | Question bank expansion, one skill set at a time |
| After PSAT | Data analysis of Responses sheet to evaluate tool effectiveness |

# **10. Quick Reference**

## **URLs**

| **Quiz (direct)** | See `private/deployment-ids.md` (PSAT quiz URL) |
| --- | --- |
| **Quiz (Google Sites embed)** | Same URL; paste into Insert → Embed in Sites |
| **Gradebook Hub** | See `private/deployment-ids.md` (Gradebook Hub URL) |

## **Adding a Question — Cheat Sheet**

| **Field** | **What to Enter** |
| --- | --- |
| Skill (col A) | vocab OR main OR struct OR evid |
| Difficulty (col B) | easy OR medium OR hard |
| Passage (col C) | Optional. Leave blank if none. |
| Question (col D) | Full question stem |
| Choice A–D (cols E–H) | Four answer options |
| Correct (col I) | A, B, C, or D (uppercase) |
| Rationale (col J) | Why correct is right; why best distractor is wrong |
| Active (col K) | Leave blank (active). Type "no" to exclude. |

## **Deployment Checklist**

- Changed Code.gs or PSATAdaptive.html? → Deploy a new version

- Changed access setting? → Verify email collection still works

- Added questions to spreadsheet? → No redeployment needed, reload quiz

- Students reporting submission errors? → Check access setting is "Anyone with a Google account"

- Questions not showing up? → Hard refresh, check column A and B values are lowercase, column I is uppercase A/B/C/D

*Document prepared {{SCHOOL_YEAR}}*

*Plymouth Scholars Charter Academy — ELA Department*