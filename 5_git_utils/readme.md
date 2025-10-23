# GitHub PR Metadata Fetcher - Implementation Plan

## Overview
Create a simple Python module to fetch PR metadata from the ab-bellaventure GitHub repo with configurable lookback window and CSV output.

## Requirements
- **Metadata to fetch:**
  - PR name (title)
  - Branch name
  - Status (open/merged/closed)
  - Merge timestamp (if applicable)
  - First comment in conversation
- **Lookback window:** Filter by last updated date, default 24 hours
- **Output:** CSV file in same directory

## Implementation Approach

### 1. Create `fetch_pr_metadata.py`
- Location: `/Users/greghills/dev/ab-bellaventure/utils_local/git_utils_/`
- Use GitHub CLI (`gh`) commands to fetch data:
  - `gh pr list` with filters for updated date
  - `gh pr view` for detailed PR information
- Follow existing patterns from `cloudrun_service_url_fetcher`

### 2. Key Features
- **CLI arguments:**
  - `--lookback-hours`: Configurable lookback window (default 24)
  - `--output-dir`: Optional output directory (default: current directory)
  - `--repo`: Repository (default: ab-bellaventure)
- **Data processing:**
  - Calculate lookback datetime from current time
  - Fetch PRs updated within window
  - Extract metadata for each PR
  - Handle merged vs closed status
- **CSV output:**
  - Headers: pr_name, branch_name, status, merge_timestamp, first_comment
  - Timestamped filename: `pr_metadata_{timestamp}.csv`

### 3. Error Handling
- Check if `gh` CLI is available
- Handle authentication errors
- Log skipped/failed PRs
- Validate repo exists

## Files to Create
1. `fetch_pr_metadata.py` - Main script
2. `plan.md` - This planning document

## Dependencies
- Python 3 (already available)
- GitHub CLI (`gh`) - already installed at `/opt/homebrew/bin/gh`
- Standard library: `argparse`, `subprocess`, `csv`, `logging`, `datetime`

## Usage Example
```bash
# Fetch PRs updated in last 24 hours (default)
python fetch_pr_metadata.py

# Fetch PRs updated in last 7 days
python fetch_pr_metadata.py --lookback-hours 168

# Specify custom output directory
python fetch_pr_metadata.py --lookback-hours 48 --output-dir /path/to/output
```

## Implementation Status
- [x] Planning complete
- [ ] Script implementation
- [ ] Testing
