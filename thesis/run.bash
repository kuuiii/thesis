#!/bin/bash

mkdir -p /mp_thesis/thesis/simulation_results
mkdir -p /mp_thesis/thesis/mined_scenarios

echo "📁 Generating initial random scenarios..."
python3 scenario_generator.py

echo "🚗 Running initial scenarios..."
python3 -c "
from batch_run_scenarios import batch_run
batch_run(
    scenario_dir='/autoware_map/generated_scenarios',
    results_csv='/mp_thesis/thesis/simulation_results/simulation_results.csv'
)
"

echo "🧬 Starting genetic optimization..."
python3 genetic_optimizer.py

echo "✅ Full pipeline complete."
