#!/usr/bin/env bash
# Punto de entrada único del proceso batch diario:
# 1. corre dbt (staging + marts + tests) contra data/ecommerce.duckdb
# 2. genera report.html con las respuestas a las 4 preguntas de negocio
set -euo pipefail

cd "$(dirname "$0")"

dbt build --project-dir dbt_project --profiles-dir dbt_project

python report/build_report.py
