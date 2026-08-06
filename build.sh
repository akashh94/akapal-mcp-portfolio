#!/usr/bin/env bash

set -euo pipefail

# Keep the checked-out branch in sync before building
git pull

export PROJECT_ID="labs-gcp-msls-16495-1782829337"
export REGION="us-east1"
# Build the container image tag:
#   ${REGION}-docker.pkg.dev/${PROJECT_ID}/<repository>/<image>:<tag>
#   - ${REGION}-docker.pkg.dev  -> regional Artifact Registry hostname
#   - akapal-geap-ui            -> Artifact Registry repository (created in
#                                  the Google Cloud console)
#   - akapal-mcp-portfolio      -> image name within that repository
#   - $(git rev-parse --short HEAD) -> short git SHA as the version tag, so
#                                  every build gets a unique, traceable image
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/akapal-geap-ui/akapal-mcp-portfolio:$(git rev-parse --short HEAD)"

echo "$IMAGE"

# Build with the repo root as the context so Cloud Build uses the root Dockerfile
gcloud builds submit . --tag "$IMAGE" --project "$PROJECT_ID"
