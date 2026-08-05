FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8080
CMD ["python", "-m", "akapal_mcp_portfolio.app"]
