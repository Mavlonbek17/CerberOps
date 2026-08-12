# ── CerberOps Backend ──────────────────────────────────────────
# Multi-stage build: slim runtime with security scanners

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for scanners and building
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    wget \
    unzip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Nuclei
ARG NUCLEI_VERSION=3.3.7
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_${ARCH}.zip" \
    -O /tmp/nuclei.zip && \
    unzip /tmp/nuclei.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip

# Install Subfinder (subdomain enumeration)
ARG SUBFINDER_VERSION=2.6.6
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q "https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_${ARCH}.zip" \
    -O /tmp/subfinder.zip && \
    unzip /tmp/subfinder.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/subfinder && \
    rm /tmp/subfinder.zip

# Install httpx (ProjectDiscovery CLI tool for tech fingerprinting —
# NOT the Python httpx pip library used elsewhere in this codebase)
ARG HTTPX_VERSION=1.6.9
RUN ARCH=$(dpkg --print-architecture) && \
    wget -q "https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VERSION}/httpx_${HTTPX_VERSION}_linux_${ARCH}.zip" \
    -O /tmp/httpx.zip && \
    unzip /tmp/httpx.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/httpx && \
    rm /tmp/httpx.zip

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ ./app/
COPY cli/ ./cli/
COPY pyproject.toml .

# Non-root user
RUN useradd -r -s /bin/false cerberops && \
    mkdir -p /app/scan_outputs && \
    chown -R cerberops:cerberops /app
USER cerberops

EXPOSE 8000

# Default: run the API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
