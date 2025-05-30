import os
import csv
from launch_scenario import run_simulation

DEFAULT_SCENARIO_DIR = "/autoware_map/generated_scenarios"
SCENARIO_EXT = ".yaml"
DEFAULT_RESULTS_CSV = "/ros2_ws/simulation_results/simulation_results.csv"


def batch_run(scenario_dir=DEFAULT_SCENARIO_DIR, results_csv=DEFAULT_RESULTS_CSV):
    # Gather all scenario files, sorted numerically by index
    scenarios = sorted(
        [os.path.join(scenario_dir, f) for f in os.listdir(scenario_dir) if f.endswith(SCENARIO_EXT)],
        key=lambda path: int(os.path.splitext(os.path.basename(path))[0].split('_')[1])
    )

    print(f"🚗 Running {len(scenarios)} scenarios from {scenario_dir}\n")

    for i, scenario_path in enumerate(scenarios):
        print(f"[{i+1}/{len(scenarios)}] ▶ Running {os.path.basename(scenario_path)}")
        run_simulation(scenario_path, csv_path=results_csv)

    failed = count_collisions(results_csv)

    print(f"\n--- Summary ---")
    print(f"Total Scenarios Run: {len(scenarios)}")
    print(f"Collisions: {failed} ({(failed/len(scenarios))*100:.1f}%)")


def count_collisions(csv_path):
    count = 0
    try:
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("result_type", "").strip().lower() == "collision":
                    count += 1
    except FileNotFoundError:
        print("⚠️ CSV results file not found.")
    return count


if __name__ == "__main__":
    batch_run()
