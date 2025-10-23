"""Helpers for inspecting BigQuery table activity.

This module uses Application Default Credentials to connect to BigQuery and
return table metadata for a configured list of datasets. Tables whose names
contain any excluded substring are filtered out from the output. For every
remaining table we return both the last updated timestamp and the latest query
time pulled from ``INFORMATION_SCHEMA.JOBS_BY_PROJECT``.

Example:
    >>> from shared_helpers.get_bq_metadata.table_usage_tracker import (
    ...     save_table_activity_csv,
    ... )
    >>> save_table_activity_csv()
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

DEFAULT_PROJECT_ID = "proje "
TARGET_DATASETS: Tuple[str, ...] = (
    "dataset1",
    "dataset2",
    "dataset3",
)
EXCLUDED_TABLE_NAME_SUBSTRINGS: Tuple[str, ...] = ("irrelevant table names", "irrelevant table names")
DEFAULT_LOCATION = "US"


@dataclass
class TableActivity:
    """Container for the activity metadata of a BigQuery table."""

    dataset_id: str
    table_id: str
    last_updated: Optional[datetime]
    last_queried: Optional[datetime]
    creation_time: Optional[datetime]
    row_count: Optional[int]
    size_bytes: Optional[int]


def fetch_table_activity(
    *, client: Optional[bigquery.Client] = None
) -> List[TableActivity]:
    """Return activity details for tables defined in ``TARGET_DATASETS``.

    Args:
        client: Optional BigQuery client. When not provided the function will
            instantiate one using the current ADC configuration.

    Returns:
        A list of :class:`TableActivity` entries describing each table that
        remains after applying the exclusion rules.
    """

    bq_client = client or bigquery.Client(project=DEFAULT_PROJECT_ID)
    exclusions = _normalize_exclusions(EXCLUDED_TABLE_NAME_SUBSTRINGS)

    last_query_lookup = _fetch_last_query_times(
        bq_client=bq_client,
        project_id=DEFAULT_PROJECT_ID,
        datasets=TARGET_DATASETS,
        location=DEFAULT_LOCATION,
    )

    activities: List[TableActivity] = []
    for dataset_id in TARGET_DATASETS:
        try:
            table_rows = _query_dataset_tables(
                bq_client=bq_client,
                project_id=DEFAULT_PROJECT_ID,
                dataset_id=dataset_id,
                location=DEFAULT_LOCATION,
            )
        except NotFound:
            logging.warning("Dataset %s.%s not found", DEFAULT_PROJECT_ID, dataset_id)
            continue

        for row in table_rows:
            table_id = row["table_name"]
            if _is_excluded(table_id, exclusions):
                continue

            key = (dataset_id, table_id)
            activities.append(
                TableActivity(
                    dataset_id=dataset_id,
                    table_id=table_id,
                    last_updated=row["last_modified_time"],
                    last_queried=last_query_lookup.get(key),
                    creation_time=row["creation_time"],
                    row_count=row["row_count"],
                    size_bytes=row["size_bytes"],
                )
            )

    return activities


def save_table_activity_csv(
    path: Union[Path, str] = "table_usage_tracking.csv",
    *,
    client: Optional[bigquery.Client] = None,
) -> Path:
    """Persist the current table activity snapshot to ``path``.

    The directory that contains ``path`` is created automatically.
    """

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "dataset_id",
        "table_id",
        "last_updated",
        "last_queried",
        "creation_time",
        "row_count",
        "size_bytes",
    ]

    activities = fetch_table_activity(client=client)
    rows = [_activity_to_row(activity) for activity in activities]

    with target_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return target_path


def _query_dataset_tables(
    *,
    bq_client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    location: str,
) -> Iterable[Mapping[str, object]]:
    query = f"""
        SELECT
          table_name,
          creation_time,
          last_altered AS last_modified_time,
          row_count,
          size_bytes
        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_type = "BASE TABLE"
    """

    job_config = bigquery.QueryJobConfig(use_legacy_sql=False)
    return bq_client.query(query, job_config=job_config, location=location)


def _fetch_last_query_times(
    *,
    bq_client: bigquery.Client,
    project_id: str,
    datasets: Sequence[str],
    location: str,
) -> Dict[Tuple[str, str], Optional[datetime]]:
    if not datasets:
        return {}

    region_prefix = _region_prefix(location)
    jobs_table = f"`{region_prefix}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`"
    query = f"""
        SELECT
          ref.dataset_id AS dataset_id,
          ref.table_id AS table_id,
          MAX(creation_time) AS last_query_time
        FROM {jobs_table}
        CROSS JOIN UNNEST(referenced_tables) AS ref
        WHERE
          job_type = "QUERY"
          AND ref.project_id = @project_id
          AND ref.dataset_id IN UNNEST(@datasets)
        GROUP BY dataset_id, table_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
            bigquery.ArrayQueryParameter("datasets", "STRING", list(datasets)),
        ],
        use_legacy_sql=False,
    )

    rows = bq_client.query(query, job_config=job_config, location=location)
    return {
        (row["dataset_id"], row["table_id"]): row["last_query_time"] for row in rows
    }


def _normalize_exclusions(values: Optional[Sequence[str]]) -> Tuple[str, ...]:
    cleaned = tuple(value.lower() for value in values or [] if value)
    return cleaned


def _is_excluded(table_id: str, exclusions: Sequence[str]) -> bool:
    table_id_lower = table_id.lower()
    return any(exclusion in table_id_lower for exclusion in exclusions)


def _region_prefix(location: str) -> str:
    location = location.strip()
    if not location:
        raise ValueError("location cannot be empty")
    return f"region-{location.lower()}"


def _activity_to_row(activity: TableActivity) -> Dict[str, object]:
    return {
        "dataset_id": activity.dataset_id,
        "table_id": activity.table_id,
        "last_updated": _format_timestamp(activity.last_updated),
        "last_queried": _format_timestamp(activity.last_queried),
        "creation_time": _format_timestamp(activity.creation_time),
        "row_count": activity.row_count,
        "size_bytes": activity.size_bytes,
    }


def _format_timestamp(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    return value.isoformat()


__all__ = ["TableActivity", "fetch_table_activity", "save_table_activity_csv"]


if __name__ == "__main__":
    save_table_activity_csv()
