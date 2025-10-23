#!/usr/bin/env python3
"""
Fetch GitHub PR metadata and save to CSV file.

This script fetches pull request metadata from a GitHub repository
with a configurable lookback window based on last updated date.

Usage:
    python fetch_pr_metadata.py
    python fetch_pr_metadata.py --lookback-hours 168
    python fetch_pr_metadata.py --repo owner/repo --lookback-hours 48
"""

import argparse
import csv
import json
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configuration
DEFAULT_REPO = "owner/repo"
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_OUTPUT_DIR = Path(__file__).parent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_command(cmd: List[str]) -> str:
    """
    Run a command and return stdout.

    Args:
        cmd: Command and arguments as list

    Returns:
        Command stdout

    Raises:
        subprocess.CalledProcessError: If command fails
    """
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        raise


def check_gh_cli() -> bool:
    """
    Check if GitHub CLI is available and authenticated.

    Returns:
        True if gh CLI is available and authenticated
    """
    try:
        run_command(["gh", "--version"])
        run_command(["gh", "auth", "status"])
        return True
    except subprocess.CalledProcessError:
        logger.error("GitHub CLI (gh) is not available or not authenticated")
        logger.error("Please install: brew install gh")
        logger.error("Then authenticate: gh auth login")
        return False


def fetch_pr_list(repo: str, lookback_hours: int) -> List[Dict[str, Any]]:
    """
    Fetch list of PRs updated within the lookback window.

    Args:
        repo: Repository name (owner/repo or just repo)
        lookback_hours: Hours to look back from now

    Returns:
        List of PR metadata dictionaries
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    logger.info(f"Fetching PRs updated since {cutoff_date.isoformat()}")
    logger.info(f"Repository: {repo}")

    # Fetch all PRs (open, closed, merged) with JSON format
    cmd = [
        "gh",
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "all",
        "--limit",
        "1000",
        "--json",
        "number,title,headRefName,state,mergedAt,updatedAt,url",
    ]

    output = run_command(cmd)
    all_prs = json.loads(output)

    # Filter by updated date
    filtered_prs = []
    for pr in all_prs:
        updated_str = pr.get("updatedAt", "")
        if updated_str:
            # Parse ISO8601 datetime
            updated_dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            if updated_dt >= cutoff_date:
                filtered_prs.append(pr)

    logger.info(
        f"Found {len(filtered_prs)} PR(s) updated in last {lookback_hours} hours"
    )
    return filtered_prs


def fetch_pr_details(repo: str, pr_number: int) -> Optional[str]:
    """
    Fetch detailed PR information including first comment.

    Args:
        repo: Repository name
        pr_number: PR number

    Returns:
        First comment/body of the PR, or None if not available
    """
    try:
        cmd = [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "body",
        ]
        output = run_command(cmd)
        pr_data = json.loads(output)
        return pr_data.get("body", "").strip()
    except Exception as e:
        logger.warning(f"Could not fetch details for PR #{pr_number}: {e}")
        return None


def process_pr_metadata(pr: Dict[str, Any], repo: str) -> Dict[str, Any]:
    """
    Process and extract metadata from a PR.

    Args:
        pr: Raw PR data from gh CLI
        repo: Repository name

    Returns:
        Cleaned PR metadata dictionary
    """
    pr_number = pr.get("number")
    title = pr.get("title", "")
    branch = pr.get("headRefName", "")
    state = pr.get("state", "").lower()
    merged_at = pr.get("mergedAt", "")

    # Determine status: open, merged, or closed
    if state == "merged":
        status = "merged"
    elif state == "open":
        status = "open"
    else:
        status = "closed"

    # Format merge timestamp
    merge_timestamp = ""
    if merged_at:
        try:
            merge_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            merge_timestamp = merge_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            merge_timestamp = merged_at

    # Fetch first comment (PR body)
    first_comment = fetch_pr_details(repo, pr_number) or ""

    return {
        "pr_name": title,
        "branch_name": branch,
        "status": status,
        "merge_timestamp": merge_timestamp,
        "first_comment": first_comment,
        "pr_number": pr_number,
        "url": pr.get("url", ""),
    }


def save_to_csv(pr_metadata: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Save PR metadata to CSV file.

    Args:
        pr_metadata: List of processed PR metadata
        output_dir: Directory to save CSV

    Returns:
        Path to created CSV file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pr_metadata_{timestamp}.csv"
    output_path = output_dir / filename

    # Define CSV columns
    fieldnames = [
        "pr_name",
        "branch_name",
        "status",
        "merge_timestamp",
        "first_comment",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(pr_metadata)

    logger.info(f"Saved {len(pr_metadata)} PR(s) to {output_path}")
    return output_path


def main() -> None:
    """Main function to fetch PR metadata and save to CSV."""
    parser = argparse.ArgumentParser(
        description="Fetch GitHub PR metadata and save to CSV"
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"Repository name (owner/repo or just repo, default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=DEFAULT_LOOKBACK_HOURS,
        help=f"Hours to look back from now (default: {DEFAULT_LOOKBACK_HOURS})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: script directory)",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("GitHub PR Metadata Fetcher")
    logger.info("=" * 70)

    # Check GitHub CLI availability
    if not check_gh_cli():
        return

    # Fetch PRs
    prs = fetch_pr_list(args.repo, args.lookback_hours)

    if not prs:
        logger.info("No PRs found in the specified timeframe")
        return

    # Process each PR
    processed_prs = []
    for pr in prs:
        pr_number = pr.get("number", "unknown")
        try:
            metadata = process_pr_metadata(pr, args.repo)
            processed_prs.append(metadata)
            logger.info(f"✓ Processed PR #{pr_number}: {metadata['pr_name'][:50]}")
        except Exception as e:
            logger.error(f"✗ Error processing PR #{pr_number}: {e}")
            continue

    # Save to CSV
    if processed_prs:
        output_path = save_to_csv(processed_prs, args.output_dir)
        logger.info("=" * 70)
        logger.info(f"✓ Done! Output saved to: {output_path}")
        logger.info("=" * 70)
    else:
        logger.warning("No PRs were successfully processed")


if __name__ == "__main__":
    main()
