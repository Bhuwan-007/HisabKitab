#!/usr/bin/env bash
cd "$(dirname "$0")/../backend"
python -m app.seed.generator
