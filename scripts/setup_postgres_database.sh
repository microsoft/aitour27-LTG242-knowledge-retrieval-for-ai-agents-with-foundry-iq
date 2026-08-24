#!/bin/sh
set -eu

uv run --locked python scripts/setup_postgres_database.py
