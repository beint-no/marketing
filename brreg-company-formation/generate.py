#!/usr/bin/env -S uv run --no-project
# /// script
# dependencies = [
#   "PyPDF2==3.0.1",
#   "reportlab==4.0.7",
# ]
# ///

"""
Company Formation Document Generator
Converts markdown templates to PDFs with signatures
"""

import sys
import subprocess
import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import io


# ANSI colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_color(text, color):
    """Print colored text"""
    print(f"{color}{text}{Colors.NC}")


def convert_markdown_to_pdf(input_file, output_file):
    """Convert markdown to PDF using pandoc"""
    cmd = [
        'pandoc',
        str(input_file),
        '-o', str(output_file),
        '--pdf-engine=xelatex',
        '-V', 'geometry:margin=2.5cm',
        '-V', 'fontsize=11pt',
        '-V', 'documentclass=article',
        '-V', 'colorlinks=true',
        '-V', 'linkcolor=blue',
        '--highlight-style=tango',
    ]

    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def add_signatures(input_pdf, output_pdf, sig1="Greg Taube", sig2="Ak"):
    """Add professional signature blocks to the bottom of the last page"""
    try:
        from datetime import date

        # Read the input PDF
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        # Get the last page
        num_pages = len(reader.pages)
        last_page = reader.pages[num_pages - 1]

        # Create signature overlay
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        # Position signatures at the bottom
        y_position = 4 * cm  # 4cm from bottom
        x_left = 3 * cm      # Left signature
        x_right = 12 * cm    # Right signature

        # Current date
        today = date.today().strftime("%d.%m.%Y")

        # Draw signature blocks for both signers
        for x_pos, name in [(x_left, sig1), (x_right, sig2)]:
            # Draw signature line
            line_width = 5 * cm
            can.setLineWidth(0.5)
            can.line(x_pos, y_position, x_pos + line_width, y_position)

            # Draw handwritten-style signature above the line
            can.setFont("Times-Italic", 16)
            can.drawString(x_pos + 0.2*cm, y_position + 0.3*cm, name)

            # Draw printed name below the line
            can.setFont("Helvetica", 9)
            can.drawString(x_pos, y_position - 0.5*cm, name)

            # Draw date below the name
            can.setFont("Helvetica", 8)
            can.drawString(x_pos, y_position - 1*cm, f"Dato: {today}")

        can.save()
        packet.seek(0)

        # Merge the signature overlay with the last page
        overlay_pdf = PdfReader(packet)
        last_page.merge_page(overlay_pdf.pages[0])

        # Add all pages to writer
        for i in range(num_pages):
            if i == num_pages - 1:
                writer.add_page(last_page)
            else:
                writer.add_page(reader.pages[i])

        # Write the final PDF
        with open(output_pdf, "wb") as output_file:
            writer.write(output_file)

        return True
    except Exception as e:
        print_color(f"Error adding signatures: {e}", Colors.RED)
        return False


def process_document(doc_type, company_dir, output_dir):
    """Process a single markdown document"""
    input_file = company_dir / f"{doc_type}.md"
    temp_pdf = output_dir / f"{doc_type}_temp.pdf"
    final_pdf = output_dir / f"{doc_type}.pdf"

    if not input_file.exists():
        print_color(f"⚠ Skipping {doc_type}.md (not found)", Colors.YELLOW)
        return False

    print_color(f"📄 Processing {doc_type}.md...", Colors.GREEN)

    # Convert markdown to PDF
    if not convert_markdown_to_pdf(input_file, temp_pdf):
        print_color(f"✗ Failed to convert {doc_type}.md to PDF", Colors.RED)
        return False

    # Add signatures
    if add_signatures(temp_pdf, final_pdf):
        temp_pdf.unlink()  # Remove temp file
        print_color(f"✓ Generated {final_pdf}", Colors.GREEN)
        print()
        return True
    else:
        # If signature adding fails, keep the PDF without signatures
        temp_pdf.rename(final_pdf)
        print_color(f"  Saved without signatures as {final_pdf}", Colors.YELLOW)
        print()
        return True


def main():
    """Main entry point"""
    # Always use new-company directory
    company_dir = Path("new-company")

    # Check if company directory exists
    if not company_dir.exists() or not company_dir.is_dir():
        print_color(f"Error: Directory '{company_dir}' does not exist", Colors.RED)
        sys.exit(1)

    # Create output directory
    output_dir = company_dir / "output"
    output_dir.mkdir(exist_ok=True)

    print_color("=== Company Formation Document Generator ===", Colors.GREEN)
    print()

    # Process all document types
    documents = ["protokoll", "stiftelse", "vedtak", "vedtekter"]
    generated = []

    for doc_type in documents:
        if process_document(doc_type, company_dir, output_dir):
            generated.append(doc_type)

    print_color("=== Generation Complete ===", Colors.GREEN)
    print(f"Output directory: {output_dir}")
    print()

    if generated:
        print("Generated files:")
        for doc in generated:
            print_color(f"  ✓ {doc}.pdf", Colors.GREEN)
    else:
        print_color("No files were generated", Colors.YELLOW)


if __name__ == "__main__":
    main()
