# PSCA 8th Grade ELA — Yearly Working Repo

Universal, reusable resource set for 8th Grade ELA at Plymouth Scholars Charter Academy (NHA). This is the codespace equivalent of the year's planning folder: curriculum, teaching context, digital infrastructure, and blank templates. All student-specific and year-specific data has been stripped — fill placeholders (`{{LIKE_THIS}}`) at the start of each year and keep anything real in `/private` (gitignored).

## Structure

```
.
├── curriculum/
│   ├── regular-ela8/        Scope & sequence — General Ed ELA 8 track (searchable PDFs)
│   ├── accelerated-ela89/   Scope & sequence — English 8/9 accelerated track
│   └── overview/            Yearlong overview + MI Year-at-a-Glance
├── context/
│   ├── teaching-context.md      SBG philosophy, school context, challenges
│   ├── planning-guide.md        Full year plan, both tracks, tech stack, assessment calendar
│   └── beginning-of-year-todo.md
├── infrastructure/
│   ├── gradebook_processor.html     NHA gradebook paste-and-clean tool (client-side)
│   ├── gradebook_ultimate.html      Gradebook Hub UI (client-side)
│   ├── fill_bubbles_template.py     Bubble-sheet auto-fill (pdfplumber/pdf2image/PIL/reportlab)
│   ├── fill_bubbles_README.md
│   ├── SBG_schema.md                Standards-based gradebook DB schema + implementation plan
│   └── PSAT_Adaptive_Handoff.md     PSAT Adaptive Practice system architecture & maintenance
├── templates/
│   ├── _TEMPLATE_student_accommodations.md
│   ├── _TEMPLATE_academic_integrity_log.md
│   └── _TEMPLATE_recommendation_letter.md
└── private/                  Gitignored. Real rosters, IEPs, completed logs go here.
```

## Two tracks

`regular-ela8` and `accelerated-ela89` are **not** duplicates. Units 1, 2, and 6 share texts across both tracks but differ in depth, page count, and standards (8/9 integrates 9th-grade standards). Both are kept intentionally.

## Start-of-year setup

1. Drop real rosters / IEP / 504 files into `/private`.
2. Copy each `templates/_TEMPLATE_*.md` to `/private`, drop the `_TEMPLATE` prefix, and fill in.
3. Replace placeholder tokens (below) with the year's live values. **Keep live IDs out of committed files** — store them in `/private` or as codespace secrets.

### Placeholder tokens

| Token | Meaning |
|---|---|
| `{{SCHOOL_YEAR}}` | e.g. 2026-27 |
| `{{TEACHER_NAME}}` / `{{TEACHER_EMAIL}}` | Your name / NHA email |
| `{{STUDENT_NAME}}` / `{{STUDENT_ID}}` / `{{SECTION}}` | Per-student fields in templates |
| `{{GRADEBOOK_SHEET_ID}}` | Gradebook Hub spreadsheet ID |
| `{{GRADEBOOK_GAS_DEPLOY_ID}}` | Gradebook Hub Apps Script deployment ID |
| `{{PSAT_GAS_DEPLOY_ID}}` | PSAT Adaptive Practice deployment ID |
| `{{SONGVUE_SHEET_ID}}` | SongVue spreadsheet ID |
| `{{AGENDA_SHEET_ID}}` / `{{AGENDA_GAS_DEPLOY_ID}}` | Grade Level Agenda IDs |

## Conventions baked in

- **SBG:** record highest/best attempt, not average; behavior separated from academic measurement; MI-Access students excluded from proficiency denominators.
- **Academic integrity:** Draftback (process) + stylometry (product); follow the protocol in the log template.
- **Writing style for drafted comms:** no em dashes (commas/semicolons); parent-facing warm/professional, student-facing direct/age-appropriate.
- **Bubble pipeline gotchas:** constrain right-column detection to `150 <= x0 < 250`; use reportlab `canvas.drawImage` per page (PIL `save_all` breaks scaling on pages 2+).
- **Apps Script:** one `doGet` per project; redeploy a New version after any code/HTML change; test in incognito to dodge cache.

## Notes

- Curriculum PDFs were rebuilt as real searchable PDFs (image + invisible OCR text layer) from the original scan bundles, so text is selectable and the files open normally.
- `private/` is gitignored. Verify with `git status` that nothing under it (and no roster/grades CSV) is staged before pushing.
