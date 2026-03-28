FROM python:3.13-slim

# System deps for pyzbar (zbar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything
COPY . .

# Install dependencies directly (avoid editable install build isolation issues)
RUN pip install --no-cache-dir \
    "fastmcp>=3.0.0b1" \
    "requests>=2.31.0" \
    "requests-oauthlib>=1.3.0" \
    "pydantic>=2.5.0" \
    "python-dotenv>=1.0.0" \
    "keyring>=24.0.0" \
    "claude-agent-sdk>=0.1.51" \
    "aiogram>=3.26.0" \
    "openai>=1.0.0" \
    "pyzbar>=0.1.9" \
    "Pillow>=10.0.0"

# Create memory directory
RUN mkdir -p /app/memory

# Create non-root user (Claude CLI refuses bypassPermissions as root)
RUN useradd -m -s /bin/bash botuser && chown -R botuser:botuser /app
USER botuser

ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "run_bot.py"]
