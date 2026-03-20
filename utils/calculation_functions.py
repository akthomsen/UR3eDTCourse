import numpy as np
from spatialmath import SE3
import json
from communication.protocol import RobotArmStateKeys

def compute_time(q_start, q_end, v_max_deg, a_max_deg, dt):
    """
    Positions: radians
    Velocity: deg/s
    Acceleration: deg/s^2
    """

    q_start = np.array(q_start)
    q_end   = np.array(q_end)

    # Convert velocity and acceleration to radians
    v_max = np.deg2rad(v_max_deg)
    a_max = np.deg2rad(a_max_deg)

    T_all = []

    for i in range(len(q_start)):
        delta_q = abs(q_end[i] - q_start[i])  # already radians

        t_acc = v_max / a_max
        q_acc = dt * a_max * t_acc**2
        q_acc_total = 2 * q_acc

        if delta_q > q_acc_total:
            # Trapezoidal profile
            q_const = delta_q - q_acc_total
            t_const = q_const / v_max
            T_i = 2 * t_acc + t_const
        else:
            # Triangular profile
            T_i = 2 * np.sqrt(delta_q / a_max)

        T_all.append(T_i)

    T_total = max(T_all)

    return T_total

def compute_steps(q_start: np.ndarray, q_end: np.ndarray, v_max: float, a_max: float, dt: float):
    """
    Positions: radians
    Velocity: deg/s
    Acceleration: deg/s^2
    """

    T_all = []

    for i in range(len(q_start)):
        delta_q = abs(q_end[i] - q_start[i])

        t_acc = v_max / a_max
        q_acc = 0.5 * a_max * t_acc**2
        q_acc_total = 2 * q_acc

        if delta_q > q_acc_total:
            # Trapezoidal profile
            q_const = delta_q - q_acc_total
            t_const = q_const / v_max
            T_i = 2 * t_acc + t_const
        else:
            # Triangular profile
            T_i = 2 * np.sqrt(delta_q / a_max)

        T_all.append(T_i)

    T_total = max(T_all)
    n_steps = int(np.ceil(T_total / dt))

    return n_steps


def compute_stop_q_end(q_start, v_current, a_max):
    stop_dist = 0.5 * (v_current ** 2) / a_max
    q_end = q_start + stop_dist * np.sign(v_current)

    return q_end