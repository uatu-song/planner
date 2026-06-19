#!/usr/bin/env python3
"""
Generic Fill-Bubble Script Template
Copy this file and customize for new assessments.

Required customizations:
1. Set file paths (CSV_PATH, PDF_PATH, OUTPUT_PATH)
2. Set ANSWER_KEY with correct answers
3. Set CR_SCORES with manual scores for constructed response
4. Update parse_csv() column mappings if needed
5. Adjust detect_bubbles_on_page() if layout differs significantly

Two gotchas baked into this template (do not re-derive):
- Output is assembled with reportlab canvas.drawImage per page, NOT PIL
  Image.save(save_all=True). PIL save_all corrupts page scaling past page 1,
  so bubbles land in the wrong place on every page after the first.
- Right-column bubble detection is constrained to 150 <= x0 < 250. A bare
  x0 >= 150 threshold pulls in the Student-ID grid and spoofs phantom rows.
"""

import csv
import re
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - CUSTOMIZE THESE
# ══════════════════════════════════════════════════════════════════════════════

# File paths
CSV_PATH = '/path/to/responses.csv'
PDF_PATH = '/path/to/bubble_sheets.pdf'
OUTPUT_PATH = '/path/to/filled_bubbles.pdf'

# Answer key - map question numbers to correct answers
# For multi-select: '5': ['A', 'C']
ANSWER_KEY = {
    '1': 'A',
    '2': 'B',
    '3': 'C',
    '4': 'D',
    # Add all questions...
}

# Manual CR scores - keyed by normalized (lowercase) student name
# CR question number (e.g., '10' for Q10)
CR_QUESTION = '10'
CR_SCORES = {
    'student name lowercase': 2,
    # Add all students...
}

# Drawing settings
BUBBLE_RADIUS = 12      # Size of filled bubble (adjust if too small/large)
FILL_COLOR = (0, 0, 0)  # Black
Y_OFFSET = -2.5         # Vertical adjustment (negative = up)

# Render resolution for PDF -> image conversion
RENDER_DPI = 150

# Right-column detection window. Keep the upper bound: a bare x0 >= 150
# threshold pulls in the Student-ID grid and spoofs phantom bubble rows.
RIGHT_COL_MIN_X = 150
RIGHT_COL_MAX_X = 250

# Letter sets for validating bubble rows
LETTERS_ABCD = {'A', 'B', 'C', 'D'}
LETTERS_ABCDEF = {'A', 'B', 'C', 'D', 'E', 'F'}
LETTERS_012 = {'0', '1', '2'}

# ══════════════════════════════════════════════════════════════════════════════
# NAME NORMALIZATION
# ══════════════════════════════════════════════════════════════════════════════

def normalize_name(name):
    """Normalize a name for matching."""
    if not name:
        return ''
    name = re.sub(r'\([^)]*\)', '', name)  # Remove (nicknames)
    name = ' '.join(name.lower().split())
    return name

def match_student_name(csv_name, pdf_names_map):
    """Match CSV name to PDF page index."""
    csv_norm = normalize_name(csv_name)

    # Exact match
    if csv_norm in pdf_names_map:
        return pdf_names_map[csv_norm]

    # Prefix match
    for pdf_norm, page_idx in pdf_names_map.items():
        if csv_norm.startswith(pdf_norm) or pdf_norm.startswith(csv_norm):
            return page_idx

    # First name match
    csv_first = csv_norm.split()[0] if csv_norm else ''
    for pdf_norm, page_idx in pdf_names_map.items():
        pdf_first = pdf_norm.split()[0] if pdf_norm else ''
        if csv_first and csv_first == pdf_first:
            return page_idx

    return None

# ══════════════════════════════════════════════════════════════════════════════
# BUBBLE POSITION DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_bubble_positions(pdf_path):
    """Extract bubble positions for each page."""
    all_positions = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_positions = detect_bubbles_on_page(page.chars)
            all_positions[page_idx] = page_positions

    return all_positions

