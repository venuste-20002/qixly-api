# Base image for building dependencies
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy dependency files (only pyproject.toml, as poetry.lock might not exist)
COPY pyproject.toml /app/

# Install poetry
RUN pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only=main

# Final stage for the runtime image
FROM python:3.12-slim as runtime

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nano \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

# Set permissions and entry point
RUN chmod +x ./start.sh
CMD ./start.sh
