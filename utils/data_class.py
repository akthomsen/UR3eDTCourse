"""
class RobotData:
    def __init__(self, q_actual: list[float], qd_actual: list[float], time_stamp: list[float], tcp_pose):
        self.q_actual = q_actual
        self.qd_actual = qd_actual
        self.time_stamp = time_stamp
        self.tcp_pose = tcp_pose
"""

class RobotData:
    def __init__(self, q_actual: list[float], qd_actual: list[float], time_stamps: list[float], tcp_pose):
        self.q_actual: list[list[float]] = q_actual # List of list of float since we have 6 joint positions for each time step
        self.qd_actual: list[list[float]] = qd_actual
        self.time_stamps: list[float] = time_stamps
        self.tcp_pose = tcp_pose

    def add_q_actual(self, q: list[float]):
        self.q_actual.append(q)

    def add_qd_actual(self, qd: list[float]):
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
