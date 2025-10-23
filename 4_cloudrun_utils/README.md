# Cloud Run Service Metadata Fetcher

Utility to fetch Cloud Run service metadata from GCP and save it to a JSON file for documentation purposes.

## Purpose

This tool retrieves all Cloud Run services from your GCP project and extracts key information including:
- Service URLs
- Container images
- Resource allocations (CPU, memory)
- Scaling configuration
- Authentication settings
- Environment variables
- Service account
- And more...

## Prerequisites

1. Python 3.7+
2. gcloud CLI installed and configured
3. Authenticated with GCP:
   ```bash
   gcloud auth login
   ```
4. Project configured:
   ```bash
   gcloud config set project assembled-wh
   ```

## Installation

No external dependencies required. The script uses Python standard library and gcloud CLI.

## Configuration

Edit `config.py` to customize:

```python
# GCP Configuration
PROJECT_ID = "assembled-wh"
REGION = "us-central1"

# Output Configuration
DEFAULT_OUTPUT_DIR = Path(...) / "docs/repo_documentation/cloudrun_services"
OUTPUT_FILENAME = "cloudrun_services_metadata.json"

# Services to skip (if any)
SKIP_SERVICES = []
```

## Usage

### Basic usage (uses defaults from config.py):
```bash
python fetch_cloudrun_services.py
```

### Custom output directory:
```bash
python fetch_cloudrun_services.py --output-dir /path/to/output
```

### Custom project and region:
```bash
python fetch_cloudrun_services.py --project my-project --region us-east1
```

### All options:
```bash
python fetch_cloudrun_services.py \
  --project assembled-wh \
  --region us-central1 \
  --output-dir /Users/greghills/dev/ab-bellaventure/docs/repo_documentation/cloudrun_services \
  --output-filename cloudrun_services_metadata.json
```

### Run from anywhere:
```bash
cd /Users/greghills/dev/ab-bellaventure/shared_helpers/fetch_gcp_metadata_utils/cloudrun_service_url_fetcher
python fetch_cloudrun_services.py
```

## Output Format

The script generates a JSON file with the following structure:

```json
{
  "fetched_at": "2025-10-21T22:30:00Z",
  "project": "assembled-wh",
  "region": "us-central1",
  "total_services": 15,
  "services": [
    {
      "name": "ab-command-center",
      "urls": [
        "https://ab-command-center-y5j5rjce2q-uc.a.run.app",
        "https://ab-command-center-915401990209.us-central1.run.app"
      ],
      "primary_url": "https://ab-command-center-y5j5rjce2q-uc.a.run.app",
      "image": "gcr.io/assembled-wh/ab-command-center:v5",
      "region": "us-central1",
      "project": "assembled-wh",
      "service_account": "bellaventurebq@assembled-wh.iam.gserviceaccount.com",
      "resources": {
        "cpu": "1",
        "memory": "512Mi"
      },
      "scaling": {
        "min_instances": "1",
        "max_instances": "10"
      },
      "timeout_seconds": 300,
      "container_concurrency": 80,
      "ingress": "all",
      "authentication": "authenticated",
      "cpu_throttling": false,
      "startup_cpu_boost": true,
      "environment_variables": {
        "GUNICORN_WORKERS": "1",
        "GUNICORN_THREADS": "2"
      },
      "created": "2025-08-21T18:25:27.318581Z",
      "generation": 11,
      "latest_revision": "ab-command-center-00006-5r5",
      "ready": true
    }
  ]
}
```

## Default Output Location

By default, the script saves the metadata to:
```
/Users/greghills/dev/ab-bellaventure/docs/repo_documentation/cloudrun_services/cloudrun_services_metadata.json
```

This location is configured in `config.py` and can be overridden using the `--output-dir` flag.

## Similar Tools

This utility follows the same pattern as other GCP metadata fetchers in the repository:
- `/infrastructure/schedulers/pull_schedules.py` - Cloud Scheduler jobs
- `/infrastructure/cloudbuild/pull_triggers_from_cloud.py` - Cloud Build triggers

## Troubleshooting

### Permission Denied
Make sure you're authenticated and have the necessary permissions:
```bash
gcloud auth login
gcloud config set project assembled-wh
```

### Command Not Found: gcloud
Install the gcloud CLI: https://cloud.google.com/sdk/docs/install

### Empty Services List
Verify you're using the correct project and region:
```bash
gcloud run services list --project=assembled-wh --region=us-central1
```

## Example Output

When you run the script, you'll see output like:
```
2025-10-21 22:30:00 - INFO - ======================================================================
2025-10-21 22:30:00 - INFO - Cloud Run Services Metadata Fetcher
2025-10-21 22:30:00 - INFO - ======================================================================
2025-10-21 22:30:00 - INFO - Fetching Cloud Run services for assembled-wh/us-central1...
2025-10-21 22:30:02 - INFO - Found 15 service(s)
2025-10-21 22:30:02 - INFO - ✓ Processed ab-command-center
2025-10-21 22:30:02 - INFO -   URL: https://ab-command-center-y5j5rjce2q-uc.a.run.app
2025-10-21 22:30:02 - INFO - ✓ Processed ab-data-quality-checks
2025-10-21 22:30:02 - INFO -   URL: https://ab-data-quality-checks-y5j5rjce2q-uc.a.run.app
...
2025-10-21 22:30:05 - INFO - Saved metadata to /Users/greghills/dev/.../cloudrun_services_metadata.json
2025-10-21 22:30:05 - INFO - Total services: 15
2025-10-21 22:30:05 - INFO - ======================================================================
2025-10-21 22:30:05 - INFO - ✓ Done!
2025-10-21 22:30:05 - INFO - ======================================================================
```
