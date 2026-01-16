#!/bin/bash
set -e

echo "===== Start FastAPI ====="
uvicorn app:app --host 0.0.0.0 --port 8080