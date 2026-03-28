FROM python:3.13-slim

# System deps for pyzbar (zbar) and Claude CLI (node runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

# Copy project files
COPY . .

# Install the project itself
RUN pip install --no-cache-dir -e .

# Create memory directory
RUN mkdir -p /app/memory

# Run the bot
CMD ["python", "run_bot.py"]
