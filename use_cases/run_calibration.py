
from calibration.utils import load_scenario_csv, save_parameters, load_parameters
from calibration.optimize import calibrate

if __name__ == "__main__":


    scenario_path = "data/from_0_to_90.csv"
    output_path = "models/parameters.json"

    scenario = load_scenario_csv(scenario_path)
    print(f"  samples : {len(scenario['timestamps'])}")
    print("\nRunning calibration...")
    result = calibrate(scenario)

    initial_vel_scale = None
    initial_acc_scale = None
    initial_t_delay = 0.0
    prev = load_parameters(output_path)
    if prev.get("t_delay") != 0.0:
        initial_vel_scale = prev.get("vel_scale")
        initial_acc_scale = prev.get("acc_scale")
        initial_t_delay = prev.get("t_delay", 0.0)
        print(f"  warm-starting from existing: {output_path}")
    else:
        print("  existing params have no t_delay, using physics-informed initial guess")

    result = calibrate(scenario,
        initial_vel_scale=initial_vel_scale,
        initial_acc_scale=initial_acc_scale,
        initial_t_delay=initial_t_delay,
    )





    status = "SUCCEEDED" if result["success"] else "FAILED"
    print(f"\nCalibration {status}:")
    print(f"  cost     : {result['cost']:.6e}")
    print(f"  nfev     : {result['nfev']}")
    print(f"\nSaving parameters to: {output_path}")
    save_parameters(output_path, result)


