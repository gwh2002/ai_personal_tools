#!/usr/bin/env python3
"""
Table Comparison Test - Refactored Version
This test verifies if two tables are identical by checking:
1. Row counts
2. Column counts
3. Data types
4. Actual data values
5. NULL handling

Usage Options:
1. Run with default configuration:
   ./table_comparison_refactored.py

2. Override specific table names (use full table path):
   ./table_comparison_refactored.py --table1 "project.dataset.table1" --table2 "project.dataset.table2"

3. Compare only a subset of data using a WHERE clause:
   ./table_comparison_refactored.py --where-clause "where time_period >= '2024-01-01'"

4. Compare specific columns only:
   ./table_comparison_refactored.py --specific-columns "company_name, time_period, values"

5. Order results for better readability:
   ./table_comparison_refactored.py --order-by-clause "order by company_name desc, time_period"
"""

import argparse
import csv
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from google.cloud import bigquery

# Default configuration
DEFAULT_CONFIG = {
    "table1": "project.dataset.table",
    "table2": "project.dataset.table2",
    "where_clause": None,
    "order_by_clause": None,
    "specific_columns": None,
}


class QueryBuilder:
    """Helper class to build SQL queries consistently"""

    @staticmethod
    def normalize_where_clause(where_clause: Optional[str]) -> Optional[str]:
        """Ensure WHERE clause starts with 'where' keyword"""
        if not where_clause:
            return None
        where_clause = where_clause.strip()
        if not where_clause.lower().startswith("where"):
            where_clause = f"where {where_clause}"
        return where_clause

    @staticmethod
    def normalize_order_by_clause(order_by_clause: Optional[str]) -> Optional[str]:
        """Ensure ORDER BY clause starts with 'order by' keywords"""
        if not order_by_clause:
            return None
        order_by_clause = order_by_clause.strip()
        if not order_by_clause.lower().startswith("order by"):
            order_by_clause = f"order by {order_by_clause}"
        return order_by_clause

    @staticmethod
    def build_column_list(
        columns: Optional[str], common_columns: Optional[Set[str]] = None
    ) -> str:
        """Build column list for SELECT statements"""
        if columns:
            return columns
        elif common_columns:
            return ", ".join(sorted(common_columns))
        else:
            return "*"

    @staticmethod
    def build_row_count_query(table: str, where_clause: Optional[str] = None) -> str:
        """Build a row count query"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where_clause:
            query += f" {where_clause}"
        return query

    @staticmethod
    def build_except_distinct_query(
        table1: str,
        table2: str,
        columns: str,
        where_clause: Optional[str] = None,
        order_by_clause: Optional[str] = None,
        limit: Optional[int] = None,
        add_source_column: Optional[str] = None,
    ) -> str:
        """
        Build an EXCEPT DISTINCT query with proper structure

        Args:
            table1: First table (rows from this table)
            table2: Second table (excluding rows from this table)
            columns: Column list to select
            where_clause: Optional WHERE clause
            order_by_clause: Optional ORDER BY clause
            limit: Optional LIMIT
            add_source_column: Optional source column to add (e.g., 'exclusive_to_table1')
        """
        # Build the basic EXCEPT DISTINCT query
        where_part = f" {where_clause}" if where_clause else ""

        except_query = f"""
