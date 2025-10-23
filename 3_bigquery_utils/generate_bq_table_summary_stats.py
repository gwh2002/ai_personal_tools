def generate_table_summary(project_id, dataset_id, table_id):
    """
    Auto-generate comprehensive table summary for Claude context
    """

    tables_to_document = [
        ("dataset1", "table1"),
        ("dataset2", "table2"),
        ("dataset3", "table3"),
    ]

    client = bigquery.Client()

    # Basic stats
    basic_query = f"""
    SELECT 
      COUNT(*) as total_rows,
      MIN(time_period) as earliest_date,
      MAX(time_period) as latest_date,
      COUNT(DISTINCT company_name) as distinct_companies,
      COUNT(DISTINCT metric_name) as distinct_metrics,
      COUNTIF(metric_value IS NULL OR metric_value = '') as null_values,
      ROUND(
        COUNTIF(metric_value IS NULL OR metric_value = '') / COUNT(*) * 100, 
        2
      ) as null_percentage
    FROM `{project_id}.{dataset_id}.{table_id}`
    """

    # Company completeness
    company_query = f"""
    SELECT 
      company_name,
      COUNT(*) as total_records,
      MIN(time_period) as first_date,
      MAX(time_period) as last_date,
      COUNT(DISTINCT EXTRACT(YEAR FROM time_period)) as years_of_data,
      COUNTIF(metric_value IS NULL OR metric_value = '') as null_records,
      ROUND(
        COUNTIF(metric_value IS NULL OR metric_value = '') / COUNT(*) * 100, 
        2
      ) as null_pct
    FROM `{project_id}.{dataset_id}.{table_id}`
    GROUP BY company_name
    ORDER BY total_records DESC
    """

    # Metric completeness
    metric_query = f"""
    SELECT 
      metric_name,
      COUNT(*) as total_records,
      COUNT(DISTINCT company_name) as companies_with_metric,
      COUNTIF(metric_value IS NULL OR metric_value = '') as null_records,
      ROUND(COUNTIF(metric_value IS NULL OR metric_value = '') / COUNT(*) * 100, 2) as null_pct
    FROM `{project_id}.{dataset_id}.{table_id}`
    GROUP BY metric_name
    ORDER BY companies_with_metric DESC
    """

    # Generate markdown output
    basic_stats = client.query(basic_query).to_dataframe().iloc[0]

    markdown = f"""
## {dataset_id}.{table_id}
**Row Count**: {basic_stats['total_rows']:,} rows
**Date Range**: {basic_stats['earliest_date']} to {basic_stats['latest_date']}
**Companies**: {basic_stats['distinct_companies']} distinct companies
**Metrics**: {basic_stats['distinct_metrics']} distinct metrics
**Data Quality**: {basic_stats['null_percentage']}% null values

### Top Companies by Data Volume
{client.query(company_query).to_dataframe().head(10).to_markdown(index=False)}

### Most Common Metrics
{client.query(metric_query).to_dataframe().head(10).to_markdown(index=False)}
"""

    return markdown


with open(".claude/table_schemas.md", "w") as f:
    f.write("# BigQuery Table Schemas & Statistics\n\n")
    for dataset, table in tables_to_document:
        summary = generate_table_summary("assembled-wh", dataset, table)
        f.write(summary + "\n\n")
