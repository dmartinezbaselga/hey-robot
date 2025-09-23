cmake_minimum_required(VERSION 3.0.2)
project(hey_robot)

## Find catkin and any catkin packages
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  mpc_planner_msgs
)

## Declare a catkin package
catkin_package(
  CATKIN_DEPENDS rospy std_msgs mpc_planner_msgs
)

## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
  ${catkin_INCLUDE_DIRS}
)

## Mark executable scripts (Python)
catkin_install_python(PROGRAMS hey_robot_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
