# SBG Mastery App — Build Plan

Concrete build plan derived from `SBG_schema.md`. Where the schema and the repo's stated conventions disagree, this plan follows the conventions and flags the deviation. Read alongside `SBG_schema.md` (data model detail), `../context/planning-guide.md` (MTs, tracks), and `../context/year-timeline.md` (unit weeks).

## Decision: architecture

**Google Apps Script + Google Sheets.** Chosen over the schema's recommended cloud stack (Option 1: Postgres + Auth0 + Vercel/Railway) because:
- Student PII (names, parent emails, grades) stays inside NHA's authenticated Google Workspace, where rosters already live; no new cloud PII surface and no district data-privacy sign-off to chase.
- Reuses the PSAT pattern (`PSAT_Adaptive_Handoff.md`): one GAS web app, HtmlService UI, Sheets as store. You already maintain one deployment.
- Reachable from any school machine via Google sign-in; no per-device install.
- Adequate at scale (2 courses, roughly 150 students, about 50 standards).

The repo holds **code and templates only**. The Sheet and its data never get committed; `.gitignore` already blocks `*roster*` and `*grades*.csv`. The Sheet ID and GAS deploy ID go in `private/deployment-ids.md`.

## Guardrails carried from repo conventions (resolve these in the build)

1. **Mastery = highest attempt, not a blend.** The schema's `calculateMastery()` (section 3A) computes a weighted average of the top 3 attempts (0.5/0.3/0.2). That is a blend, and it contradicts the repo convention ("record highest/best attempt, not average") and the SBG philosophy throughout the planning guide. **Build the pure-highest rule:** mastery for a standard = max proficiency achieved (most recent attempt breaks ties), stored as `highest_proficiency`. Drop the weighted blend unless you explicitly want it. The Gradebook Hub already sorts by highest earned skill grade, so pure-highest is already your working practice; reuse that logic, do not rebuild it.
2. **MI-Access students excluded from proficiency denominators.** The schema `students` table has no MI-Access flag. **Add `mi_access` (boolean)**; exclude those students from all class/MT proficiency aggregates while still tracking their individual evidence.
3. **Behavior separated from academic measurement.** Keep behavior out of the `grades`/proficiency tables entirely; if behavior notes are needed, a separate tab, never folded into proficiency.
4. **No em dashes in generated parent/student text** (commas/semicolons); parent-facing warm/professional. Applies to the parent-report generator.

## Data model on Sheets (tabs)

Map the schema's SQL tables to Sheet tabs. Seed tabs are read-only reference; the rest are append/update.

| Tab | Role | Key columns (from schema) |
|---|---|---|
| `standards` | seed | code, category, description, measurement_topic, is_ninth_grade |
| `measurement_topics` | seed | code (MT1-5), name |
| `units` | seed | unit_number, title, weeks, track, essential_question |
| `assignments` | seed/edit | unit_id, name, type, category, week_number, is_retakeable, max_retakes |
| `assignment_standards` | seed/edit | assignment_id, standard_id, is_primary |
| `students` | import | student_id, first/last, parent_email, course, period, **mi_access**, is_active |
| `grades` | append | student_id, assignment_id, standard_id, proficiency_level (1-4), attempt_number, evidence_type, date_assessed |
| `mastery` | derived | student_id, standard_id, highest_proficiency, attempts_count, last_assessed, trend, mastery_date |
| `retakes` | append | student_id, assignment_id, standard_id, status, scheduled_date, prep_evidence |

`mastery` is recomputed from `grades` on write (highest rule); do not hand-edit it.

## Seed data to reconcile before coding

The schema's seed blocks are a strong start but need reconciliation against current source:

- **Both tracks must be seeded.** The schema `UNITS` array encodes only the Gen Ed sequence. The accelerated 8/9 units (Odyssey, Night, Romeo & Juliet, Things Fall Apart) are missing. Seed both tracks from `planning-guide.md`; tag units/standards with track and `is_ninth_grade`.
- **Unit weeks are stale.** Schema has U3 "12-17" and U6 "30-33"; the revised `year-timeline.md` has U3 12-18 and U6 completing by Wk 31, U5 24-28. Seed weeks from `year-timeline.md`, not the schema.
- **Verify unit texts against the curriculum PDFs.** Schema U1 lists "The Dinner Party"; planning-guide U1 lists "The Monkey's Paw, Charles, The Tell-Tale Heart, A Sound of Thunder." Confirm against `../curriculum/` before seeding.
- **NHA export cut scores** (schema 3E: 4→95, 3→85, 2→75, 1→65) are a policy choice. Confirm with NHA's actual conversion before trusting the export.

## Milestones (GAS + Sheets)

- **M0 — Workbook + seed.** Create the Sheet with the tabs above; seed standards, MTs, both-track units/assignments. No UI yet. Output: a populated, correct backbone.
- **M1 — Roster import + grade-entry grid.** Import students from CSV (schema `students.csv` template). Build the grade-entry screen (schema 4: pick assignment, show its standards, enter 1-4 per student in a grid). **This is the daily-use core; it kills the daily pain first.**
- **M2 — Mastery (highest) + mastery grid.** Recompute `mastery` on write using the pure-highest rule; render the per-student MT bars and the class standards heat-map (schema 4).
- **M3 — Retakes + charts.** Retake request/schedule/complete flow (schema 3B rules: max 2, prep required, 3-day wait); growth-over-time and MT dashboards.
- **M4 — Parent report + NHA export.** Generate a printable per-student report (Google Doc/PDF, no em dashes); CSV export to NHA format with confirmed cut scores.
- **M5 — Data import normalizer.** Pull external evidence into `grades`: PSAT Responses column-V JSON, plus NoRedInk and Lexia CSV exports, each mapped once to the 1-4 scale (see `../context/improvement-backlog.md` items 2, 3, 5). Add rubric-based entry for projects/presentations so subjective work flows through the same grid.

**MVP = M0 + M1 + M2.** That gives daily standards-based grade entry and live mastery views, which is the thing that fixes both the workload and the SBG-fidelity pain. M3-M5 layer on after it is in daily use.

## Secrets & PII handling

- Reuse the existing `{{GRADEBOOK_SHEET_ID}}` / `{{GRADEBOOK_GAS_DEPLOY_ID}}` tokens; they point at the Gradebook Hub this app extends. Values live in `private/deployment-ids.md` (gitignored).
- Never commit a roster or grade export. Verify with `git status` before any push.

## Open decisions

1. **Relationship to the Gradebook Hub — resolved.** The Gradebook Hub is an existing Google spreadsheet that already holds your apps for sorting highest-earned skill grade plus related data, referenced by `{{GRADEBOOK_SHEET_ID}}`/`{{GRADEBOOK_GAS_DEPLOY_ID}}`. The SBG app is not a new silo: build it into (or directly linked to) the Hub and reuse the existing highest-skill-grade logic. **Remaining sub-decision:** extend the Hub workbook in place (add tabs plus bound script) vs. a separate workbook that reads it. To choose, I need to see the Hub's current tabs and Apps Script (see the Future input in `../context/improvement-backlog.md`).
2. **Keep pure-highest, or allow the schema's weighted-recent blend as an option?** Default in this plan is pure-highest per convention.
3. **Confirm NHA conversion cut scores** before building the export.
