FROM --platform=linux/arm64 python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTORCH_ENABLE_MPS_FALLBACK=1 \
    PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    procps \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-450.0.0-linux-arm.tar.gz > /tmp/google-cloud-sdk.tar.gz && \
    mkdir -p /usr/local/gcloud && \
    tar -C /usr/local/gcloud -xzf /tmp/google-cloud-sdk.tar.gz && \
    /usr/local/gcloud/google-cloud-sdk/install.sh --quiet && \
    rm /tmp/google-cloud-sdk.tar.gz

ENV PATH="/usr/local/gcloud/google-cloud-sdk/bin:${PATH}"

FROM base as production

WORKDIR /app

RUN groupadd --gid 1000 discovery && \
    useradd --uid 1000 --gid discovery --shell /bin/bash --create-home discovery

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=discovery:discovery . .

RUN mkdir -p /app/logs /app/output /app/.cache /app/checkpoints && \
    chown -R discovery:discovery /app

USER discovery

RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

if [[ "$1" == "--dry-run" || "$DRY_RUN" == "true" ]]; then
    echo "Running in dry-run mode with M1 optimization"
    exec python main.py --dry-run "${@:2}"
fi

if [[ "$1" == "--resume" || "$RESUME" == "true" ]]; then
    echo "Resuming from checkpoint with M1 optimization"
    exec python main.py --resume "${@:2}"
fi

echo "Starting AO1 discovery with M1 optimization"
exec python main.py "$@"
EOF

RUN chmod +x /app/entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "
import sys
import os
from pathlib import Path

if Path('/app/discovery_running.lock').exists():
    print('Discovery running')
    sys.exit(0)

if Path('/app/ao1_visibility_cmdb.db').exists():
    print('Discovery completed')
    sys.exit(0)

if Path('/app/logs').exists():
    error_files = list(Path('/app/logs').glob('*error*'))
    if error_files:
        print('Errors detected')
        sys.exit(1)

print('Status unknown')
sys.exit(1)
"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]

LABEL maintainer="Development Team" \
      version="1.0.0" \
      description="AO1 Discovery System with M1 GPU Support" \
      architecture="arm64"

FROM production as development

USER root

RUN pip install --no-cache-dir \
    pytest pytest-asyncio pytest-cov \
    black flake8 mypy \
    ipython jupyter \
    memory-profiler

RUN apt-get update && apt-get install -y \
    htop \
    vim \
    strace \
    && rm -rf /var/lib/apt/lists/*

USER discovery

ENTRYPOINT ["/bin/bash"]