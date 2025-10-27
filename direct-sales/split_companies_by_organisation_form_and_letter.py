#!/usr/bin/env -S uv run --no-project
# /// script
# dependencies = [
#   "pandas",
# ]
# ///
"""
Split all-companies-norway.csv into subdivided CSVs organized by:
  1. organisasjonsform.kode (e.g., AS, ENK, NUF)
  2. First letter of navn (A-Z + OTHER for non-ASCII/numbers)

Creates directory structure:
  companies/
    AS/
      A.csv, B.csv, ..., Z.csv, OTHER.csv
    ENK/
      A.csv, B.csv, ..., Z.csv, OTHER.csv
    etc.

Usage:
  ./split_companies_by_organisation_form_and_letter.py

Requirements:
  - Input file: all-companies-norway.csv (Brønnøysundregistrene dump)
  - Output: companies/ directory with subdivided CSVs
"""

import pandas as pd
from pathlib import Path
import sys


def get_letter_bucket_for_company_name(name: str) -> str:
    """
    Extract first letter bucket from company name.

    Returns:
        - A-Z for ASCII letters
        - OTHER for numbers, non-ASCII, or empty names

    Examples:
        "ACME AS" → "A"
        "Ålesund Handel" → "OTHER"
        "123 Company" → "OTHER"
    """
    if not name or not isinstance(name, str):
        return "OTHER"

    first_char = name[0].upper()

    if 'A' <= first_char <= 'Z':
        return first_char
    else:
        return "OTHER"


def split_brreg_dump_into_subdivided_csvs():
    """
    Main function: Load Brreg dump and split into organized CSV structure.
    """
    # Input and output paths
    input_csv_path = Path("all-companies-norway.csv")
    output_companies_dir = Path("companies")

    # Validate input file exists
    if not input_csv_path.exists():
        print(f"❌ Error: {input_csv_path} not found!")
        print(f"   Please ensure the Brønnøysundregistrene dump is named 'all-companies-norway.csv'")
        sys.exit(1)

    # Load CSV
    print(f"📂 Loading {input_csv_path}...")
    companies_dataframe = pd.read_csv(input_csv_path)

    # Validate required columns exist
    required_columns = ["organisasjonsform.kode", "navn"]
    missing_columns = [col for col in required_columns if col not in companies_dataframe.columns]
    if missing_columns:
        print(f"❌ Error: Required columns missing: {missing_columns}")
        sys.exit(1)

    # Clean data: replace NaN with UNKNOWN
    companies_dataframe["organisasjonsform.kode"] = companies_dataframe["organisasjonsform.kode"].fillna("UNKNOWN")
    companies_dataframe["navn"] = companies_dataframe["navn"].fillna("UNKNOWN")

    # Display processing info
    total_companies = len(companies_dataframe)
    organisation_forms = sorted(companies_dataframe["organisasjonsform.kode"].unique())
    print(f"\n📊 Processing {total_companies:,} companies...")
    print(f"📋 Found {len(organisation_forms)} organisation forms: {organisation_forms}")

    # Split by organisation form, then by first letter
    total_files_created = 0

    for organisation_form in organisation_forms:
        # Filter companies for this organisation form
        companies_in_org_form = companies_dataframe[
            companies_dataframe["organisasjonsform.kode"] == organisation_form
        ]

        # Create directory for this organisation form
        organisation_form_directory = output_companies_dir / str(organisation_form)
        organisation_form_directory.mkdir(parents=True, exist_ok=True)

        # Group companies by first letter of navn
        companies_by_letter = {}
        for _, company_row in companies_in_org_form.iterrows():
            letter_bucket = get_letter_bucket_for_company_name(company_row["navn"])

            if letter_bucket not in companies_by_letter:
                companies_by_letter[letter_bucket] = []

            companies_by_letter[letter_bucket].append(company_row)

        # Write each letter group to its own CSV file
        for letter, company_rows in sorted(companies_by_letter.items()):
            letter_dataframe = pd.DataFrame(company_rows)
            output_csv_file = organisation_form_directory / f"{letter}.csv"
            letter_dataframe.to_csv(output_csv_file, index=False)

            total_files_created += 1
            print(f"  ✓ {organisation_form}/{letter}.csv: {len(company_rows):,} companies")

    # Summary
    print(f"\n✅ Successfully created {total_files_created} CSV files in {output_companies_dir}/")
    print(f"📁 Directory structure: companies/<ORG_FORM>/<LETTER>.csv")


if __name__ == "__main__":
    split_brreg_dump_into_subdivided_csvs()
