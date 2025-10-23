#!/usr/bin/env python3
"""
Configuration for Cloud Run service metadata fetcher.
"""

# GCP Configuration
PROJECT_ID = "projects"
REGION = "us-central1"

# Output Configuration
# Default output directory - can be overridden via command line argument
DEFAULT_OUTPUT_DIR = "docs/repo_documentation/cloudrun_services"

# Output filename
OUTPUT_FILENAME = "cloudrun_services_metadata.json"

# Services to skip (if any)
SKIP_SERVICES = []

# Fields to extract from each service
# Set to None to extract all fields, or specify a list of fields to extract
EXTRACT_FIELDS = None  # Extract everything by default
