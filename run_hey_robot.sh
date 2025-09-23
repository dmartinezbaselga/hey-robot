#!/usr/bin/bash 
path="/workspace/src"
if [ $# -eq 0 ]; then
    cd ${path}/LLM-Navigation && poetry run python hey_robot_node.py
else
    cd ${path}/LLM-Navigation && poetry run python hey_robot_node.py "$1"
fi