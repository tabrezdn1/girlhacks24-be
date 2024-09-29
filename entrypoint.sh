#!/bin/bash
set -e

# Run database migrations


# Start the application
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
