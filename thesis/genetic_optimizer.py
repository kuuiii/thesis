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
from pathlib import Path

# === Configurations ===
POP_SIZE = 10
SCENARIOS_PER_BATCH = 20
GENERATIONS = 8
TEMPLATE = "/autoware_map/template.yaml"

# Directories for scenario batches and results
GENERATED_BASE   = Path("/autoware_map/generated_scenarios")
RESULTS_BASE     = Path("/ros2_ws/simulation_results")
INITIAL_CSV_PATH = RESULTS_BASE / "simulation_results.csv"

# ensure directories exist
GENERATED_BASE.mkdir(parents=True, exist_ok=True)
RESULTS_BASE.mkdir(parents=True, exist_ok=True)

def load_collision_scenarios(csv_path):
    """
    Read initial collision scenarios from CSV to seed the GA.
    Returns a list of parameter tuples.
    """
    collisions = []
    try:
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("result_type", "").strip().lower() == "collision":
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
    """
    Evaluate each batch by copying into a unique workdir and running simulations.
    Returns a sorted list of (batch_path, fitness_score).
    """
    fitness_scores = []
    for idx, batch_path in enumerate(population):
        batch_path = Path(batch_path)
        batch_info = f"gen{generation}_batch{idx}"

        # prepare a fresh workdir for this batch
        workdir = GENERATED_BASE / batch_info
        if workdir.exists():
            shutil.rmtree(workdir)
        shutil.copytree(batch_path, workdir)

        # prepare results CSV
        result_csv = RESULTS_BASE / f"{batch_info}_results.csv"
        result_csv.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n=== Evaluating {batch_path} as {workdir} ===")

        # run and score
        batch_run(
            scenario_dir=str(workdir),
            results_csv=str(result_csv)
        )
        fitness = read_collision_rate(str(result_csv))
        fitness_scores.append((batch_path, fitness))

    # sort descending by fitness
    return sorted(fitness_scores, key=lambda x: x[1], reverse=True)

def evolve():
    """
    Main genetic optimization loop.
    """
    seen_hashes = set()
    population = []
    population_params = []

    # seed from initial collisions
    seed_params = load_collision_scenarios(str(INITIAL_CSV_PATH))
    if not seed_params:
        print("❌ No collision scenarios found. Please run initial simulation first.")
        return

    # --- generation 0: sample initial population ---
    for i in range(POP_SIZE):
        batch_dir = GENERATED_BASE / f"gen0_batch{i}"
        # clear old dir
        if batch_dir.exists():
            shutil.rmtree(batch_dir)

        # sample unique parameters if possible
        if len(seed_params) >= SCENARIOS_PER_BATCH:
            batch_params = random.sample(seed_params, k=SCENARIOS_PER_BATCH)
        else:
            batch_params = random.choices(seed_params, k=SCENARIOS_PER_BATCH)

        # generate scenario files
        generate_batch_from_params(TEMPLATE, str(batch_dir), batch_params)

        # record population and params
        population.append(batch_dir)
        population_params.append(batch_params)

        # track seen hashes to avoid re-generating identical
        for params in batch_params:
            seen_hashes.add(round_scenario_hash(params))

    # --- subsequent generations ---
    for gen in range(1, GENERATIONS + 1):
        print(f"\n\n==== Generation {gen} ====")
        scored = evaluate_population(population, gen)

        # select top 2 batches
        top_batches = [scored[0][0], scored[1][0]]
        top_params = [
            population_params[population.index(top_batches[0])],
            population_params[population.index(top_batches[1])]
        ]

        new_population = []
        new_population_params = []

        # create next-gen population
        for i in range(POP_SIZE):
            # Crossover step: combine top parents
            child_params = crossover_batches(top_params[0], top_params[1])

            # If every offspring tuple has been seen before, force a 100% mutation for full novelty
            if all(round_scenario_hash(t) in seen_hashes for t in child_params):
                child_params = mutate_batch(
                    child_params,
                    seen=seen_hashes,
                    mutation_rate=1.0  # mutate every scenario to guarantee change
                )

            # Standard mutation pass
            child_params = mutate_batch(child_params, seen=seen_hashes)

            # write out scenarios
            child_dir = GENERATED_BASE / f"gen{gen}_batch{i}"
            if child_dir.exists():
                shutil.rmtree(child_dir)
            generate_batch_from_params(TEMPLATE, str(child_dir), child_params)

            new_population.append(child_dir)
            new_population_params.append(child_params)

            # update seen hashes
            for params in child_params:
                seen_hash_s = round_scenario_hash(params)
                seen_hashes.add(seen_hash_s)

        population = new_population
        population_params = new_population_params

    print("\n✅ Genetic optimization complete.")

if __name__ == "__main__":
    evolve()
