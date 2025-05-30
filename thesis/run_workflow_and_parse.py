import os
import subprocess
import xml.etree.ElementTree as ET
import csv
import re

WORKFLOW_PATH = "/autoware_map/generated_scenarios/workflow.yaml"
LOG_DIR = "/autoware_map/workflow_logs"
CSV_OUTPUT = "simulation_results.csv"

def run_workflow():
    print("🚀 Running workflow batch...")
    command = [
        "ros2", "launch", "scenario_test_runner", "scenario_test_runner.launch.py",
        f"workflow:={WORKFLOW_PATH}",
        f"log_directory:={LOG_DIR}"
    ]
    try:
        subprocess.run(command, check=True)
        print("✅ Batch execution finished.")
    except subprocess.CalledProcessError as e:
        print("❌ Workflow execution failed.")
        print(e)

def parse_results_and_write_csv():
    rows = []
    for root_dir, _, files in os.walk(LOG_DIR):
        for file in files:
            if file == "result.junit.xml":
                full_path = os.path.join(root_dir, file)
                result = parse_result_xml(full_path)
                scenario_yaml = extract_scenario_path_from_log_dir(root_dir)
                rows.append([
                    scenario_yaml,
                    result.get("collision"),
                    result.get("collided_with"),
                    result.get("message"),
                    result.get("result_type")
                ])

    if rows:
        with open(CSV_OUTPUT, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["scenario_yaml", "collision", "collided_with", "failure_message", "result_type"])
            writer.writerows(rows)
        print(f"[✓] Parsed {len(rows)} results to {CSV_OUTPUT}")
    else:
        print("⚠️ No results found to parse.")

def extract_scenario_path_from_log_dir(log_subdir):
    # Infer scenario name from log folder name (if named accordingly)
    base_name = os.path.basename(log_subdir)
    return f"/autoware_map/generated_scenarios/{base_name}.yaml"

def parse_result_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        failures = int(root.attrib.get("failures", 0))
        failure_msg = ""
        collision_entity = None

        for testcase in root.iter("testcase"):
            failure = testcase.find("failure")
            if failure is not None:
                failure_msg = failure.attrib.get("message", "")
                match = re.search(r"colliding with another given entity (\w+)", failure_msg)
                if match:
                    collision_entity = match.group(1)

        result_type = "success"
        if failures > 0:
            if "colliding with another given entity" in failure_msg:
                result_type = "collision"
            elif "simulation time greater than" in failure_msg:
                result_type = "timeout"
            elif "standstill" in failure_msg:
                result_type = "standstill"
            else:
                result_type = "unknown_failure"

        return {
            "collision": result_type == "collision",
            "message": failure_msg,
            "collided_with": collision_entity,
            "result_type": result_type
        }

    except Exception as e:
        print(f"❌ Failed to parse {xml_path}: {e}")
        return {
            "collision": None,
            "message": "parse_error",
            "collided_with": None,
            "result_type": "parse_error"
        }

if __name__ == "__main__":
    run_workflow()
    parse_results_and_write_csv()
