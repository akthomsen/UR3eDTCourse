import numpy as np
"""
class RobotData:
    def __init__(self, q_actual: np.ndarray, qd_actual: np.ndarray, time_stamp: np.ndarray, tcp_pose):
        self.q_actual = q_actual
        self.qd_actual = qd_actual
        self.time_stamp = time_stamp
        self.tcp_pose = tcp_pose
"""

class RobotData:
    def __init__(self):

        self.q_actual: list[np.ndarray] = [] # List of joint positions for each time step
        self.qd_actual: list[np.ndarray] = [] # List of joint velocities for each time step
        self.time_stamps: list[float] = [] # List of time stamps
        self.tcp_pose: list = []

    def add_q_actual(self, q: np.ndarray):
        self.q_actual.append(q)

    def add_qd_actual(self, qd: np.ndarray):
        self.qd_actual.append(qd)

    def add_time_stamp(self, t: float):
        self.time_stamps.append(t)

    def add_tcp_pose(self, pose):
        self.tcp_pose.append(pose)

    def reset(self) -> None:
        self.q_actual = []
        self.qd_actual = []
        self.time_stamp = []
        self.tcp_pose = []

    def get_q_actual(self):
        return self.q_actual
    
    def get_qd_actual(self):
        return self.qd_actual
    
    def get_time_stamps(self):
        return self.time_stamps
    
    def get_tcp_pose(self):
        return self.tcp_pose
