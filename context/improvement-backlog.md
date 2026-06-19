# Improvement Backlog — Bottlenecks & Opportunities

Living list of choke points and improvement opportunities for this repo and the surrounding workflow. Append as new ones surface; mark status as they get solved. Not year-specific.

## Headline

The **standards-mastery gradebook** is the most-stated, already-designed, still-unbuilt need (see `../infrastructure/SBG_schema.md`). It is the single biggest lever on both stated pains: SBG fidelity and workload. Most items below either feed it or are unblocked by it.

## Grading & data choke points (the workload sinks)

### 1. Standards-mastery gradebook not built
`SBG_schema.md` is a full schema plus an 8-phase build plan; the app does not exist. The two gradebook HTMLs only clean/reformat CSVs; they do not track mastery by standard. **Direction:** build the client-side SBG app; the gradebook HTMLs become its import front-end.

### 2. Subjective / rubric-graded work — projects, presentations, culminating tasks
Canva projects, debates, synthesis essays, and presentations are not auto-scorable. Each needs rubric judgment per student, and SBG requires mapping the rubric to the 1-4 proficiency scale per standard, not a single score. This is a major recurring load the bubble-filler does nothing for.
**Directions:**
- Build standard-aligned rubrics with 1-4 anchors once per project *type* (reuse across the year); the planning guide already calls for "rubrics that align with standards tracking."
- Rubric-entry screen in the SBG app: grade by rubric, auto-map to the relevant MT.
- Reusable Canva project templates so artifacts are consistent and faster to assess.
- Peer-review pre-pass (already in the planning guide) to cut first-pass teacher load.

### 3. External learning platforms — NoRedInk, Lexia
Each platform holds its own progress data behind its own dashboard. Pulling it into the gradebook is manual, and native scoring (mastery %, levels) does not map cleanly to the 1-4 scale. NoRedInk feeds Language (MT 5); Lexia feeds Reading (MT 1 / foundational). Lexia is not yet in the planning-guide tech stack and should be added.
**Directions:**
- Define a fixed mapping from each platform's metric to the 1-4 scale (one-time decision per platform).
- CSV export from each platform into the same normalizer that feeds the SBG app's evidence table (see Opportunity 2).
- Decide which MT each platform is system-of-record for, to avoid re-grading the same skill in two places.

### 4. Bubble pipeline fragility
One template, hardcoded to an 11-question / 1-CR layout; each new assessment means hand-editing `parse_csv` and `detect_bubbles`. No config file, CLI, preview mode, or tests, so the fixed gotchas can silently regress. **Direction:** see Opportunity 3.

### 5. Manual weekly data routine
The planning guide's "export every tool's data into MT evidence folders each week" is entirely manual across Pear Deck, Blooket, NoRedInk, Lexia, and PSAT. **Direction:** see Opportunity 2.

### 6. Accommodation logs
Tracking that accommodations (IEP / 504 / MI-Access) were actually provided per assessment and assignment is manual and compliance-sensitive; an audit wants evidence of delivery, not just a plan on file. The repo has a blank `_TEMPLATE_student_accommodations.md` but no system for logging delivery over time. **Direction:** need a real (de-identified) sample log first to see the actual fields and cadence; then a lightweight log tied to the SBG app's `students` tab (`mi_access` already planned) or a private Sheet. Captured as a Future to-do input below.

## Repo / tooling improvements

- **Two overlapping gradebook tools, no canonical one.** "Complete Processor" vs. "Ultimate Processor" are two iterations of one job. Pick the survivor, archive the other.
- **External systems referenced by token.** The Gradebook Hub is a real existing Google Sheet (apps for sorting highest-earned skill grade plus related data); SongVue and Agenda also have placeholder tokens. These are external by design and their code/tabs are not in the repo. The SBG app extends the Gradebook Hub (see `../infrastructure/SBG_build_plan.md`); document SongVue/Agenda scope when relevant.
- **Manual year-start stamping.** Placeholder replacement is a hand-hunt across files. **Direction:** see Opportunity 5.
- **No CLAUDE.md.** Conventions (SBG rules, no em dashes, bubble gotchas, Apps Script rules) are scattered across README and context; a CLAUDE.md would auto-load them each session.

## Opportunities (solution backlog, highest leverage first)

1. **Build the SBG mastery app** from `SBG_schema.md`. Client-side (keeps student data off any server): ingest cleaned gradebook CSV, track highest attempt per standard/MT, manage retakes, visualize mastery, generate conference/parent reports, export back to NHA format. Moves both stated pains; design already done.
2. **Unify the data exhaust into one mastery feed.** Pear Deck, Blooket, NoRedInk, Lexia, and PSAT all emit per-skill data that maps to MT 1-5; PSAT already logs per-question JSON (column V) with a parser on its roadmap. A normalizer feeding the SBG app's evidence table automates the weekly portfolio and absorbs choke points 2, 3, and 5.
3. **Parameterize `fill_bubbles`:** per-assessment JSON config, a small argparse CLI, a 2-page preview mode, and two golden-file tests so the fixes cannot regress. A new assessment becomes a data file, not a code edit.
4. **Collapse the gradebook tools to one** and fold it into the SBG app's import path.
5. **Year-start stamp script** that reads `private/deployment-ids.md`, stamps `{{SCHOOL_YEAR}}` and non-secret tokens, leaves secrets in `private/`.
6. **Add a CLAUDE.md** (`/init`) so conventions auto-load every session.

## Future to-do (inputs needed to unblock)

These need source material from the teacher before a system can be designed. Drop files in `private/` (gitignored).

- [ ] **Upload a sample accommodation log** (de-identified) so we can see the real fields, cadence, and audit expectations, then plan a system to address accommodation tracking expediently. Relates to choke point 6 and `../templates/_TEMPLATE_student_accommodations.md`. Note: real logs are PII; `*_accommodations.md` and `private/` are already gitignored, but redact the sample anyway.
- [ ] **Export the Gradebook Hub's current tabs and Apps Script** (the highest-skill-grade sorting apps plus related data structure) so the SBG build extends and consolidates them instead of duplicating. The code can be committed (no PII); keep any data export in `private/`.
- [ ] **Scan and upload the individual month event calendars** for the school year. `year-timeline.md` is built from the planning-guide's date list; per-month calendars give a more granular, authoritative picture (early releases, half-days, PD days, assemblies, testing sub-windows) that the high-level calendar misses. Once uploaded, reconcile `year-timeline.md` against them.
