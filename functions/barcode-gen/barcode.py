#!/usr/bin/env python3

import csv
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


CSV_FILE = "barcodes.csv"
OUTPUT_PDF = "barcodes.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 10 * mm
TOP_MARGIN = 10 * mm
BOTTOM_MARGIN = 10 * mm
VERT_SPACE = 5 * mm
BARCODE_HEIGHT = 25 * mm

MIN_CELL_WIDTH = 40 * mm  # used to choose 3–5 columns


def try_register_arial():
    """Try to register Arial, otherwise fall back to Helvetica."""
    try:
        pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
        return "Arial"
    except Exception:
        return "Helvetica"


def decide_columns():
    """
    Dynamically choose columns 3–5 based on width available.
    Tries 5 first (denser), falls back to 3 if necessary.
    """
    usable_width = PAGE_WIDTH - 2 * LEFT_MARGIN
    for cols in [5, 4, 3]:
        col_width = usable_width / cols
        if col_width >= MIN_CELL_WIDTH:
            return cols, col_width
    return 3, usable_width / 3  # safety fallback


def read_barcodes(csv_file, repeat=1):
    items = []
    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row:
                continue
            code = row[0].strip()
            title = row[1].strip() if len(row) > 1 else ""
            if code:
                for i in range(repeat):
                  items.append((code, title))
    return items


def create_pdf(barcode_items):
    font_name = try_register_arial()
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)

    cols, cell_width = decide_columns()
    x_positions = [
        LEFT_MARGIN + i * cell_width for i in range(cols)
    ]

    y = PAGE_HEIGHT - TOP_MARGIN

    c.setFont(font_name, 10)

    col_index = 0
    for code, title in barcode_items:

        if y < BOTTOM_MARGIN + 2 * BARCODE_HEIGHT:
            c.showPage()
            c.setFont(font_name, 10)
            y = PAGE_HEIGHT - TOP_MARGIN
            col_index = 0

        x = x_positions[col_index]

        # heading text (optional)
        if title:
            c.drawCentredString(x + cell_width / 2, y, title)

        # generate barcode
        barcode_obj = code128.Code128(code,
                                      barHeight=BARCODE_HEIGHT,
                                      barWidth=.9)

        # center barcode inside cell
        bw = barcode_obj.width
        bx = x + (cell_width - bw) / 2
        by = y - BARCODE_HEIGHT - 5

        barcode_obj.drawOn(c, bx, by)

        # draw human-readable text below barcode
        c.drawCentredString(x + cell_width / 2, by - 12, code)

        col_index += 1

        # wrap to new row
        if col_index >= cols:
            col_index = 0
            y -= (BARCODE_HEIGHT + 40 + VERT_SPACE)

    c.save()
    print(f"PDF created: {OUTPUT_PDF}")


if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        print(f"CSV file not found: {CSV_FILE}")
    else:
        items = read_barcodes(CSV_FILE, 2)
        if not items:
            print("No barcodes found in CSV.")
        else:
            create_pdf(items)

