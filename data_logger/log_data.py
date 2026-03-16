"""This module provides functions for decoding and saving the received data,
                        used by the on_message_received callback in subscriber.py."""

import os
from typing import Dict, Any, List

class Logger:
    """A class responsible"""

    def __init__(self, scenario_name : str):

        self.scenario_name = scenario_name
        self.robot_mode_history = []
        self.actual_joint_position_history = []
        self.tcp_position_history = []
        self.timestamp_history = []
        self.target_joint_position : float = 0.0
        self.max_joint_speed : float = 0.0
        self.joint_acceleration : float = 0.0

        self.scenario_status : str = "not_started"


    def handle_received_step(self, data):
        """Decode the received data and save it to a file."""
        try:
            # Info
            robot_mode : str = data['robot_mode']
            actual_joint_position : List[float] = data['q_actual']
            tcp_position : List[float] = data['tcp_pose']
            timestamp : float = data['timestamp']

            # Config (Constrains + target position)
            self.target_joint_position : List[float] = data['q_target']
            self.max_joint_speed : float = data['joint_max_speed']
            self.joint_acceleration : float = data['joint_max_acceleration']

            self.robot_mode_history.append(robot_mode)
            self.actual_joint_position_history.append(actual_joint_position)
            self.tcp_position_history.append(tcp_position)
            self.timestamp_history.append(timestamp)

        except Exception as e:
            print(f"✗ Failed to decode and save data: {e}")




    def is_scenario_finished(self):
        if len(self.robot_mode_history) > 2:
            was_moving = any(m.lower() != "idle" for m in self.robot_mode_history)
            if was_moving and self.robot_mode_history[-1].lower() == "idle":
                self.scenario_status = "finished"


    def get_step_data(self) -> Dict[str, Any]:
        """Get the current data as a dictionary."""
        return {
            "robot_mode": self.robot_mode_history[-1] if self.robot_mode_history else None,
            "actual_joint_position": self.actual_joint_position_history[-1] if self.actual_joint_position_history else None,
            "tcp_position": self.tcp_position_history[-1] if self.tcp_position_history else None,
            "timestamp": self.timestamp_history[-1] if self.timestamp_history else None,
            "target_joint_position": self.target_joint_position,
            "max_joint_speed": self.max_joint_speed,
            "joint_acceleration": self.joint_acceleration
        }

    def save_data_to_file(self, filename: str, path: str):

        """Save the collected data to a file."""
        try:
            os.makedirs(path, exist_ok=True)
            file_path = os.path.join(path, filename)

            with open(file_path, 'w') as f:
                f.write("timestamp,robot_mode,actual_joint_position,\
                        tcp_position,target_joint_position,\
                        max_joint_speed,joint_acceleration\n")

                for i in range(len(self.timestamp_history)):
                    row = [
                        str(self.timestamp_history[i]),
                        str(self.robot_mode_history[i]),
                        str(self.actual_joint_position_history[i]),
                        str(self.tcp_position_history[i]),
                        str(self.target_joint_position),
                        str(self.max_joint_speed),
                        str(self.joint_acceleration),
                    ]
                    f.write(",".join(row) + "\n")

            print(f"✓ Data saved successfully to {file_path}")

        except Exception as e:
            print(f"✗ Failed to save data to file: {e}")