def detect_bubbles_on_page(chars):
    """
    Detect bubble row positions on a single page.

    CUSTOMIZE THIS for your specific bubble sheet layout.
    This generic version assumes:
    - Left column has Q1-Q9 (ABCD)
    - Right column has Q10 (012) and Q11 (ABCD)

    Right-column detection is windowed to RIGHT_COL_MIN_X <= x0 < RIGHT_COL_MAX_X
    (150 <= x0 < 250). The upper bound is required: without it the Student-ID
    grid on the right margin is read as bubble rows and spoofs phantom questions.

    Returns: {question: {letter: (x, y)}}
    """
    positions = {}

    # Group characters by y-position
    y_groups = {}
    for c in chars:
        y_key = round(c['top'])
        if y_key not in y_groups:
            y_groups[y_key] = []
        y_groups[y_key].append(c)

    left_abcd_rows = []
    right_abcd_rows = []
    right_012_rows = []

    for y_key in sorted(y_groups.keys()):
        group = y_groups[y_key]

        # Left column: x0 < RIGHT_COL_MIN_X
        left_chars = [(c['text'].upper(), (c['x0'] + c['x1']) / 2, (c['top'] + c['bottom']) / 2)
                      for c in group
                      if c['x0'] < RIGHT_COL_MIN_X
                      and len(c['text']) == 1 and c['text'].upper() in 'ABCDEF012']
        # Right column: RIGHT_COL_MIN_X <= x0 < RIGHT_COL_MAX_X (excludes Student-ID grid)
        right_chars = [(c['text'].upper(), (c['x0'] + c['x1']) / 2, (c['top'] + c['bottom']) / 2)
                       for c in group
                       if RIGHT_COL_MIN_X <= c['x0'] < RIGHT_COL_MAX_X
                       and len(c['text']) == 1 and c['text'].upper() in 'ABCDEF012']

        left_letters = {ch[0] for ch in left_chars}
        if left_letters == LETTERS_ABCD:
            letter_pos = {ch[0]: (ch[1], ch[2]) for ch in left_chars}
            left_abcd_rows.append((y_key, letter_pos))
        elif left_letters == LETTERS_ABCDEF:
            letter_pos = {ch[0]: (ch[1], ch[2]) for ch in left_chars}
            left_abcd_rows.append((y_key, letter_pos))

        right_letters = {ch[0] for ch in right_chars}
        if right_letters == LETTERS_ABCD:
            letter_pos = {ch[0]: (ch[1], ch[2]) for ch in right_chars}
            right_abcd_rows.append((y_key, letter_pos))
        elif right_letters == LETTERS_012:
            letter_pos = {ch[0]: (ch[1], ch[2]) for ch in right_chars}
            right_012_rows.append((y_key, letter_pos))

    # Assign questions (CUSTOMIZE these mappings)
    left_questions = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    for i, (y_key, letter_pos) in enumerate(left_abcd_rows):
        if i < len(left_questions):
            positions[left_questions[i]] = letter_pos

    if right_012_rows:
        positions[CR_QUESTION] = right_012_rows[0][1]

    if right_abcd_rows:
        positions['11'] = right_abcd_rows[0][1]

    return positions

# ══════════════════════════════════════════════════════════════════════════════
# PDF NAME EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_pdf_names(pdf_path):
    """Extract student names from each page."""
    names_map = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ''
            lines = text.strip().split('\n')

            if lines:
                raw_name = lines[0].strip()
                norm_name = normalize_name(raw_name)
                if norm_name:
                    names_map[norm_name] = page_idx

    return names_map

# ══════════════════════════════════════════════════════════════════════════════
# CSV PARSING - CUSTOMIZE COLUMN MAPPINGS
# ══════════════════════════════════════════════════════════════════════════════

def parse_csv(csv_path):
    """
    Parse student submissions CSV.
    CUSTOMIZE the column name mappings below.
    """
    submissions = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Student Name', '').strip()
            norm_name = normalize_name(name)

            if not norm_name:
                continue

            answers = {}

            # CUSTOMIZE these column mappings
            answers['1'] = row.get('Q1', '').strip().upper()
            answers['2'] = row.get('Q2', '').strip().upper()
            answers['3'] = row.get('Q3', '').strip().upper()
            answers['4'] = row.get('Q4', '').strip().upper()
            answers['5'] = row.get('Q5', '').strip().upper()
            answers['6'] = row.get('Q6', '').strip().upper()
            answers['7'] = row.get('Q7', '').strip().upper()
            answers['8'] = row.get('Q8', '').strip().upper()
            answers['9'] = row.get('Q9', '').strip().upper()
            answers['11'] = row.get('Q11', '').strip().upper()

            # CR score from manual grading
            answers[CR_QUESTION] = str(CR_SCORES.get(norm_name, 0))

            submissions[norm_name] = answers

    return submissions

# ══════════════════════════════════════════════════════════════════════════════
# BUBBLE FILLING
# ══════════════════════════════════════════════════════════════════════════════

