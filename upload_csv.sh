#!/usr/bin/env bash
set -euo pipefail

mc alias set local http://localhost:9000 minioadmin minioadmin123

mc mb local/ml-data || true
mc mb local/ml-data/raw || true
mc mb local/ml-data/processed || true

mc cp data/application_train.csv local/ml-data/raw/
mc cp data/application_test.csv  local/ml-data/raw/
mc cp data/bureau.csv            local/ml-data/raw/