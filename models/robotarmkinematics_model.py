import math
import numpy as np
import roboticstoolbox as rtb
from roboticstoolbox.tools.trajectory import Trajectory
from spatialmath import SE3
from spatialmath.base import tr2rpy
from utils.calculation_functions import compute_steps
from communication.protocol import RobotArmStateKeys
from utils.constants import step_size, pi

class RobotArmKinematicsModel:
    def __init__(self):
        self.q_start: list[float] = np.array([0.0, -pi/2, pi/2, -pi/2, -pi/2, 0.0]) # Init q_start from exercise class. Upright with joints tucked a bit
        self.q_end: list[float] = np.array([0, 0, 0, 0, 0, 0]) # Init q_end
        self.q_actual: list[float] = np.array([0.0, -pi/2, pi/2, -pi/2, -pi/2, 0.0]) # Init q_start from exercise class. Upright with joints tucked a bit
        self.max_velocity: float = 0.0
        self.acceleration: float = 0.0
        self.current_v: list[float] = np.array([0, 0, 0, 0, 0, 0]) # Current velocity deg/s
        self.current_a: list[float] = np.array([0, 0, 0, 0, 0, 0]) # Current acceleration deg/s^2
        self.trajectory: Trajectory = None
    
    def set_start_position(self, q_start: list[float]):
        self.q_start = q_start
    
    def set_end_position(self, q_end: list[float]) -> None:
        self.q_end = q_end
    
    # Max velocity is given in deg/s. One value given for all joints
    def set_max_velocity(self, max_velocity: float) -> None:
        self.max_velocity = max_velocity
    
    # Acceleration is given in deg/s^2. One value is given for all joints
    def set_max_acceleration(self, acceleration: float) -> None:
        self.acceleration = acceleration
    
    def get_start_position(self) -> list[float]:
        return self.q_start
    
    def get_current_position(self) -> list[float]:
        return self.q_actual
    
    def get_current_velocity(self) -> list[float]:
        return self.current_v
    
    def get_current_acceleration(self) -> list[float]:
        return self.current_a

    def do_calculations(self, n_steps: int):
        self.trajectory = rtb.jtraj(self.q_start, self.q_end, n_steps) # Calculate the trajectory and set the field variable

    def get_state(self) -> str:
        return self.state
    
    # Simulate a time step and update class variables so they can be fetched using get_current_values()
    def do_step(self, step_counter: int) -> None:
        # Check if trajectory exists
        if self.trajectory == None:
            return
        
        self.q_actual = self.trajectory.s[step_counter] # Get the position values with respect to the time
        self.current_v = self.trajectory.sd[step_counter] # Get the current joint velocities
        self.current_a = self.trajectory.sdd[step_counter]
