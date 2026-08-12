FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

# Run as non-root for Cloud Run / production best practice
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080
CMD ["python", "-m", "app"]
