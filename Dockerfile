FROM python:3.12-bookworm as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /myapp

# Update system and install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies in /.venv without activating
RUN python3 -m venv /.venv \
    && /.venv/bin/pip install --upgrade pip setuptools wheel \
    && /.venv/bin/pip install -r requirements.txt

# Define a second stage for the runtime, using the same Debian Bookworm slim image
FROM python:3.12-slim-bookworm as final

# Upgrade libc-bin in the final stage to ensure security patch is applied
RUN apt-get update && apt-get install -y --no-install-recommends \
    libc-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the base stage
COPY --from=base /.venv /.venv

# Set environment variable to ensure all python commands run inside the virtual environment
ENV PATH="/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Set the working directory
WORKDIR /myapp

# Create and switch to a non-root user
RUN useradd -m myuser
USER myuser

# Copy application code with appropriate ownership
COPY --chown=myuser:myuser . .

# Inform Docker that the container listens on the specified port at runtime.
EXPOSE 8000

# Make the entrypoint script executable
RUN chmod +x /myapp/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/myapp/entrypoint.sh"]
