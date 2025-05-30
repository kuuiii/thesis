import os
import random
import shutil
from ruamel.yaml import YAML
import hashlib
import csv
from pathlib import Path

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

def mutate_batch(params, seen: set,
                 mutation_rate: float = 0.30,       # mutate 30% of scenarios
                 max_delta: float = 10.0,           # ±10 m shifts
                 min_delta: float = 1.0,            # at least 2 m change
                 lane_mutation_rate: float = 0.20   # 20% chance to swap lanes
                 ) -> list: 
    """
    Mutate each scenario parameter with a given probability, ensuring any float mutation
    differs by at least min_delta, optionally mutate lane IDs, clamp to valid lane ranges,
    and prevent Ego/NPC overlap on the same lane. Also enforce within-batch uniqueness.
    """
    new_params = []
    for param_tuple in params:
        h0 = round_scenario_hash(param_tuple)
        # Force mutation if already seen, or randomly based on mutation_rate
        if h0 in seen or random.random() < mutation_rate:
            attempts = 0
            while True:
                mutated = []
                # Step 1: Mutate each element in the tuple
                for idx, val in enumerate(param_tuple):
                    if isinstance(val, float):
                        # Float mutation with min_delta enforcement
                        delta = random.uniform(-max_delta, max_delta)
                        if abs(delta) < min_delta:
                            delta = min_delta if delta >= 0 else -min_delta
                        mutated_val = val + delta

                        # Clamp to valid range depending on lane
                        if idx == 1:    # ego_start_s
                            max_s = START_LANE_IDS[str(param_tuple[0])][1]
                        elif idx == 3:  # npc_start_s
                            max_s = START_LANE_IDS[str(param_tuple[2])][1]
                        elif idx == 5:  # ego_dest_s
                            max_s = DEST_LANE_IDS[str(param_tuple[4])][1]
                        elif idx == 7:  # npc_dest_s
                            max_s = DEST_LANE_IDS[str(param_tuple[6])][1]
                        else:
                            max_s = None

                        if max_s is not None:
                            mutated_val = max(0.0, min(mutated_val, max_s))
                        # Round to one decimal to avoid overly precise floats
                        mutated_val = round(mutated_val, 1)

                        mutated.append(mutated_val)
                    else:
                        # Lane ID mutation with lane_mutation_rate
                        if idx in (0, 2) and random.random() < lane_mutation_rate:
                            mutated.append(random.choice(list(START_LANE_IDS.keys())))
                        elif idx in (4, 6) and random.random() < lane_mutation_rate:
                            mutated.append(random.choice(list(DEST_LANE_IDS.keys())))
                        else:
                            mutated.append(val)

                mutated_tuple = tuple(mutated)
                h = round_scenario_hash(mutated_tuple)
                attempts += 1

                # Step 2: Check for global uniqueness
                if h in seen:
                    if attempts > 10:
                        # Give up after 10 tries, keep original
                        new_params.append(param_tuple)
                        break
                    else:
                        continue

                # Step 3: Prevent overlap if Ego and NPC share the same lane
                ego_lane, ego_s, npc_lane, npc_s = mutated_tuple[0], mutated_tuple[1], mutated_tuple[2], mutated_tuple[3]
                if ego_lane == npc_lane and positions_overlap(ego_s, EGO_LENGTH, npc_s, NPC_LENGTH):
                    # They overlap on same lane → reject and retry
                    if attempts > 10:
                        new_params.append(param_tuple)
                        break
                    else:
                        continue

                # If we reach here, it's a valid new mutation
                seen.add(h)
                new_params.append(mutated_tuple)
                break

        else:
            # No mutation needed; keep the original
            new_params.append(param_tuple)

    # Enforce within-batch uniqueness and refill if needed
    unique = []
    local_hashes = set()
    for p in new_params:
        h = round_scenario_hash(p)
        if h not in local_hashes:
            unique.append(p)
            local_hashes.add(h)

    idx = 0
    while len(unique) < len(params):
        candidate = params[idx % len(params)]
        h = round_scenario_hash(candidate)
        if h not in local_hashes:
            unique.append(candidate)
            local_hashes.add(h)
        idx += 1

    return unique

def round_scenario_hash(params):
    key = "-".join(
        str(round(p, 1)) if isinstance(p, float) else str(p)
        for p in params
    )
    return hashlib.sha256(key.encode()).hexdigest()

def read_collision_rate(csv_path):
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