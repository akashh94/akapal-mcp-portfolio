#!/usr/bin/env bash

set -eo pipefail

export PROJECT_ID="adk-tut-499512"
# Cloud Run service region (us-central1 has capacity; us-east1 was quota-blocked)
export REGION="${REGION:-us-central1}"
# Artifact Registry repo lives in us-east1; Cloud Run pulls it from there,
# so the repo region is independent of the service region above.
export ARTIFACT_REGION="${ARTIFACT_REGION:-us-east1}"
# Build the container image tag:
#   ${ARTIFACT_REGION}-docker.pkg.dev/${PROJECT_ID}/<repository>/<image>:<tag>
#   - ${ARTIFACT_REGION}-docker.pkg.dev  -> regional Artifact Registry hostname
#   - akapal-geap-ui            -> Artifact Registry repository (created in
#                                  the Google Cloud console)
#   - akapal-mcp-portfolio      -> image name within that repository
#   - $(git rev-parse --short HEAD) -> short git SHA as the version tag, so
#                                  every build gets a unique, traceable image
export IMAGE="${ARTIFACT_REGION}-docker.pkg.dev/${PROJECT_ID}/akapal-geap-ui/akapal-mcp-portfolio:$(git rev-parse --short HEAD)"

# Deploy as mcp-portfolio so the service URL stays
# https://mcp-portfolio-492310803820.us-east1.run.app/sse, which the agent's
# MCP_PORTFOLIO_URL already points at. No extra env vars needed: Cloud Run
# injects PORT and the app binds 0.0.0.0.
gcloud run deploy mcp-portfolio \
    --image "$IMAGE" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --min-instances 1 \
    --max-instances 1
