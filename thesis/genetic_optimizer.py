# genetic_optimizer.py

import os
import shutil
import random
import csv
from batch_run_scenarios import batch_run
from scenario_utils import (
    generate_batch_from_params,
    crossover_batches,
    mutate_batch,
    read_collision_rate,
    round_scenario_hash
)

# === Configurations ===
POP_SIZE = 10
SCENARIOS_PER_BATCH = 10
GENERATIONS = 2
TEMPLATE = "/autoware_map/template.yaml"
BASE_DIR = "/autoware_map/genetic_batches"
INITIAL_CSV_PATH = "/mp_thesis/thesis/simulation_results/simulation_results.csv"
RESULTS_DIR = "/mp_thesis/thesis/simulation_results"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def load_collision_scenarios(csv_path):
    collisions = []
    try:
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("result_type", "").strip().lower() == "collision":
                    print("Collision found!.") # TEST, REMOVE AFTER!!
                    params = (
                        row["ego_start_lane"], float(row["ego_start_s"]),
                        row["npc_start_lane"], float(row["npc_start_s"]),
                        row["ego_dest_lane"], float(row["ego_dest_s"]),
                        row["npc_dest_lane"], float(row["npc_dest_s"])
                    )
                    collisions.append(params)
    except FileNotFoundError:
        print("⚠️ Collision CSV file not found.")
    return collisions

def evaluate_population(population, generation):
    fitness_scores = []

    for i, batch_path in enumerate(population):
        print(f"\n=== Evaluating {batch_path} ===")

        shutil.copytree(batch_path, "/autoware_map/generated_scenarios", dirs_exist_ok=True)

        result_csv = os.path.join(RESULTS_DIR, f"batch_gen{generation}_{i}_results.csv")
        batch_run(scenario_dir="/autoware_map/generated_scenarios", results_csv=result_csv) ## Base directory?

        fitness = read_collision_rate(result_csv)
        fitness_scores.append((batch_path, fitness))

    return sorted(fitness_scores, key=lambda x: x[1], reverse=True)

def evolve():
    seen_hashes = set()
    population = []
    population_params = []

    seed_params = load_collision_scenarios(INITIAL_CSV_PATH)
    if not seed_params:
        print("❌ No collision scenarios found. Please run initial simulation first.")
        return

    for i in range(POP_SIZE):
        batch_dir = os.path.join(BASE_DIR, f"batch_gen0_{i}")
        batch_params = random.choices(seed_params, k=SCENARIOS_PER_BATCH)
        generate_batch_from_params(TEMPLATE, batch_dir, batch_params)
        population.append(batch_dir)
        population_params.append(batch_params)

    for gen in range(1, GENERATIONS + 1):
        print(f"\n\n==== Generation {gen} ====")
        scored = evaluate_population(population, gen)

        top_batches = [scored[0][0], scored[1][0]]
        top_params = [population_params[population.index(top_batches[0])],
                      population_params[population.index(top_batches[1])]]

        new_population = []
        new_population_params = []

        for i in range(POP_SIZE):
            child_params = crossover_batches(top_params[0], top_params[1])
            child_params = mutate_batch(child_params, seen=seen_hashes)

            child_dir = os.path.join(BASE_DIR, f"batch_gen{gen}_{i}")
            generate_batch_from_params(TEMPLATE, child_dir, child_params)

            new_population.append(child_dir)
            new_population_params.append(child_params)

        population = new_population
        population_params = new_population_params

    print("\n✅ Genetic optimization complete.")

if __name__ == "__main__":
    evolve()
