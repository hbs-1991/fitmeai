FROM python:3.13-slim

# System deps for pyzbar (zbar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install build tools first
RUN pip install --no-cache-dir setuptools wheel

# Copy and install dependencies
COPY pyproject.toml ./
COPY src/ ./src/
COPY main.py main_noauth.py ./

# Install the project
RUN pip install --no-cache-dir ".[dev]"

# Copy remaining files
COPY . .

# Create memory directory
RUN mkdir -p /app/memory

CMD ["python", "run_bot.py"]