def fill_bubbles_on_image(image, positions, answers, scale_x, scale_y):
    """Draw filled bubbles on the image."""
    draw = ImageDraw.Draw(image)

    for q_name, letter_positions in positions.items():
        answer = answers.get(q_name)

        if not answer:
            continue

        # Handle multi-select (list of answers)
        if isinstance(answer, list):
            for ans in answer:
                if ans in letter_positions:
                    x, y = letter_positions[ans]
                    draw_filled_bubble(draw, x * scale_x, (y + Y_OFFSET) * scale_y)
        else:
            if answer in letter_positions:
                x, y = letter_positions[answer]
                draw_filled_bubble(draw, x * scale_x, (y + Y_OFFSET) * scale_y)

def draw_filled_bubble(draw, x, y):
    """Draw a filled circle."""
    r = BUBBLE_RADIUS
    draw.ellipse([x - r, y - r, x + r, y + r], fill=FILL_COLOR)

# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════

def save_pdf_per_page(images, page_sizes, output_path):
    """
    Assemble the output PDF one page at a time with reportlab.

    Do NOT replace this with PIL Image.save(save_all=True, append_images=...).
    PIL save_all corrupts page scaling past the first page, so bubbles drift
    off-target on every page after page 1. reportlab sets the page box to the
    source PDF point size and draws each rendered image to fill it exactly.
    """
    if not images:
        return

    c = canvas.Canvas(output_path)
    for img, (pt_width, pt_height) in zip(images, page_sizes):
        rgb = img.convert('RGB') if img.mode != 'RGB' else img
        c.setPageSize((pt_width, pt_height))
        c.drawImage(ImageReader(rgb), 0, 0, width=pt_width, height=pt_height)
        c.showPage()
    c.save()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def process_bubble_sheets(csv_path, pdf_path, output_path):
    """Main processing function."""
    print("=" * 60)
    print("Fill-Bubble Script")
    print("=" * 60)

    print("\n[1/5] Parsing CSV submissions...")
    submissions = parse_csv(csv_path)
    print(f"      Found {len(submissions)} student submissions")

    print("\n[2/5] Extracting names from bubble sheet PDF...")
    pdf_names_map = extract_pdf_names(pdf_path)
    print(f"      Found {len(pdf_names_map)} student pages")

    print("\n[3/5] Detecting bubble positions...")
    all_positions = extract_bubble_positions(pdf_path)

    if 0 in all_positions:
        detected = list(all_positions[0].keys())
        print(f"      Page 1 detected questions: {detected}")

    print("\n[4/5] Converting PDF to images...")
    images = convert_from_path(pdf_path, dpi=RENDER_DPI)
    print(f"      Converted {len(images)} pages")

    # Per-page point sizes from the source PDF (reportlab draws to these exactly)
    with pdfplumber.open(pdf_path) as pdf:
        page_sizes = [(page.width, page.height) for page in pdf.pages]

    print("\n[5/5] Filling bubbles and creating output PDF...")

    matched = 0
    unmatched_csv = []

    for norm_name, answers in submissions.items():
        page_idx = match_student_name(norm_name, pdf_names_map)

        if page_idx is not None:
            matched += 1
            img = images[page_idx].copy()
            # Per-page scale: image pixels per PDF point, computed from THIS page.
            pt_width, pt_height = page_sizes[page_idx]
            img_width, img_height = img.size
            scale_x = img_width / pt_width
            scale_y = img_height / pt_height
            positions = all_positions.get(page_idx, {})
            fill_bubbles_on_image(img, positions, answers, scale_x, scale_y)
            images[page_idx] = img
        else:
            unmatched_csv.append(norm_name)

    print(f"      Matched {matched}/{len(submissions)} students from CSV")

    if unmatched_csv:
        print(f"\n      [!] Unmatched CSV names:")
        for name in unmatched_csv:
            print(f"          - {name}")

    matched_pages = set()
    for norm_name in submissions:
        page_idx = match_student_name(norm_name, pdf_names_map)
        if page_idx is not None:
            matched_pages.add(page_idx)

    unmatched_pdf = []
    for norm_name, page_idx in pdf_names_map.items():
        if page_idx not in matched_pages:
            unmatched_pdf.append((norm_name, page_idx))

    if unmatched_pdf:
        print(f"\n      [!] PDF pages with no CSV submission:")
        for name, idx in unmatched_pdf:
            print(f"          - Page {idx + 1}: {name}")

    # Create output PDF (reportlab, per page; see save_pdf_per_page docstring)
    save_pdf_per_page(images, page_sizes, output_path)

    print(f"\n[DONE] Output saved to: {output_path}")
    print("=" * 60)

if __name__ == '__main__':
    process_bubble_sheets(CSV_PATH, PDF_PATH, OUTPUT_PATH)
