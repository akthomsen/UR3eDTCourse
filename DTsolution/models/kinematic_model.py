import roboticstoolbox as rtb
import numpy as np

class KinematicModel:
    def __init__(self, movement_fidelity : int = 50):
        self.time = 0.0 # All time measured in seconds
        self.current_joint_angles = [0] * 6
        self.movement_fidelity = movement_fidelity

        # Inputs
        self.commanded_joint_angles = [0] * 6

        # Movement variables
        self.current_movement_start_angles = [0] * 6
        self.current_movement_start_time = 0.0 # s
        self.current_movement_duration = 0.0 # s
        self.moving = False

        # Experiment variables
        self.start_time = 0.0
        self.stop_time = 0.0

        #? This seems unnecessary since movment is not dependent on robot arm construction???
        # Setup provided kinematic model
        # link1 = rtb.RevoluteDH(d=0.15185, a=0.0, alpha=np.pi/2)
        # link2 = rtb.RevoluteDH(d=0.0, a=-0.24355, alpha=0.0)
        # link3 = rtb.RevoluteDH(d=0.0, a=-0.2132, alpha=0.0)
        # link4 = rtb.RevoluteDH(d=0.13105, a=0.0, alpha=np.pi/2)
        # link5 = rtb.RevoluteDH(d=0.08535, a=0.0, alpha=-np.pi/2)
        # link6 = rtb.RevoluteDH(d=0.0921, a=0.0, alpha=0.0)
        # Create the robot object
        # self.robot = rtb.DHRobot([link1, link2, link3, link4, link5, link6], name="robot")

    def _determine_movement_duration(self, start_angles: list, end_angles: list) -> float:
        # Calculate angle difference
        max_angle_diff = np.max(np.abs(np.array(start_angles) - np.array(end_angles)))
        
        # TODO: Is the model good enough? The fact that it does not go through (0, 0) raises suspision, maybe also try and collect data at very very small movements
        # Refer to train_movement_time_model.ipynb to see where the numbers are from
        return 0.95984308 * max_angle_diff + 0.76497454

    def fmi2SetCommandedJointAngles(self, angles: list):
        # Setup variables for move to be made
        self.commanded_joint_angles = angles
        self.current_movement_start_angles = self.current_joint_angles
        self.current_movement_duration = self._determine_movement_duration(self.current_joint_angles, self.commanded_joint_angles)

    def fmi2StartMovement(self):
        self.moving = True
        self.current_movement_start_time = self.time


    def fmi2SetupExperiment(self, start_time: float, stop_time: float):
        self.start_time = start_time
        self.stop_time = stop_time

    def fmi2Instantiate(self):
        self.time = 0.0
        self.current_joint_angles = [0] * 6
        self.commanded_joint_angles = [0] * 6

    def fmi2DoStep(self, current_time: float, step_size: float): 
        self.time = current_time + step_size

        if self.moving:
            if self.time > self.current_movement_start_time + self.current_movement_duration:
                self.current_joint_angles = self.commanded_joint_angles
            else:
                # Determine how many seconds of movement is done
                traj_index = int((self.time - self.current_movement_start_time) / self.current_movement_duration * self.movement_fidelity) # index of trajectory
                traj = rtb.jtraj(np.array(self.current_movement_start_angles), np.array(self.commanded_joint_angles), self.movement_fidelity) # Determine trajectory of movement
                self.current_joint_angles = traj.q[traj_index, :].tolist()
                self.moving = False

    def fmi2Terminate(self):
        ...
    
