#!/bin/bash
set -e

echo "[Feature Store] ETL: application features"
python scripts/build_application_features.py

echo "[Feature Store] ETL: bureau features"
python scripts/build_bureau_features.py

echo "[Feature Store] Feast apply"
cd feast_repo
feast apply

echo "[Feature Store] Feast materialize"
feast materialize-incremental $(date +%Y-%m-%d)

echo "[Feature Store] Ready"