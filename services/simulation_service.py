from communication.rabbitmq import Rabbitmq, ROUTING_KEY_STATE
from communication.protocol import *
from communication.rabbitmq import *
from communication.factory import RabbitMQFactory
from models.robotarmkinematics_model import RobotArmKinematicsModel
from models.controller_model import ControllerModel
from communication.protocol import RobotArmStateKeys
from utils.calculation_functions import compute_steps
import numpy as np
from utils.constants import step_size
from utils.data_class import RobotData

class SimulationService:
    def __init__(self, should_publish_to_rabbitmq: bool = True):
        self.robotarmkinematics_model = RobotArmKinematicsModel()
        self.controller_model = ControllerModel()
        self.fault_after_n_steps: int = -1
        self.pause_after_n_steps: int = -1
        self.stop_after_n_steps: int = -1
        self.step_counter: int = 0
        self.n_steps: int = 0
        self.fault_type: int = "None"
        self.robot_data = RobotData()
        self.should_publish_to_rabbitmq: bool = should_publish_to_rabbitmq
        
        if self.should_publish_to_rabbitmq:
            self.rabbitmq_factory = RabbitMQFactory()
            self.rabbitmq: Rabbitmq = self.rabbitmq_factory.create_rabbitmq()
            self.rabbitmq.connect_to_server() # Method already contains try catch clause
        
    def set_start_pos(self, q_start: list[float]) -> None:
        self.robotarmkinematics_model.set_start_position(q_start)

    # Set a fault to happen after n steps
    def set_fault(self, n_steps: int, fault_type: str) -> None:
        self.fault_after_n_steps = n_steps
        self.fault_type = fault_type

    def publish_to_rabbitmq(self):
            # Convert values to json serializable types
            self.q_actual = self.current_values.Q_ACTUAL.tolist()
            self.qd_actual = self.current_values.QD_ACTUAL.tolist()
            self.time_stamp = self.step_counter*step_size
            
            msg = {
            RobotArmStateKeys.ROBOT_MODE: self.state, # Current mode e.g. RUNNING, IDLE
            RobotArmStateKeys.Q_ACTUAL: self.q_actual, # Current joint positions (radians)
            RobotArmStateKeys.QD_ACTUAL: self.qd_actual, # Current joint velocities (radians/second)
            RobotArmStateKeys.Q_TARGET: self.current_values.Q_TARGET, # Target position (radians)
            RobotArmStateKeys.TIMESTAMP: self.time_stamp, # Time stamp of the status message
            RobotArmStateKeys.JOINT_MAX_SPEED: self.current_values.JOINT_MAX_SPEED, # Joint max speed (degrees/second)
            RobotArmStateKeys.JOINT_MAX_ACCELERATION: self.current_values.JOINT_MAX_ACCELERATION, # Joint max acceleration (degrees/second^2)
            RobotArmStateKeys.TCP_POSE: self.tcp_pose.A.tolist() # TCP Pose calculation result
            }
    
        
            self.rabbitmq.send_message(ROUTING_KEY_STATE, msg)

    def load_program(self, q_end: list[float], max_velocity: float, acceleration: float) -> None:
        # Reset robot data values
        self.robot_data.reset()

        # Set the values in the controller
        self.controller_model.load_program(q_end, max_velocity, acceleration)

        # Set the values in the robot arm model
        self.robotarmkinematics_model.set_end_position(q_end)
        self.robotarmkinematics_model.set_max_velocity(max_velocity)
        self.robotarmkinematics_model.set_max_acceleration(acceleration)

        # Get the current positions of the robot arm model
        q_start: list[float] = self.robotarmkinematics_model.get_current_position()

        # Calculate the amount of steps necessary 
        n_steps = compute_steps(q_start, q_end, max_velocity, acceleration, step_size)
        self.n_steps: int = n_steps

        # Calculate the trajectory inside of the robot arm
        self.robotarmkinematics_model.do_calculations(n_steps)

    def reset_results(self):
        self.robot_data.reset()

    def get_results(self) -> RobotData:
        return self.robot_data
    
    # Start the loaded program
    def play(self) -> None:
        self.controller_model.play() # Immitate calling play on the controller
        
        while self.step_counter < self.n_steps:

            if self.pause_after_n_steps == self.step_counter:
                self.controller_model.pause()

            # Get the current position of the robot arm and give to the controller
            q_actual: list[float] = self.robotarmkinematics_model.get_current_position()
            self.controller_model.set_current_pos(q_actual)
            
            # Step the controller
            self.controller_model.do_step()

            # Add relevant values to the robot data instance in this class
            # The RobotData instance can be fetched when a simulation is done
            self.robot_data.add_q_actual(self.robotarmkinematics_model.get_current_position())
            self.robot_data.add_qd_actual(self.robotarmkinematics_model.get_current_velocity())
            self.robot_data.add_time_stamp(self.step_counter * step_size)
            self.robot_data.add_tcp_pose(self.controller_model.get_current_tcp_pose())

            # Step the robot arm model
            self.robotarmkinematics_model.do_step(self.step_counter) # step counter needed for fetching trajectory results

            # Publish to rabbitmq if enabled
            if self.should_publish_to_rabbitmq:
                 self.publish_to_rabbitmq()

            # Increment step counter
            self.step_counter += 1
           

    # Pause the running program after n steps
    def set_pause(self, n_steps: int) -> None:
        self.pause_after_n_steps = n_steps

    # Stop running program and clear program
    def set_stop(self):
        pass

