# Traffic Scenario Mining for Safety Validation of Autonomous Vehicle

This repository provides an open-source framework for mining critical traffic scenarios for the purpose of validating autonomous vehicle behavior in simulation environments.

The framework integrates scenario generation, execution, and crash data collection, utilizing Tier IV Scenario Simulator V2, Autoware, and Python. The primary audience is researchers and developers interested in autonomous vehicle safety validation using simulation tools.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation & Usage](#installation--usage)
- [Project Structure](#project-structure)
- [Acknowledgements](#acknowledgements)

## Overview

Autonomous vehicles must be validated in a wide range of traffic scenarios, including rare and high-risk events. This project aims to automate the mining and execution of such scenarios, supporting researchers in identifying and analyzing critical behaviors in simulation.

## Features

- **Scenario Generation:** Automated discovery of challenging and high-risk scenarios.
- **Integrated Simulation:** Uses Tier IV Scenario Simulator V2 and Autoware for realistic testing.
- **Crash Data Collection:** Gathers results and logs for further analysis.
- **Open-source:** Designed for research and educational use.

## Requirements

- **Programming Languages:** Python, Shell
- **Tools:**
  - Docker (with Autoware Universe and ROS2)
  - Tier IV Scenario Simulator V2
  - Tier IV Scenario Editor

## Installation & Usage

> **Note:** Some instructions refer to hardware or directories specific to a university environment. Adapt paths and settings as appropriate for your system.

### 1. Clone the project

```bash
git clone https://github.com/kuuiii/thesis.git
```

### 2. Run the Docker container

```bash
docker run -it --rm --privileged --env=DISPLAY --env=QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /home/autolab/mp_thesis/thesis:/ros2_ws \
  -v /home/autolab/autoware_map:/autoware_map \
  --workdir /ros2_ws mohsen_aw:full bash
```

### 3. Install dependencies inside the Docker container

```bash
sudo apt update
sudo apt install -y vim
pip3 install setuptools==58.2.0
echo "source /opt/ros/humble/setup.bash" >> ~/setup.bash
echo "source /autoware/install/setup.bash" >> ~/setup.bash
echo "source /home/iseauto/ros2_ws/install/setup.bash" >> ~/setup.bash
source ~/setup.bash
pip install ruamel.yaml
```

### 4. Source the environment

```bash
. setup.bash
```

### 5. Prepare simulation maps

Copy the `template.yaml` file into the `/autoware_map/` directory:

```bash
cp template.yaml /autoware_map/
```

### 6. Run the experiment

```bash
. run.bash
```

## Project Structure

```
thesis/
├── src/                    # Source code and scenario scripts
├── run.bash                # Script to launch the experiment
├── setup.bash              # Environment setup script
├── template.yaml           # Map template for scenarios
└── README.md
```

## Acknowledgements

- [Tier IV Scenario Simulator V2](https://github.com/tier4/scenario_simulator_v2)
- [Autoware](https://github.com/autowarefoundation/autoware)

---

*For questions, issues, or contributions, please open an issue or pull request on this repository.*
