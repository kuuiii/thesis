# Bachelor's Thesis Project

This repository contains my bachelor's thesis project.

## Run Locally

Clone the project

```bash
	git clone https://github.com/kuuiii/thesis.git
```

Run the Docker container

```bash
	docker run -it --rm --privileged --env=DISPLAY --env=QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix -v /home/autolab/mp_thesis/thesis:/ros2_ws -v /home/autolab/autoware_map:/autoware_map --workdir /ros2_ws mohsen_aw:full bash
```

Run the following commands inside the Docker terminal to install requirements.

```bash
	sudo apt update
	sudo apt install -y vim
	pip3 install setuptools==58.2.0
	echo "source /opt/ros/humble/setup.bash" >> ~/setup.bash
	echo "source /autoware/install/setup.bash" >> ~/setup.bash
	echo "source /home/iseauto/ros2_ws/install/setup.bash" >> ~/setup.bash source ~/setup.bash
	pip install ruamel.yaml
```

Then run the following command

```bash
	. setup.bash 
```

Include template.yaml to /autoware_map/ directory.

```bash
	template.yaml -> /autoware_map/
```

You are all set, now run the following.

```bash
	. run.bash 
```

## Mutating parameters

**Genetic Algorithm Parameters (in** `scenario_utils.py`**)**

These control mutation behavior for evolving scenarios:

```py
mutation_rate = 0.30         # 30% of scenarios mutate each generation
max_delta = 10.0             # max shift in meters (±10 m)
min_delta = 1.0              # min shift to prevent trivial changes
lane_mutation_rate = 0.20    # 20% chance to switch lane IDs
```
- `mutation_rate`: Controls how many scenarios change per generation to explore new failure points.
- `max_delta`: Larger jumps help escape local optima and find diverse scenarios.
- `min_delta`: Prevents tiny ineffective tweaks that clog evolution.
- `lane_mutation_rate`: Introduces topological variety by occasionally swapping lane IDs.

**Examples:**
|                |mutation rate                      |max delta                       |min delta                        |lane mutation rate                        |
|----------------|-------------------------------|-----------------------------|-----------------------------|-----------------------------|
|Balanced Exploration		|0.30			|10.0				|1.0 		          |0.20			          |
|Aggression Exploration		|0.50			|15.0				|2.0 		          |0.30			          |
|Lane-Focused Exploration	|0.20			|7.0				|1.0 		          |0.50			          |












