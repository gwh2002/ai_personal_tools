#!/usr/bin/env python3
"""
Fetch Cloud Run service metadata and save to JSON file.

This script fetches all Cloud Run services from a GCP project and saves
key metadata (URLs, images, resources, settings) to a JSON file.

Usage:
    python fetch_cloudrun_services.py [--output-dir /path/to/output]
    python fetch_cloudrun_services.py --project my-project --region us-east1
"""

import argparse
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    from .config import (
        DEFAULT_OUTPUT_DIR,
        OUTPUT_FILENAME,
        PROJECT_ID,
        REGION,
        SKIP_SERVICES,
    )
except ImportError:
    from config import (  # type: ignore
        DEFAULT_OUTPUT_DIR,
        OUTPUT_FILENAME,
        PROJECT_ID,
        REGION,
        SKIP_SERVICES,
    )

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


def fetch_cloudrun_services(project: str, region: str) -> List[Dict[str, Any]]:
    """
    Fetch all Cloud Run services from GCP.

    Args:
        project: GCP project ID
        region: GCP region

    Returns:
        List of service metadata dictionaries
    """
    logger.info(f"Fetching Cloud Run services for {project}/{region}...")

    cmd = [
        "gcloud",
        "run",
        "services",
        "list",
        f"--project={project}",
        f"--region={region}",
        "--format=json",
    ]

    output = run_command(cmd)
    services = json.loads(output)

    logger.info(f"Found {len(services)} service(s)")
    return services


def extract_service_metadata(
    service: Dict[str, Any], project: str, region: str
) -> Dict[str, Any]:
    """
    Extract relevant metadata from a Cloud Run service.

    Args:
        service: Raw service data from gcloud
        project: GCP project ID
        region: GCP region

    Returns:
        Cleaned service metadata
    """
    metadata = service.get("metadata", {})
    spec = service.get("spec", {})
    status = service.get("status", {})
    template = spec.get("template", {})
    template_metadata = template.get("metadata", {})
    template_spec = template.get("spec", {})
    containers = template_spec.get("containers", [])
    container = containers[0] if containers else {}

    # Extract key information
    service_name = metadata.get("name", "unknown")

    # Get URLs
    urls = []
    if status.get("url"):
        urls.append(status["url"])
    if status.get("address", {}).get("url"):
        url = status["address"]["url"]
        if url not in urls:
            urls.append(url)

    # Extract annotations
    annotations = metadata.get("annotations", {})
    template_annotations = template_metadata.get("annotations", {})

    # Get container resources
    resources = container.get("resources", {})
    limits = resources.get("limits", {})

    # Get environment variables (if any)
    env_vars = {}
    for env_var in container.get("env", []):
        env_vars[env_var.get("name", "")] = env_var.get("value", "")

    # Build simplified metadata
    simplified = {
        "name": service_name,
        "urls": urls,
        "primary_url": urls[0] if urls else None,
        "image": container.get("image"),
        "region": region,
        "project": project,
        "service_account": template_spec.get("serviceAccountName"),
        "resources": {
            "cpu": limits.get("cpu"),
            "memory": limits.get("memory"),
        },
        "scaling": {
            "min_instances": template_annotations.get(
                "autoscaling.knative.dev/minScale"
            ),
            "max_instances": template_annotations.get(
                "autoscaling.knative.dev/maxScale"
            ),
        },
        "timeout_seconds": template_spec.get("timeoutSeconds"),
        "container_concurrency": template_spec.get("containerConcurrency"),
        "ingress": annotations.get("run.googleapis.com/ingress"),
        "authentication": "public"
        if annotations.get("run.googleapis.com/invoker-iam-disabled") == "true"
        else "authenticated",
        "cpu_throttling": template_annotations.get(
            "run.googleapis.com/cpu-throttling", "true"
        )
        != "false",
        "startup_cpu_boost": template_annotations.get(
            "run.googleapis.com/startup-cpu-boost"
        )
        == "true",
        "environment_variables": env_vars if env_vars else None,
        "created": metadata.get("creationTimestamp"),
        "generation": metadata.get("generation"),
        "latest_revision": status.get("latestReadyRevisionName"),
        "ready": any(
            c.get("type") == "Ready" and c.get("status") == "True"
            for c in status.get("conditions", [])
        ),
    }

    # Remove None values for cleaner output
    simplified = {k: v for k, v in simplified.items() if v is not None}

    return simplified


def save_services_metadata(
    services: List[Dict[str, Any]], output_dir: Path, filename: str
) -> None:
    """
    Save services metadata to JSON file.

    Args:
        services: List of service metadata
        output_dir: Directory to save output
        filename: Output filename
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Create output data with metadata
    output_data = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "project": services[0]["project"] if services else None,
        "region": services[0]["region"] if services else None,
        "total_services": len(services),
        "services": services,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved metadata to {output_path}")
    logger.info(f"Total services: {len(services)}")


def main() -> None:
    """Main function to fetch and save Cloud Run services metadata."""
    parser = argparse.ArgumentParser(
        description="Fetch Cloud Run services metadata and save to JSON"
    )
    parser.add_argument(
        "--project",
        default=PROJECT_ID,
        help=f"GCP project ID (default: {PROJECT_ID})",
    )
    parser.add_argument(
        "--region",
        default=REGION,
        help=f"GCP region (default: {REGION})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--output-filename",
        default=OUTPUT_FILENAME,
        help=f"Output filename (default: {OUTPUT_FILENAME})",
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Cloud Run Services Metadata Fetcher")
    logger.info("=" * 70)

    # Fetch services
    raw_services = fetch_cloudrun_services(args.project, args.region)

    # Process services
    processed_services = []
    for service in raw_services:
        service_name = service.get("metadata", {}).get("name", "unknown")

        if service_name in SKIP_SERVICES:
            logger.warning(f"Skipping service {service_name} (configured to skip)")
            continue

        try:
            metadata = extract_service_metadata(service, args.project, args.region)
            processed_services.append(metadata)
            logger.info(f"✓ Processed {service_name}")
            logger.info(f"  URL: {metadata.get('primary_url', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Error processing {service_name}: {e}")
            continue

    # Save to file
    save_services_metadata(processed_services, args.output_dir, args.output_filename)

    logger.info("=" * 70)
    logger.info("✓ Done!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
