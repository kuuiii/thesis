import subprocess
import os
import xml.etree.ElementTree as ET
import csv
from pathlib import Path
import re
import shutil
from datetime import datetime

# launch_scenario.py (near top, after imports)
MINED_BASE = Path("/ros2_ws/mined_scenarios")

def run_simulation(scenario_path, output_dir="/autoware_map", log_output=True, csv_path="simulation_results.csv"):
    command = [
        "ros2", "launch", "scenario_test_runner", "scenario_test_runner.launch.py",
        f"record:=false",
        f"scenario:={scenario_path}",
        f"sensor_model:=sample_sensor_kit",
        f"vehicle_model:=sample_vehicle",
        f"output_directory:={output_dir}",
        f"launch_rviz:=false"
    ]

    print(f"Running simulation with scenario: {scenario_path}")
    try:
        with open("simulation_log.txt", "w") as logfile:
            subprocess.run(command, check=True, stdout=logfile, stderr=subprocess.STDOUT)
        print("Simulation finished.")
    except subprocess.CalledProcessError as e:
        print("Simulation failed to run.")
        print(e)

    xosc_path = parse_simulation_log("simulation_log.txt")
    result_xml_path = os.path.join(output_dir, "scenario_test_runner", "result.junit.xml")
    result = parse_result_xml(result_xml_path)

    # --- collision handling, per-batch mined folder ---
    if result["collision"]:
        # derive the batch_info string from your results CSV name
        batch_info = Path(csv_path).stem
        if batch_info.endswith("_results"):
            batch_info = batch_info[:-len("_results")]

        # make sure the per-batch mined dir exists
        mined_dir = MINED_BASE / batch_info
        mined_dir.mkdir(parents=True, exist_ok=True)

        # copy the .yaml into it with a timestamp
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = mined_dir / f"collision_{ts}.yaml"
        shutil.copy(scenario_path, dest)
        print(f"[💥] Collision detected! Saved to {dest}")

    # Extract lane and distance info
    params = extract_scenario_parameters(scenario_path)
    log_result_to_csv(csv_path, scenario_path, result, params)

def parse_simulation_log(log_path):
    xosc_path = None
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if "derived :" in line:
                    parts = line.strip().split("derived :")
                    if len(parts) > 1:
                        xosc_path = parts[1].strip()
                        break
    except Exception as e:
        print(f"Error reading simulation log: {e}")
    return xosc_path

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
        print(f"Error parsing XML result file: {e}")
        return {
            "collision": None,
            "message": "Error reading result file",
            "collided_with": None,
            "result_type": "parse_error"
        }

def extract_scenario_parameters(scenario_path):
    from ruamel.yaml import YAML
    yaml = YAML()
    with open(scenario_path, 'r') as f:
        data = yaml.load(f)

    ego_start = ego_dest = npc_start = npc_dest = (None, None)

    for private in data["OpenSCENARIO"]["Storyboard"]["Init"]["Actions"]["Private"]:
        entity = private["entityRef"]
        actions = private["PrivateAction"]

        start = actions[0]["TeleportAction"]["Position"]["LanePosition"]
        dest = actions[1]["RoutingAction"]["AcquirePositionAction"]["Position"]["LanePosition"]

        if entity == "ego":
            ego_start = (start["laneId"], start["s"])
            ego_dest = (dest["laneId"], dest["s"])
        elif entity == "Npc1":
            npc_start = (start["laneId"], start["s"])
            npc_dest = (dest["laneId"], dest["s"])

    return {
        "ego_start_lane": ego_start[0],
        "ego_start_s": ego_start[1],
        "ego_dest_lane": ego_dest[0],
        "ego_dest_s": ego_dest[1],
        "npc_start_lane": npc_start[0],
        "npc_start_s": npc_start[1],
        "npc_dest_lane": npc_dest[0],
        "npc_dest_s": npc_dest[1]
    }

def log_result_to_csv(csv_path, scenario_yaml, result, params):
    p = Path(csv_path)
    # Ensure the parent directory exists (even if it's just ".")
    p.parent.mkdir(parents=True, exist_ok=True)

    # Check existence before opening
    first_time = not p.exists()
    # Open in append mode (creates file if missing)
    with p.open(mode="a", newline="") as f:
        writer = csv.writer(f)
        if first_time:
            writer.writerow([
                "scenario_yaml", "collision", "result_type", "collided_with", "failure_message",
                "ego_start_lane", "ego_start_s", "ego_dest_lane", "ego_dest_s",
                "npc_start_lane", "npc_start_s", "npc_dest_lane", "npc_dest_s"
            ])
        writer.writerow([
            scenario_yaml,
            result["collision"],
            result["result_type"],
            result["collided_with"],
            result["message"],
            params["ego_start_lane"],
            params["ego_start_s"],
            params["ego_dest_lane"],
            params["ego_dest_s"],
            params["npc_start_lane"],
            params["npc_start_s"],
            params["npc_dest_lane"],
            params["npc_dest_s"]
        ])