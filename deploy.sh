#!/usr/bin/env bash

set -eo pipefail

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