SELECT {columns} FROM {table1}{where_part}
EXCEPT DISTINCT
SELECT {columns} FROM {table2}{where_part}"""

        # If we need to add source column or order by, wrap in outer query
        if add_source_column or order_by_clause:
            if add_source_column:
                outer_select = f"SELECT *, '{add_source_column}' as source_table"
            else:
                outer_select = "SELECT *"

            query = f"{outer_select} FROM ({except_query})"

            if order_by_clause:
                query += f" {order_by_clause}"
        else:
            query = except_query

        if limit:
            query += f" LIMIT {limit}"

        return query.strip()

    @staticmethod
    def build_union_query(
        queries: List[str], order_by_clause: Optional[str] = None
    ) -> str:
        """Build a UNION ALL query from multiple queries"""
        union_query = " UNION ALL ".join(f"({q})" for q in queries)

        if order_by_clause:
            # Wrap in outer SELECT to apply ORDER BY
            return f"SELECT * FROM ({union_query}) {order_by_clause}"

        return union_query


class TableComparator:
    """Main class for comparing tables"""

    def __init__(self, client: bigquery.Client):
        self.client = client
        self.query_builder = QueryBuilder()

    def get_table_schema(
        self, project: str, dataset: str, table_name: str
    ) -> List[Tuple[str, str]]:
        """Get schema information for a table"""
        query = f"""
        SELECT column_name, data_type 
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS` 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position
        """
        result = self.client.query(query).result()
        return [(row.column_name, row.data_type) for row in result]

    def get_row_count(self, table: str, where_clause: Optional[str] = None) -> int:
        """Get row count for a table with optional WHERE clause"""
        query = self.query_builder.build_row_count_query(table, where_clause)
        result = self.client.query(query).result()
        return next(result).count

    def analyze_schemas(
        self,
        schema1: List[Tuple[str, str]],
        schema2: List[Tuple[str, str]],
        specific_columns: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze and compare table schemas"""
        schema1_columns = set(col[0] for col in schema1)
        schema2_columns = set(col[0] for col in schema2)

        # Handle specific columns if provided
        if specific_columns:
            specified_cols = [col.strip() for col in specific_columns.split(",")]
            common_columns = (
                set(specified_cols)
                .intersection(schema1_columns)
                .intersection(schema2_columns)
            )
            missing_cols = set(specified_cols) - common_columns
        else:
            common_columns = schema1_columns.intersection(schema2_columns)
            missing_cols = set()

        # Find differences
        only_in_table1 = schema1_columns - schema2_columns
        only_in_table2 = schema2_columns - schema1_columns

        # Check for type mismatches in common columns
        schema1_dict = dict(schema1)
        schema2_dict = dict(schema2)

        schema_mismatches = []
        for col in common_columns:
            if col in schema1_dict and col in schema2_dict:
                if schema1_dict[col] != schema2_dict[col]:
                    schema_mismatches.append(
                        (col, schema1_dict[col], schema2_dict[col])
                    )

        return {
            "common_columns": common_columns,
            "only_in_table1": only_in_table1,
            "only_in_table2": only_in_table2,
            "schema_mismatches": schema_mismatches,
            "missing_specified_cols": missing_cols,
            "schemas_identical": len(schema1) == len(schema2)
            and not schema_mismatches
            and not specific_columns,
        }

    def check_data_differences(
        self, table1: str, table2: str, columns: str, where_clause: Optional[str] = None
    ) -> bool:
        """Check if there are data differences between tables"""
        query = f"""
        SELECT 
          CASE 
            WHEN EXISTS (
              SELECT {columns} FROM {table1}{' ' + where_clause if where_clause else ''}
              EXCEPT DISTINCT
              SELECT {columns} FROM {table2}{' ' + where_clause if where_clause else ''}
            ) OR EXISTS (
              SELECT {columns} FROM {table2}{' ' + where_clause if where_clause else ''}
              EXCEPT DISTINCT
              SELECT {columns} FROM {table1}{' ' + where_clause if where_clause else ''}
            ) THEN TRUE
            ELSE FALSE
          END as has_differences
        """
        result = self.client.query(query).result()
        return next(result).has_differences

    def get_sample_differences(
        self,
        table1: str,
        table2: str,
        columns: str,
        where_clause: Optional[str] = None,
        order_by_clause: Optional[str] = None,
        limit: int = 10,
    ) -> Tuple[List[Dict], List[Dict]]:
        """Get sample of differences between tables"""
        # Rows in table1 but not in table2
        query1 = self.query_builder.build_except_distinct_query(
            table1, table2, columns, where_clause, order_by_clause, limit
        )

        # Rows in table2 but not in table1
        query2 = self.query_builder.build_except_distinct_query(
            table2, table1, columns, where_clause, order_by_clause, limit
        )

        result1 = self.client.query(query1).result()
        result2 = self.client.query(query2).result()

        return ([dict(row) for row in result1], [dict(row) for row in result2])

    def export_all_differences(
        self,
        table1: str,
        table2: str,
        table1_name: str,
        table2_name: str,
        columns: str,
        output_file: str,
        where_clause: Optional[str] = None,
        order_by_clause: Optional[str] = None,
    ) -> int:
        """Export all differences to CSV file"""
        # Build queries for differences
        query1 = self.query_builder.build_except_distinct_query(
            table1,
            table2,
            columns,
            where_clause,
            add_source_column=f"exclusive_to_{table1_name}",
        )

        query2 = self.query_builder.build_except_distinct_query(
            table2,
            table1,
            columns,
            where_clause,
            add_source_column=f"exclusive_to_{table2_name}",
        )

        # Combine with UNION ALL
        combined_query = self.query_builder.build_union_query(
            [query1, query2], order_by_clause
        )

        # Execute and export
        result = self.client.query(combined_query).result()
        rows = [dict(row) for row in result]

        if rows:
            with open(output_file, "w", newline="") as csvfile:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

        return len(rows)


def execute_comparison(
    client: bigquery.Client,
    table1_full: str,
    table2_full: str,
    table1_project: str,
    table1_dataset: str,
    table1_name: str,
    table2_project: str,
    table2_dataset: str,
    table2_name: str,
    where_clause: Optional[str] = None,
    order_by_clause: Optional[str] = None,
    specific_columns: Optional[str] = None,
):
    """Execute the table comparison"""
    comparator = TableComparator(client)
    query_builder = QueryBuilder()

    # Normalize clauses
    where_clause = query_builder.normalize_where_clause(where_clause)
    order_by_clause = query_builder.normalize_order_by_clause(order_by_clause)

    try:
        # Get schemas
        print("Analyzing table schemas...")
        schema1 = comparator.get_table_schema(
            table1_project, table1_dataset, table1_name
        )
        schema2 = comparator.get_table_schema(
            table2_project, table2_dataset, table2_name
        )

        print(f"Table 1 ({table1_full}): {len(schema1)} columns")
        print(f"Table 2 ({table2_full}): {len(schema2)} columns")

        # Analyze schemas
        schema_analysis = comparator.analyze_schemas(schema1, schema2, specific_columns)

        if schema_analysis["only_in_table1"]:
            print("\nColumns only in Table 1:")
            for col in sorted(schema_analysis["only_in_table1"]):
                print(f"  - {col}")

        if schema_analysis["only_in_table2"]:
            print("\nColumns only in Table 2:")
            for col in sorted(schema_analysis["only_in_table2"]):
                print(f"  - {col}")

        if schema_analysis["missing_specified_cols"]:
            print("\nWarning: Some specified columns not found in both tables:")
            for col in sorted(schema_analysis["missing_specified_cols"]):
                print(f"  - {col}")

        if not schema_analysis["common_columns"]:
            print("\nERROR: No common columns found between tables!")
            return

        print(f"\nCommon columns: {len(schema_analysis['common_columns'])}")
        print("Common columns:", ", ".join(sorted(schema_analysis["common_columns"])))

        if schema_analysis["schema_mismatches"]:
            print("\nSchema mismatches in common columns:")
            for col, type1, type2 in schema_analysis["schema_mismatches"]:
                print(f"  - {col}: {type1} vs {type2}")

        # Get row counts
        print("\nComparing row counts...")
        count1 = comparator.get_row_count(table1_full, where_clause)
        count2 = comparator.get_row_count(table2_full, where_clause)

        print(f"Table 1 ({table1_full}): {count1:,} rows")
        print(f"Table 2 ({table2_full}): {count2:,} rows")
        print(f"Difference: {abs(count1 - count2):,} rows")

        # Build column list for comparison
        columns = query_builder.build_column_list(
            specific_columns, schema_analysis["common_columns"]
        )

        # Check for data differences
        print("\nChecking for data differences...")
        has_differences = comparator.check_data_differences(
            table1_full, table2_full, columns, where_clause
        )

        if not has_differences:
            print("\nTest Result: PASS - Tables are identical for compared columns")
        else:
            print("\nTest Result: FAIL - Tables have differences")

            print("\n" + "=" * 60)
            print("DETAILED DIFFERENCE ANALYSIS")
            print("=" * 60)

            # Get sample differences
            rows_only_in_1, rows_only_in_2 = comparator.get_sample_differences(
                table1_full,
                table2_full,
                columns,
                where_clause,
                order_by_clause,
                limit=10,
            )

            print(f"\n1. Sample rows in {table1_full} but not in {table2_full}:")
            print(f"   Found {len(rows_only_in_1)} rows (showing up to 10):")
            for i, row in enumerate(rows_only_in_1):
                print(f"   Row {i+1}: {row}")

            print(f"\n2. Sample rows in {table2_full} but not in {table1_full}:")
            print(f"   Found {len(rows_only_in_2)} rows (showing up to 10):")
            for i, row in enumerate(rows_only_in_2):
                print(f"   Row {i+1}: {row}")

            # Export all differences
            print("\n3. Exporting all differences to CSV...")
            output_file = "table_row_differences.csv"
            total_diffs = comparator.export_all_differences(
                table1_full,
                table2_full,
                table1_name,
                table2_name,
                columns,
                output_file,
                where_clause,
                order_by_clause,
            )
            print(f"   All differences written to {output_file} ({total_diffs} rows)")

    except Exception as e:
        print(f"Error executing comparison: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two BigQuery tables for equality"
    )
    parser.add_argument(
        "--table1",
        default=DEFAULT_CONFIG["table1"],
        help=f'First table full name (default: {DEFAULT_CONFIG["table1"]})',
    )
    parser.add_argument(
        "--table2",
        default=DEFAULT_CONFIG["table2"],
        help=f'Second table full name (default: {DEFAULT_CONFIG["table2"]})',
    )
    parser.add_argument(
        "--where-clause",
        default=DEFAULT_CONFIG["where_clause"],
        help="WHERE clause to filter data (e.g., \"where time_period >= '2024-01-01'\")",
    )
    parser.add_argument(
        "--order-by-clause",
        default=DEFAULT_CONFIG["order_by_clause"],
        help='ORDER BY clause for result ordering (e.g., "order by company_name desc, time_period")',
    )
    parser.add_argument(
        "--specific-columns",
        default=DEFAULT_CONFIG["specific_columns"],
        help='Specific columns to compare (e.g., "company_name, time_period, values")',
    )

    args = parser.parse_args()

    # Parse full table names to extract project, dataset, and table components
    def parse_table_path(table_path):
        parts = table_path.split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Table path must be in format 'project.dataset.table', got: {table_path}"
            )
        return parts[0], parts[1], parts[2]

    try:
        table1_project, table1_dataset, table1_name = parse_table_path(args.table1)
        table2_project, table2_dataset, table2_name = parse_table_path(args.table2)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Comparing tables:")
    print(f"Table 1: {args.table1}")
    print(f"Table 2: {args.table2}")

    if args.where_clause:
        print(f"Filter: {args.where_clause}")
    if args.order_by_clause:
        print(f"Order: {args.order_by_clause}")
    if args.specific_columns:
        print(f"Columns: {args.specific_columns}")

    # Initialize BigQuery client (use first table's project as default)
    client = bigquery.Client(project=table1_project)

    # Execute comparison
    execute_comparison(
        client,
        args.table1,
        args.table2,
        table1_project,
        table1_dataset,
        table1_name,
        table2_project,
        table2_dataset,
        table2_name,
        args.where_clause,
        args.order_by_clause,
        args.specific_columns,
    )


if __name__ == "__main__":
    main()
