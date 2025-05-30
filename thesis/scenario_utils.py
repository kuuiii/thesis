# scenario_utils.py

import os
import random
import shutil
from ruamel.yaml import YAML
import hashlib

# === Lane Definitions (same as in scenario_generator.py) ===
START_LANE_IDS = {
    "34408": (0, 24.0),
    "34600": (0, 52.5),
    "34576": (0, 27.0),
    "34981": (0, 8.4),
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

yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

def positions_overlap(s1, l1, s2, l2, buffer=1.0):
    rear1, front1 = s1, s1 + l1
    rear2, front2 = s2, s2 + l2
    return not (front1 + buffer < rear2 or front2 + buffer < rear1)

def generate_batch_from_params(template_path, output_dir, batch_params):
    os.makedirs(output_dir, exist_ok=True)
    for i, params in enumerate(batch_params):
        with open(template_path, 'r') as f:
            data = yaml.load(f)

        ego_lane, ego_s, npc_lane, npc_s, ego_dest_lane, ego_dest_s, npc_dest_lane, npc_dest_s = params

        try:
            for private_action in data["OpenSCENARIO"]["Storyboard"]["Init"]["Actions"]["Private"]:
                entity = private_action.get("entityRef", "")
                actions = private_action.get("PrivateAction", [])

                if entity == "ego":
                    teleport_pos = actions[0]["TeleportAction"]["Position"]["LanePosition"]
                    teleport_pos["laneId"] = ego_lane
                    teleport_pos["s"] = ego_s

                    routing_pos = actions[1]["RoutingAction"]["AcquirePositionAction"]["Position"]["LanePosition"]
                    routing_pos["laneId"] = ego_dest_lane
                    routing_pos["s"] = ego_dest_s

                elif entity == "Npc1":
                    teleport_pos = actions[0]["TeleportAction"]["Position"]["LanePosition"]
                    teleport_pos["laneId"] = npc_lane
                    teleport_pos["s"] = npc_s

                    routing_pos = actions[1]["RoutingAction"]["AcquirePositionAction"]["Position"]["LanePosition"]
                    routing_pos["laneId"] = npc_dest_lane
                    routing_pos["s"] = npc_dest_s

        except Exception as e:
            print(f"[ERROR] generating scenario: {e}")

        out_path = os.path.join(output_dir, f"scenario_{i}.yaml")
        with open(out_path, 'w') as f:
            yaml.dump(data, f)

def crossover_batches(parent_batch_a, parent_batch_b, crossover_rate=0.5):
    child_batch = []
    for i in range(len(parent_batch_a)):
        scenario_a = parent_batch_a[i]
        scenario_b = parent_batch_b[i % len(parent_batch_b)]
        child_scenario = []
        for j in range(len(scenario_a)):
            val = scenario_a[j] if random.random() < crossover_rate else scenario_b[j]
            child_scenario.append(val)
        child_batch.append(tuple(child_scenario))
    return child_batch

def mutate_batch(batch, mutation_rate=0.3, seen=None):
    mutated_batch = []
    for params in batch:
        attempts = 0
        while attempts < 10:
            mutated = list(params)

            if random.random() < mutation_rate:
                mutated[0] = random.choice(list(START_LANE_IDS.keys()))
                mutated[1] = round(random.uniform(START_LANE_IDS[mutated[0]][1] - 5.0, START_LANE_IDS[mutated[0]][1]), 2)
            if random.random() < mutation_rate:
                mutated[2] = random.choice([l for l in START_LANE_IDS if l != mutated[0]])
                mutated[3] = round(random.uniform(START_LANE_IDS[mutated[2]][1] - 5.0, START_LANE_IDS[mutated[2]][1]), 2)
            if random.random() < mutation_rate:
                mutated[4] = random.choice(list(DEST_LANE_IDS.keys()))
                mutated[5] = round(random.uniform(*DEST_LANE_IDS[mutated[4]]), 2)
            if random.random() < mutation_rate:
                mutated[6] = random.choice(list(DEST_LANE_IDS.keys()))
                mutated[7] = round(random.uniform(*DEST_LANE_IDS[mutated[6]]), 2)

            if not positions_overlap(mutated[1], EGO_LENGTH, mutated[3], NPC_LENGTH):
                hash_val = round_scenario_hash(tuple(mutated))
                if seen is None or hash_val not in seen:
                    if seen is not None:
                        seen.add(hash_val)
                    mutated_batch.append(tuple(mutated))
                    break

            attempts += 1

        else:
            mutated_batch.append(params)

    return mutated_batch

def round_scenario_hash(params):
    key = "-".join([str(round(float(p), 1)) if isinstance(p, float) else str(p) for p in params])
    return hashlib.sha256(key.encode()).hexdigest()

def read_collision_rate(csv_path):
    import csv
    total = 0
    collisions = 0
    try:
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                total += 1
                if row.get("result_type", "").lower() == "collision":
                    collisions += 1
    except FileNotFoundError:
        return 0.0
    return collisions / total if total > 0 else 0.0
