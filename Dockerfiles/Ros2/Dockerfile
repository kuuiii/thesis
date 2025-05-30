# Base image: ROS 2 Humble (or your desired ROS 2 distribution)
FROM osrf/ros:humble-desktop

# Install TurtleBot 3 packages and tools
RUN apt-get update && apt-get install -y \
    ros-humble-gazebo-* \
    ros-humble-cartographer \
    ros-humble-cartographer-ros \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-msgs \
    python3-colcon-common-extensions \
    build-essential \
    git \
    vim && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
# ENV TURTLEBOT3_MODEL=burger

# Add a non-root user for students
RUN useradd -ms /bin/bash markus
USER markus
WORKDIR /home/markus

# Source ROS 2 setup scripts in the bash environment
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo 'export ROS_DOMAIN_ID=30 #TURTLEBOT3' >> ~/.bashrc
RUN echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc

# Default command
CMD ["bash"]