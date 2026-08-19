#!/usr/bin/env bash

set -euo pipefail

# Resolve this project's root.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Office environment config (self-contained): PROJECT_ID / REGION /
# ARTIFACT_REGISTRY / SERVICE_NAME all come from geap.deploy.env — the
# single source of truth for the office deployment.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/geap.deploy.env"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY}/akapal-mcp-portfolio:$(git rev-parse --short HEAD)"

# Deploy the MCP server as ${SERVICE_NAME} on Cloud Run. The Streamable HTTP
# endpoint becomes https://${SERVICE_NAME}-<hash>.${REGION}.run.app/mcp, which
# the agent's MCP_PORTFOLIO_URL must point at. No extra env vars needed: Cloud
# Run injects PORT and the app binds 0.0.0.0.
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --min-instances 1 \
    --max-instances 1 \
    --timeout=900

# Register or update the MCP server in Agent Registry.
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format="value(status.url)")

if gcloud agent-registry services describe "$SERVICE_NAME" --project "$PROJECT_ID" --location "$REGION" >/dev/null 2>&1; then
    echo "Updating existing Agent Registry service..."
    gcloud agent-registry services update "$SERVICE_NAME" \
        --project "$PROJECT_ID" \
        --location "$REGION" \
        --display-name="ETrade Portfolio MCP" \
        --mcp-server-spec-type=tool-spec \
        --mcp-server-spec-content="$(cat "${PROJECT_ROOT}/toolspec.json")" \
        --interfaces=url="${SERVICE_URL}/mcp",protocolBinding=jsonrpc
else
    echo "Creating new Agent Registry service..."
    gcloud agent-registry services create "$SERVICE_NAME" \
        --project "$PROJECT_ID" \
        --location "$REGION" \
        --display-name="ETrade Portfolio MCP" \
        --mcp-server-spec-type=tool-spec \
        --mcp-server-spec-content="$(cat "${PROJECT_ROOT}/toolspec.json")" \
        --interfaces=url="${SERVICE_URL}/mcp",protocolBinding=jsonrpc
fi
