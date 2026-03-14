from services.simulation_service import UR3eService
import numpy as np
from startup.start_docker_rabbitmq import start_rabbitmq
from communication.protocol import ROUTING_KEY_STATE
from utils.data_class import RobotData
import matplotlib.pyplot as plt
from utils.constants import step_size

pi = np.pi
# Maybe use later
# ur3e_service.set_fault(15, "stuck_joint") # Example fault injection after 15 steps


q_start = [0.0, -pi/2, pi/2, -pi/2, -pi/2, 0.0] # From exercise class. Upright with joints tucked a bit
q_end = [0.0, -pi/2, pi/2, -pi/2, -pi/1, 0.0] # Move 5th joint a bit

ur3e_service = UR3eService()
ur3e_service.set_start_pos(q_start)

max_velocity = 60 # deg/s
acceleration = 80 # deg/s²

ur3e_service.load_program(q_end, max_velocity, acceleration)
ur3e_service.play()

robot_data: RobotData = ur3e_service.get_results()

time_stamps = robot_data.get_time_stamps()

velocities = robot_data.get_qd_actual()

positions = robot_data.get_q_actual()

plt.plot(time_stamps, velocities, label="Velocities") # Plotted as lines
plt.plot(time_stamps, positions, ".", label="Positions") # Plotted as dots
plt.title("Robot joint velocity over time")
plt.xlabel("Time")
plt.ylabel("Value")
plt.legend() # Show the labels
plt.show()
