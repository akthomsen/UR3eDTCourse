import models.robot_model as robot_model
import numpy as np

SIM_DURATION = 3.0  # seconds
STEP_SIZE = 0.001

model = robot_model.RobotModel(step_size=STEP_SIZE)

end_q = np.array([2, -0.5, 3.2, -3, -2, 1.5]) # Target joint positions in radians
model.load_program(end_q, max_velocity=np.pi, acceleration=np.pi)
model.play()

time_stamps = []
q_values = []
qd_values = []
qdd_values = []

for i in range(int(SIM_DURATION / STEP_SIZE)):
    current_time = i * model.step_size
    if current_time == 0.5:  # Example of pausing at step 100
        model.pause()
    if current_time == 2:  # Example of resuming at step 200
        model.play()
    model.step(current_time)
    #print(f"Step {i}: q_current = {model.get_q_current()}, dq_current = {model.get_dq_current()}, ddq_current = {model.get_ddq_current()}")
    # Store the results for analysis
    time_stamps.append(current_time)
    q_values.append(model.get_q_current().copy())
    qd_values.append(model.get_qd_current().copy())
    qdd_values.append(model.get_qdd_current().copy())

#plot the results
import matplotlib.pyplot as plt
time_stamps = np.array(time_stamps)
q_values = np.array(q_values)
qd_values = np.array(qd_values)
qdd_values = np.array(qdd_values)
plt.figure(figsize=(12, 8))
for i in range(6):
    plt.subplot(3, 2, i+1)
    plt.plot(time_stamps, q_values[:, i], label='q')
    plt.plot(time_stamps, qd_values[:, i], label='qd')
    plt.plot(time_stamps, qdd_values[:, i], label='qdd')
    plt.title(f'Joint {i+1}')
    plt.xlabel('Time (s)')
    plt.ylabel('Value')
    plt.legend()
plt.savefig('robot_model_test_results.png')