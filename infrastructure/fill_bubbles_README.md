# Fill-Bubble Script

`fill_bubbles_template.py` automates filling NHA bubble sheets: it reads student responses from a CSV export and draws the corresponding bubbles onto the PDF answer sheets, producing a completed PDF ready for scanning/grading.

This repo ships one generic template. Copy it per assessment; do not edit the template in place.

## What it does

1. Parse student responses from a CSV export (Google Forms / Gradebook Hub).
2. Extract student names and bubble positions from the PDF answer sheets.
3. Match students by name (exact, then prefix, then first name fallback).
4. Fill bubbles on rendered page images.
5. Assemble a completed PDF, one page at a time, with reportlab.

## Requirements

```bash
pip install pdfplumber pdf2image Pillow reportlab --break-system-packages
```

Also requires `poppler-utils` for PDF rendering:

```bash
sudo apt-get install poppler-utils
```

## Workflow

1. **Copy the template** to a per-assessment file, e.g. `cp fill_bubbles_template.py u5l20_fill_bubbles.py`. Keep filled outputs out of git; `*_filled.pdf` and `filled_*.pdf` are gitignored, and student inputs belong in `private/`.
2. **Export the CSV** of student responses from Gradebook Hub.
3. **Download the blank bubble-sheet PDF** from the assessment system.
4. **Set the config block** at the top of your copy:
   - `CSV_PATH`, `PDF_PATH`, `OUTPUT_PATH` — input CSV, blank PDF, output PDF.
   - `ANSWER_KEY` — correct answers for MC questions.
   - `CR_QUESTION` and `CR_SCORES` — manual scores for the constructed-response item, keyed by lowercase student name.
   - Column mappings in `parse_csv()` — if CSV headers do not match `Q1`, `Q2`, etc.
5. **Run it:**

```bash
python u5l20_fill_bubbles.py
```

6. **Check the console** for unmatched CSV names and PDF pages with no submission before trusting the output.

## Configuration reference

### Answer key

```python
ANSWER_KEY = {
    '1': 'A',
    '2': 'C',
    '5': ['A', 'C'],   # multi-select: list the correct letters
}
```

### Manual CR scores

```python
CR_QUESTION = '10'
CR_SCORES = {
    'student name lowercase': 2,
    'another student': 1,
}
```

### Drawing settings

```python
BUBBLE_RADIUS = 12      # size of filled bubble
Y_OFFSET = -2.5         # vertical adjustment (negative = up)
FILL_COLOR = (0, 0, 0)  # black
RENDER_DPI = 150        # PDF -> image resolution
```

## Bubble-sheet layout detection

Positions are detected dynamically from pdfplumber character extraction. Assumptions:

- Student name is on the first line of each page.
- ABCD rows are detected by finding a complete {A, B, C, D} set on one y-line.
- 012 rows (CR scores) are detected by finding a complete {0, 1, 2} set.
- Questions are assigned in order by y-position.

The generic template maps a left column of Q1 to Q9 (ABCD), plus a right column with the CR item (012) and Q11 (ABCD). Adjust `detect_bubbles_on_page()` and the `parse_csv()` column list if your assessment differs.

## Two gotchas (already fixed in the template; keep them)

These are solved problems. Do not reintroduce the broken versions.

### Output is built per page with reportlab, not PIL save_all

The PDF is assembled in `save_pdf_per_page()` with reportlab `canvas.drawImage`, one page at a time, each page box set to the source page's point size. Do NOT swap this for PIL `Image.save(save_all=True, append_images=...)`; PIL `save_all` corrupts page scaling past page 1, so bubbles drift off-target on every page after the first. Scale is also computed per page, so mixed page sizes stay correct.

### Right-column detection is windowed to 150 <= x0 < 250

Right-column bubbles are detected with `RIGHT_COL_MIN_X (150) <= x0 < RIGHT_COL_MAX_X (250)`. The upper bound matters: a bare `x0 >= 150` threshold pulls in the Student-ID grid on the right margin and spoofs phantom bubble rows. Left-column detection uses `x0 < 150`.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bubbles drift on pages 2+ | Output assembly reverted to PIL `save_all` | Use `save_pdf_per_page()` (reportlab per page). |
| Phantom rows / wrong right-column questions | Right-column window too wide | Confirm `150 <= x0 < 250`; the Student-ID grid sits past 250. |
| Bubbles off-center | Calibration | Adjust `Y_OFFSET` (negative = up) or `BUBBLE_RADIUS`. |
| Some pages not filling | Y-positions vary between pages | Widen detection in `detect_bubbles_on_page()`. |
| Student names not matching | Name format differs between CSV and PDF | Check console output; matching is exact, then prefix, then first name. |
