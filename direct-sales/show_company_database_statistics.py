#!/usr/bin/env -S uv run --no-project
# /// script
# dependencies = [
#   "pandas",
# ]
# ///
"""
Display statistics about the subdivided Brønnøysundregistrene company database.

Shows:
  - Total number of companies per organisation form
  - Number of CSV files per organisation form
  - Top 5 letter buckets by company count (within each org form)
  - Overall totals across all organisation forms

Usage:
  # Show statistics for all organisation forms
  ./show_company_database_statistics.py

  # Show statistics for specific organisation form only
  ./show_company_database_statistics.py AS
  ./show_company_database_statistics.py ENK

Requirements:
  - Existing companies/ directory with subdivided CSVs
"""

import pandas as pd
from pathlib import Path
import sys


def display_company_database_statistics():
    """
    Main function: Scan companies/ directory and display statistics.
    """
    companies_directory = Path("companies")

    # Validate companies directory exists
    if not companies_directory.exists():
        print(f"❌ Error: {companies_directory}/ directory not found!")
        print(f"   Run split_companies_by_organisation_form_and_letter.py first.")
        sys.exit(1)

    # Parse command-line arguments: filter by organisation form if specified
    if len(sys.argv) > 1:
        target_organisation_form = sys.argv[1].upper()
        organisation_form_directories = [companies_directory / target_organisation_form]

        if not organisation_form_directories[0].exists():
            print(f"❌ Error: Organisation form '{target_organisation_form}' not found!")
            print(f"\n📋 Available organisation forms:")

            available_org_forms = sorted([
                directory.name
                for directory in companies_directory.glob("*")
                if directory.is_dir()
            ])

            for org_form in available_org_forms:
                print(f"  • {org_form}")

            sys.exit(1)
    else:
        # Show all organisation forms
        organisation_form_directories = sorted([
            directory
            for directory in companies_directory.glob("*")
            if directory.is_dir()
        ])

    # Display header
    print("=" * 70)
    print("📊 BRØNNØYSUNDREGISTRENE COMPANY DATABASE STATISTICS")
    print("=" * 70)

    grand_total_companies = 0
    grand_total_files = 0

    # Process each organisation form
    for organisation_form_directory in organisation_form_directories:
        organisation_form_name = organisation_form_directory.name
        csv_files = sorted(organisation_form_directory.glob("*.csv"))

        if not csv_files:
            continue

        # Count companies in each letter bucket
        total_companies_in_org_form = 0
        companies_per_letter_bucket = {}

        for csv_file in csv_files:
            try:
                csv_dataframe = pd.read_csv(csv_file, low_memory=False)
                company_count = len(csv_dataframe)

                letter_bucket = csv_file.stem  # A, B, C, ..., Z, OTHER
                companies_per_letter_bucket[letter_bucket] = company_count

                total_companies_in_org_form += company_count
                grand_total_files += 1

            except Exception as error:
                print(f"⚠️  Warning: Could not read {csv_file}: {error}")

        grand_total_companies += total_companies_in_org_form

        # Display statistics for this organisation form
        print(f"\n{organisation_form_name}: {total_companies_in_org_form:,} companies across {len(csv_files)} CSV files")

        # Show top 5 letter buckets by company count
        sorted_letter_buckets = sorted(
            companies_per_letter_bucket.items(),
            key=lambda item: item[1],
            reverse=True
        )[:5]

        for letter_bucket, company_count in sorted_letter_buckets:
            percentage = (company_count / total_companies_in_org_form) * 100
            print(f"  • {letter_bucket:8s}: {company_count:8,} companies ({percentage:5.1f}%)")

    # Display grand totals
    print("\n" + "=" * 70)
    print(f"📈 TOTAL: {grand_total_companies:,} companies in {grand_total_files} CSV files")
    print("=" * 70)


if __name__ == "__main__":
    display_company_database_statistics()
