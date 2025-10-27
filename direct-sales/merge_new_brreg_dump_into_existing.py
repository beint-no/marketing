#!/usr/bin/env -S uv run --no-project
# /// script
# dependencies = [
#   "pandas",
# ]
# ///
"""
Incrementally merge a new Brønnøysundregistrene dump into existing subdivided CSVs.

This script:
  1. Loads all existing organisasjonsnummer from companies/ directory
  2. Compares with new dump to find new companies only
  3. Appends new companies to appropriate CSV files (by org form + first letter)

Usage:
  # Use default input file (all-companies-norway.csv)
  ./merge_new_brreg_dump_into_existing.py

  # Specify custom input file
  ./merge_new_brreg_dump_into_existing.py path/to/new-dump.csv

Requirements:
  - Existing companies/ directory with subdivided CSVs
  - New Brreg dump file (CSV format)

Output:
  - Updates existing CSV files in companies/ with new companies
  - Only adds companies not already present (by organisasjonsnummer)
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
    """
    if not name or not isinstance(name, str):
        return "OTHER"

    first_char = name[0].upper()

    if 'A' <= first_char <= 'Z':
        return first_char
    else:
        return "OTHER"


def load_all_existing_organisation_numbers(companies_directory: Path) -> set:
    """
    Scan all CSV files in companies/ directory and extract organisasjonsnummer.

    Returns:
        Set of all existing organisation numbers (as strings)
    """
    existing_organisation_numbers = set()

    # Iterate through all organisation form directories
    for organisation_form_directory in companies_directory.glob("*"):
        if not organisation_form_directory.is_dir():
            continue

        # Iterate through all letter CSV files
        for csv_file in organisation_form_directory.glob("*.csv"):
            try:
                csv_dataframe = pd.read_csv(csv_file, low_memory=False)
                if "organisasjonsnummer" in csv_dataframe.columns:
                    # Add all org numbers from this file to the set
                    existing_organisation_numbers.update(
                        csv_dataframe["organisasjonsnummer"].astype(str).values
                    )
            except Exception as e:
                print(f"⚠️  Warning: Could not read {csv_file}: {e}")

    return existing_organisation_numbers


def merge_new_companies_into_existing_structure():
    """
    Main function: Load new dump, find new companies, and merge into existing CSVs.
    """
    # Parse command-line arguments
    if len(sys.argv) > 1:
        new_dump_csv_path = Path(sys.argv[1])
    else:
        new_dump_csv_path = Path("all-companies-norway.csv")

    companies_directory = Path("companies")

    # Validate input file exists
    if not new_dump_csv_path.exists():
        print(f"❌ Error: {new_dump_csv_path} not found!")
        sys.exit(1)

    # Validate companies directory exists
    if not companies_directory.exists():
        print(f"❌ Error: {companies_directory}/ directory not found!")
        print(f"   Run split_companies_by_organisation_form_and_letter.py first.")
        sys.exit(1)

    # Load new dump
    print(f"📂 Loading new dump from {new_dump_csv_path}...")
    new_companies_dataframe = pd.read_csv(new_dump_csv_path, low_memory=False)

    # Validate required columns exist
    required_columns = ["organisasjonsform.kode", "navn", "organisasjonsnummer"]
    missing_columns = [col for col in required_columns if col not in new_companies_dataframe.columns]
    if missing_columns:
        print(f"❌ Error: Required columns missing: {missing_columns}")
        sys.exit(1)

    # Clean data
    new_companies_dataframe["organisasjonsform.kode"] = new_companies_dataframe["organisasjonsform.kode"].fillna("UNKNOWN")
    new_companies_dataframe["navn"] = new_companies_dataframe["navn"].fillna("UNKNOWN")
    new_companies_dataframe["organisasjonsnummer"] = new_companies_dataframe["organisasjonsnummer"].astype(str)

    # Filter out bankrupt companies (konkurs = True)
    original_count = len(new_companies_dataframe)
    if "konkurs" in new_companies_dataframe.columns:
        new_companies_dataframe = new_companies_dataframe[new_companies_dataframe["konkurs"] != True]
        bankrupt_count = original_count - len(new_companies_dataframe)
        print(f"🚫 Filtered out {bankrupt_count:,} bankrupt companies (konkurs=True)")

    # Load all existing organisation numbers
    print(f"🔍 Scanning existing companies/ directory...")
    existing_organisation_numbers = load_all_existing_organisation_numbers(companies_directory)
    print(f"📊 Found {len(existing_organisation_numbers):,} existing companies")

    # Filter to only new companies (not in existing set)
    companies_to_add = new_companies_dataframe[
        ~new_companies_dataframe["organisasjonsnummer"].isin(existing_organisation_numbers)
    ]

    print(f"\n🆕 {len(companies_to_add):,} new companies to add")

    if len(companies_to_add) == 0:
        print("✅ No new companies to merge!")
        return

    # Group new companies and append to appropriate CSV files
    total_companies_added = 0

    for organisation_form in sorted(companies_to_add["organisasjonsform.kode"].unique()):
        # Filter companies for this organisation form
        companies_in_org_form = companies_to_add[
            companies_to_add["organisasjonsform.kode"] == organisation_form
        ]

        organisation_form_directory = companies_directory / str(organisation_form)
        organisation_form_directory.mkdir(parents=True, exist_ok=True)

        # Group by first letter
        companies_by_letter = {}
        for _, company_row in companies_in_org_form.iterrows():
            letter_bucket = get_letter_bucket_for_company_name(company_row["navn"])

            if letter_bucket not in companies_by_letter:
                companies_by_letter[letter_bucket] = []

            companies_by_letter[letter_bucket].append(company_row)

        # Append to existing CSVs (or create new if doesn't exist)
        for letter, new_company_rows in companies_by_letter.items():
            csv_file_path = organisation_form_directory / f"{letter}.csv"
            new_companies_dataframe_subset = pd.DataFrame(new_company_rows)

            if csv_file_path.exists():
                # Append to existing file
                existing_csv_dataframe = pd.read_csv(csv_file_path, low_memory=False)
                merged_dataframe = pd.concat(
                    [existing_csv_dataframe, new_companies_dataframe_subset],
                    ignore_index=True
                )
                merged_dataframe.to_csv(csv_file_path, index=False)
            else:
                # Create new file
                new_companies_dataframe_subset.to_csv(csv_file_path, index=False)

            total_companies_added += len(new_company_rows)
            print(f"  ✓ {organisation_form}/{letter}.csv: +{len(new_company_rows):,} companies")

    # Summary
    print(f"\n✅ Successfully added {total_companies_added:,} new companies!")


if __name__ == "__main__":
    merge_new_companies_into_existing_structure()
