#!/usr/bin/env python
"""
Run BigQuery schema queries and save results to CSV files.

This module executes three BigQuery queries to fetch:
1. Column information
2. Table information
3. Table DDL

Results are saved as CSV files with the naming convention:
bq_<type>_YYYY.MM.DD.csv
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

# Define the queries and their output names
QUERIES = {
    "column_info": {
        "file": "fetch_bq_column_info.sql",
        "output_prefix": "bq_column_info",
    },
    "table_info": {"file": "fetch_bq_table_info.sql", "output_prefix": "bq_table_info"},
    "table_ddl": {"file": "fetch_bq_table_ddl.sql", "output_prefix": "bq_table_ddl"},
}


def setup_bigquery_client():
    """
    Set up BigQuery client with appropriate credentials.

    Returns:
        bigquery.Client: Authenticated BigQuery client
    """
    # Try to use Application Default Credentials first
    # This works for local development with gcloud auth application-default login
    try:
        client = bigquery.Client()
        print("✓ Using Application Default Credentials")
        return client
    except Exception as e:
        print(f"Could not use Application Default Credentials: {e}")

    # Try to use service account from environment variable
    service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if service_account_path and Path(service_account_path).exists():
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path
            )
            client = bigquery.Client(credentials=credentials)
            print(f"✓ Using service account from: {service_account_path}")
            return client
        except Exception as e:
            print(f"Error loading service account: {e}")

    # Try to create client without explicit credentials (uses default auth)
    try:
        client = bigquery.Client()
        print("✓ Using default authentication")
        return client
    except Exception as e:
        print(f"Failed to create BigQuery client: {e}")
        print("\nPlease ensure you have authenticated with:")
        print("  gcloud auth application-default login")
        print("Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        sys.exit(1)


def read_query_file(file_path):
    """
    Read SQL query from file.

    Args:
        file_path (str): Path to SQL file

    Returns:
        str: SQL query content
    """
    with open(file_path, "r") as f:
        return f.read()


def execute_query(client, query):
    """
    Execute BigQuery query and return results as DataFrame.

    Args:
        client: BigQuery client
        query (str): SQL query to execute

    Returns:
        pd.DataFrame: Query results
    """
    try:
        print("  Executing query...")
        query_job = client.query(query)
        results = query_job.to_dataframe()
        print(f"  ✓ Retrieved {len(results)} rows")
        return results
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
        raise


def save_to_csv(df, output_path):
    """
    Save DataFrame to CSV file.

    Args:
        df (pd.DataFrame): Data to save
        output_path (str): Path for output CSV file
    """
    try:
        df.to_csv(output_path, index=False)
        print(f"  ✓ Saved to: {output_path}")
        print(f"    File size: {Path(output_path).stat().st_size / 1024:.1f} KB")
    except Exception as e:
        print(f"  ✗ Failed to save CSV: {e}")
        raise


def main():
    """
    Main function to execute all queries and save results.
    """
    print("=" * 60)
    print("BigQuery Schema Query Runner")
    print("=" * 60)

    # Get current date for file naming
    current_date = datetime.now().strftime("%Y.%m.%d")
    print(f"\nDate for file naming: {current_date}")

    # Set up BigQuery client
    print("\nSetting up BigQuery client...")
    client = setup_bigquery_client()

    # Get script directory
    script_dir = Path(__file__).parent

    # Track successful and failed queries
    successful = []
    failed = []

    # Execute each query
    for query_name, config in QUERIES.items():
        print(f"\n{'-'*40}")
        print(f"Processing: {query_name}")
        print(f"{'-'*40}")

        try:
            # Read query
            query_file = script_dir / config["file"]
            if not query_file.exists():
                print(f"  ✗ Query file not found: {query_file}")
                failed.append(query_name)
                continue

            print(f"  Reading query from: {config['file']}")
            query = read_query_file(query_file)

            # Execute query
            df = execute_query(client, query)

            # Save to CSV
            output_filename = f"{config['output_prefix']}_{current_date}.csv"
            output_path = script_dir / output_filename
            save_to_csv(df, output_path)

            successful.append(query_name)

        except Exception as e:
            print(f"  ✗ Failed to process {query_name}: {e}")
            failed.append(query_name)

    # Print summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"✓ Successful: {len(successful)}/{len(QUERIES)}")
    if successful:
        for name in successful:
            print(f"  - {name}")

    if failed:
        print(f"\n✗ Failed: {len(failed)}/{len(QUERIES)}")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)

    print("\n✅ All queries completed successfully!")


if __name__ == "__main__":
    main()
