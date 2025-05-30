from ruamel.yaml import YAML
from datetime import datetime
import random
import os

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

# === Lane Definitions (s value bounds per laneId) ===
START_LANE_IDS = {
    "34408": (0, 24.0),
    "34600": (0, 52.5),
    "34576": (0, 27.0),
    "34981": (0, 8.4),   # Short lane!
    "34976": (0, 36.0)
}

DEST_LANE_IDS = {
    "34630": (0, 27.0),
    "34579": (0, 52.5),
    "34564": (0, 24.5),
    "34621": (0, 49.5)
}

EGO_LENGTH = 4.77
NPC_LENGTH = 4.0

def positions_overlap(s1, l1, s2, l2, buffer=1.0):
    rear1, front1 = s1, s1 + l1
    rear2, front2 = s2, s2 + l2
    return not (front1 + buffer < rear2 or front2 + buffer < rear1)

def sample_non_overlapping_positions():
    ego_lane = random.choice(list(START_LANE_IDS.keys()))
    npc_lane_choices = [l for l in START_LANE_IDS if l != ego_lane]
    npc_lane = random.choice(npc_lane_choices)

    ego_s_range = START_LANE_IDS[ego_lane]
    npc_s_range = START_LANE_IDS[npc_lane]

    # Aim to spawn near the higher end of the lane (closer to intersection)
    ego_base = ego_s_range[1] - 5.0
    npc_base = npc_s_range[1] - 5.0

    ego_s = round(random.uniform(max(ego_base, ego_s_range[0]), ego_s_range[1]), 2)
    npc_s = round(random.uniform(max(npc_base, npc_s_range[0]), npc_s_range[1]), 2)

    return ego_lane, ego_s, npc_lane, npc_s


def generate_scenario(template_path, output_dir, scenario_index):
    with open(template_path, 'r') as f:
        data = yaml.load(f)

    now_iso = datetime.utcnow().isoformat(timespec="milliseconds") + 'Z'
    header = data["OpenSCENARIO"]["FileHeader"]
    header["date"] = now_iso
    header["description"] = f"Mined scenario for AV safety validation - scenario {scenario_index}"
    header["author"] = 'Markus Puudersell'

    ego_start_lane, ego_start_s, npc_start_lane, npc_start_s = sample_non_overlapping_positions()
    ego_dest_lane = random.choice(list(DEST_LANE_IDS.keys()))
    ego_dest_s = round(random.uniform(*DEST_LANE_IDS[ego_dest_lane]), 2)
    npc_dest_lane = random.choice(list(DEST_LANE_IDS.keys()))
    npc_dest_s = round(random.uniform(*DEST_LANE_IDS[npc_dest_lane]), 2)

    try:
        for private_action in data["OpenSCENARIO"]["Storyboard"]["Init"]["Actions"]["Private"]:
            entity = private_action.get("entityRef", "")
            actions = private_action.get("PrivateAction", [])

            if entity == "ego":
                teleport_pos = actions[0]["TeleportAction"]["Position"]["LanePosition"]
                teleport_pos["laneId"] = ego_start_lane
                teleport_pos["s"] = ego_start_s

                routing_pos = actions[1]["RoutingAction"]["AcquirePositionAction"]["Position"]["LanePosition"]
                routing_pos["laneId"] = ego_dest_lane
                routing_pos["s"] = ego_dest_s

            elif entity == "Npc1":
                teleport_pos = actions[0]["TeleportAction"]["Position"]["LanePosition"]
                teleport_pos["laneId"] = npc_start_lane
                teleport_pos["s"] = npc_start_s

                routing_pos = actions[1]["RoutingAction"]["AcquirePositionAction"]["Position"]["LanePosition"]
                routing_pos["laneId"] = npc_dest_lane
                routing_pos["s"] = npc_dest_s

    except Exception as e:
        print(f"[ERROR] modifying scenario: {e}")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"scenario_{scenario_index}.yaml")
    with open(output_path, 'w') as f:
        yaml.dump(data, f)

    print(f"[✓] scenario_{scenario_index}.yaml generated:")
    print(f"    Ego     → start laneId: {ego_start_lane}, s: {ego_start_s}")
    print(f"              dest  laneId: {ego_dest_lane}, s: {ego_dest_s}")
    print(f"    NPC1    → start laneId: {npc_start_lane}, s: {npc_start_s}")
    print(f"              dest  laneId: {npc_dest_lane}, s: {npc_dest_s}")

def generate_batch(template_path, output_dir, count=5):
    for i in range(count):
        generate_scenario(template_path, output_dir, i)

if __name__ == "__main__":
    template_path = "/autoware_map/template.yaml"
    output_dir = "/autoware_map/generated_scenarios"
    generate_batch(template_path, output_dir, count=10)
