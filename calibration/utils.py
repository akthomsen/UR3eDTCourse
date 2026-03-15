import numpy as np
import json
import re
import os



def load_scenario_csv(filepath):
    timestamps = []
    q_actual_list = []
    q_target_val = None
    max_vel = None
    accel = None

    with open(filepath, "r") as f:
        f.readline()  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Extract all bracket-delimited arrays
            arrays = re.findall(r"\[([^\]]+)\]", line)
            # Replace arrays with a single-token placeholder
            cleaned = re.sub(r"\[[^\]]+\]", "ARRAY", line)
            parts = [p.strip() for p in cleaned.split(",")]

            # Scalar fields (everything that is not ARRAY)
            scalars = [p for p in parts if p != "ARRAY"]
            # scalars: [timestamp, robot_mode, ..., max_joint_speed, acceleration]
            timestamp = float(scalars[0])
            max_vel = float(scalars[-2])
            accel = float(scalars[-1])

            # Arrays: [0] = actual_joint_position, [1] = tcp_position, [2] = target
            actual_pos = [float(x) for x in arrays[0].split(",")]
            target_pos = [float(x) for x in arrays[2].split(",")]

            timestamps.append(timestamp)
            q_actual_list.append(actual_pos)
            if q_target_val is None:
                q_target_val = np.array(target_pos)

    timestamps = np.array(timestamps)
    timestamps -= timestamps[0]  # normalise to start at 0

    q_actual = np.array(q_actual_list)

    return {
        "timestamps": timestamps,
        "q_actual": q_actual,
        "q_target": q_target_val,
        "q0": q_actual[0].copy(),
        "max_velocity_deg": max_vel,
        "acceleration_deg": accel,
    }


def save_parameters(filepath, calibration_result):
    """Save calibrated vel_scale, acc_scale, and optionally t_delay to a JSON file."""
    data = {
        "vel_scale": calibration_result["vel_scale"],
        "acc_scale": calibration_result["acc_scale"],
        "t_delay": calibration_result.get("t_delay", 0.0),
    }
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def load_parameters(filepath):
    """Load vel_scale and acc_scale from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)
