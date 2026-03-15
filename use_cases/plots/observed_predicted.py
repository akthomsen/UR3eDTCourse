import numpy as np
from models.model import MotionModel
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

from calibration.utils import load_scenario_csv, load_parameters

def plot_calibration_results(scenario, vel_scale, acc_scale, sim_dt=0.002):
    """Plot observed vs. model-predicted joint positions.
    Args:
        scenario: dict with keys q0, q_target, max_velocity_deg, acceleration_deg,
                  timestamps, q_actual
        vel_scale: list of 6 velocity scaling factors
        acc_scale: list of 6 acceleration scaling factors
        sim_dt: simulation timestep (s)

    """

    model = MotionModel()
    t_obs = scenario["timestamps"]
    q_obs = scenario["q_actual"]

    t_model, q_model, _, _ = model.simulate_joint_motion(
        q0=scenario["q0"],
        q_target=scenario["q_target"],
        max_velocity_deg=scenario["max_velocity_deg"],
        acceleration_deg=scenario["acceleration_deg"],
        dt=sim_dt,
        t_end=t_obs[-1] + sim_dt,
        vel_scale=vel_scale,
        acc_scale=acc_scale,
    )

    n_joints = q_obs.shape[1]
    fig, axes = plt.subplots(n_joints, 1, figsize=(10, 2.5 * n_joints),
                             sharex=True)

    for j in range(n_joints):
        axes[j].plot(t_obs, np.rad2deg(q_obs[:, j]),
                     "o", markersize=3, label="Observed (PT)")
        axes[j].plot(t_model, np.rad2deg(q_model[:, j]),
                     "-", linewidth=1, label="Model")
        axes[j].set_ylabel(f"Joint {j + 1} (deg)")
        axes[j].legend(loc="best", fontsize=8)
        axes[j].grid(True)

    axes[-1].set_xlabel("Time (s)")
    fig.suptitle("Calibration: Model vs Observed", fontsize=14)
    plt.tight_layout()
    plt.show()
    return fig

def plot_model_vs_observed(scenario, vel_scale, acc_scale,
                           joint_idx=0, sim_dt=0.002):
    """Plot real observed PT data, model prediction, and tracking error for
    one joint.

    Args:
        scenario:   dict from load_scenario_csv
        vel_scale:  list of 6 velocity scaling factors
        acc_scale:  list of 6 acceleration scaling factors
        joint_idx:  joint to show (0-based, default 0)
        sim_dt:     simulation timestep (s)

    Returns:
        fig
    """

    model = MotionModel()
    t_obs = scenario["timestamps"]
    q_obs = scenario["q_actual"]

    t_model, q_model, _, _ = model.simulate_joint_motion(
        q0=scenario["q0"],
        q_target=scenario["q_target"],
        max_velocity_deg=scenario["max_velocity_deg"],
        acceleration_deg=scenario["acceleration_deg"],
        dt=sim_dt,
        t_end=t_obs[-1] + sim_dt,
        vel_scale=vel_scale,
        acc_scale=acc_scale,
    )

    # Interpolate model onto observed timestamps for pointwise error
    f_interp = interp1d(t_model, q_model[:, joint_idx], kind="linear",
                        fill_value="extrapolate")
    q_model_at_obs = f_interp(t_obs)
    err = np.rad2deg(q_model_at_obs - q_obs[:, joint_idx])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t_obs, np.rad2deg(q_obs[:, joint_idx]),
            "o", markersize=4, label="Observed (PT)")
    ax.plot(t_model, np.rad2deg(q_model[:, joint_idx]),
            "-", linewidth=1.5, label="Model prediction")
    ax.plot(t_obs, err, ":", linewidth=1.5, label="Tracking error (deg)")
    ax.axhline(0, color="k", linewidth=0.6, linestyle="--", alpha=0.4)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Degrees")
    ax.set_title(f"Model vs Observed — Joint {joint_idx + 1}")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()

    peak = np.max(np.abs(err))
    print(f"Peak tracking error (deg): {peak:.2f}")
    return fig



def main():
    scenario = load_scenario_csv("./data/from_0_to_90.csv")
    parameters = load_parameters("./models/parameters.json")

    plot_model_vs_observed(
        scenario, parameters["vel_scale"], parameters["acc_scale"]
    )

if __name__ == "__main__":
    main()
