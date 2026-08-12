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

# Deploy the MCP server as ${SERVICE_NAME} on Cloud Run. The MCP SSE URL
# becomes https://${SERVICE_NAME}-<hash>.${REGION}.run.app/sse, which the
# agent's MCP_PORTFOLIO_URL must point at. No extra env vars needed: Cloud
# Run injects PORT and the app binds 0.0.0.0.
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --min-instances 1 \
    --max-instances 1

# Register the MCP server in Agent Registry so it can be discovered by agents.
# The streamable HTTP endpoint is exposed at /mcp (FastMCP default mount path).
# Agent Registry validates toolspec.json against the MCP Tool schema; it must
# stay in sync with the tools declared in app.py.
# Use an absolute path so the script works from any working directory.
SERVICE_URL="https://${SERVICE_NAME}-${PROJECT_ID:0:6}.${REGION}.run.app"
gcloud agent-registry services create "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --location "$REGION" \
    --display-name="ETrade Portfolio MCP" \
    --mcp-server-spec-type=tool-spec \
    --mcp-server-spec-content=@"${PROJECT_ROOT}/toolspec.json" \
    --interfaces=url="${SERVICE_URL}/mcp",protocolBinding=jsonrpc
