import numpy as np
import roboticstoolbox as rtb
import utils.calculation_functions as calc
import communication.protocol as protocol
from communication.protocol import RobotMode

class RobotModel:
    def __init__(self, step_size: float = 0.01):
        self.q_current = np.zeros(6) 
        self.qd_current = np.zeros(6)
        self.qdd_current = np.zeros(6)
        self.q_end = np.zeros(6)
        self.trajectory = None

        self.max_velocity = 0
        self.max_acceleration = 0

        self.phy_max_acceleration = 4*np.pi
        self.phy_max_velocity = np.pi

        self.state = RobotMode.ROBOT_MODE_IDLE
        self.step_size = step_size
        self.current_traj_index = 0
    
    def set_q_current(self, q_current: np.ndarray):
        self.q_current = q_current

    def get_q_current(self) -> np.ndarray:
        return self.q_current
    
    def get_qd_current(self) -> np.ndarray:
        return self.qd_current
    
    def get_qdd_current(self) -> np.ndarray:
        return self.qdd_current

    def step(self, current_time: float):

        if self.trajectory is None:
            return

        # RTB trajectory fields are usually q, qd, qdd
        traj_q = getattr(self.trajectory, "q", None)
        traj_qd = getattr(self.trajectory, "qd", None)
        traj_qdd = getattr(self.trajectory, "qdd", None)

        if traj_q is None or traj_qd is None or traj_qdd is None:
            print("Trajectory does not have expected fields.")
            return
        
        if self.current_traj_index < len(traj_q):
            self.q_current = traj_q[self.current_traj_index]
            self.qd_current = traj_qd[self.current_traj_index]
            self.qdd_current = traj_qdd[self.current_traj_index]
        
            self.current_traj_index += 1
        else:
            if self.state == RobotMode.ROBOT_MODE_RUNNING:
                print("Reached end of trajectory.")
            self.state = RobotMode.ROBOT_MODE_IDLE

    def load_program(self, q_end: np.ndarray, max_velocity: float, acceleration: float):
        self.q_end = q_end
        self.max_velocity = max_velocity
        self.max_acceleration = acceleration

    def play(self):
        self.set_move_traj()
        self.state = RobotMode.ROBOT_MODE_RUNNING

    def pause(self):
        self.set_halt_traj()

    def stop(self):
        self.set_halt_traj()
        self.clear_program()

    def clear_program(self):
        self.q_end = np.zeros(6)
        self.max_velocity = 0
        self.max_acceleration = 0
        self.trajectory = None

    def set_halt_traj(self):
        self.current_traj_index = 0
        q_end = calc.compute_stop_q_end(self.q_current, self.qd_current, self.phy_max_acceleration)
        self.trajectory = rtb.jtraj(self.q_current, q_end, calc.compute_steps(self.q_current, q_end, self.phy_max_velocity, self.phy_max_acceleration, self.step_size), qd0=self.qd_current)
    
    def set_move_traj(self):
        self.current_traj_index = 0
        self.trajectory = rtb.jtraj(self.q_current, self.q_end, calc.compute_steps(self.q_current, self.q_end, self.max_velocity, self.max_acceleration, self.step_size), qd0=self.qd_current)
    
    def get_current_tcp_pose(self):
        # For simplicity, we return a fixed TCP pose. In a real implementation, this would be computed based on the current joint angles.
        return np.eye(4)  # Identity matrix as a placeholder