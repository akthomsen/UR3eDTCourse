from communication.factory import RabbitMQFactory
from communication.rabbitmq import Rabbitmq
from communication.protocol import RobotArmStateKeys, ROUTING_KEY_STATE
from models.robotarmkinematics_model import RobotArmKinematicsModel
from communication.protocol import RobotArmStateKeys
from utils.constants import step_size, State
import roboticstoolbox as rtb
import numpy as np

class ControllerModel:
    """
    A simple implementation of an FMU in Python for co-simulation.
    This FMU represents a controller for the robot arm.
    """
    def __init__(self):
        # Set default values
        self.robot = rtb.models.UR3()
        self.q_end: list[float] = np.array([0, 0, 0, 0, 0, 0]) # Init q_end
        self.q_actual: list[float] = np.array([0, 0, 0, 0, 0, 0]) # Init q_actual
        self.max_velocity: float = 0.0
        self.acceleration: float = 0.0
        self.current_v: float = 0.0 # Current velocity
        self.tcp_pose = None # Current pose
        self.time_stamp: float = 0.0
        self.current_values: RobotArmStateKeys = RobotArmStateKeys() # Empty class
        self.state = State.IDLE

    def load_program(self, q_end: list[float], max_velocity: float, acceleration: float):
        # Store these values in the controller to keep track of them
        self.q_end = q_end
        self.max_velocity = max_velocity
        self.acceleration = acceleration


    def get_acceleration(self) -> float:
        return self.acceleration
    
    def get_max_velocity(self) -> float:
        return self.max_velocity
    
    def get_current_position(self) -> list[float]:
        return self.q_actual
    
    def get_current_velocity(self) -> float:
        return self.qd_actual
    
    def get_current_tcp_pose(self):
        return self.tcp_pose
    
    def get_time_stamp(self) -> float:
        return self.time_stamp
    
    def set_current_pos(self, q_actual: list[float]) -> None:
        self.q_actual = q_actual

    # Start the loaded program
    def play(self):
        self.state = State.RUNNING
        
    # Pause the running program
    def pause(self):
        self.state = State.IDLE
    
    # Stop the running program and clear the loaded program values
    def stop(self):
        self.state = State.IDLE
        self.end_p = np.array([0, 0, 0, 0, 0, 0]) # Clear the loaded program
        self.max_velocity = 0.0
        self.acceleration = 0.0
        self.robotarmkinematics_model.set_max_acceleration(0)
        self.robotarmkinematics_model.set_max_velocity(0)
        self.robotarmkinematics_model.set_end_pos(np.array([0, 0, 0, 0, 0, 0]))

    def do_step(self):
        # Check state and current values
        if self.state == State.IDLE:
            return
    
        if self.current_values == None:
            return
        
        # Calculate the current pose using the current joint radians
        self.tcp_pose = self.robot.fkine(self.q_actual)
