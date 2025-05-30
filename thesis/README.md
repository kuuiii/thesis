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

You are all set, now run the following.

```bash
	. run.bash 
```
