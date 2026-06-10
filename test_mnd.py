import numpy as np
from mnd_assimilation import MNDAssimilation, generate_synthetic_data
from collections import OrderedDict as OD

def test_mnd_recovery():
    print("Running MND Assimilation Recovery Test...")

    # 1. Ground Truth Parameters
    TRUE_PARAMS = OD((
        ('dt', 0.01),
        ('D', 0.25),
        ('si', 100), ('gamma', 1.0),
        ('ga', 0.3), ('gb', 3.0),
        ('va', 0.0001), ('vb', 0.009),
        ('mu0', 0.3), ('mua', 0.1), ('mub', 0.7),
        ('Ks', 10.0),
        ('Ka', 1.0),  ('Ia', 100.0),
        ('Kb', 0.1),  ('Ib', 1.0),
        ('y0', 0.0), ('a0', 0.0), ('b0', 0.0)
    ))

    # 2. Initial State
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]

    # 3. Generate Synthetic Data (Truth + Noise)
    measurements, true_trajectories = generate_synthetic_data(initial_state, TRUE_PARAMS, noise_level=0.02)
    print(f"Generated {len(measurements)} synthetic measurements with 2% noise.")

    # 4. Setup Assimilator
    # We want to recover y0, a0, b0 as they are often the most uncertain
    target_keys = ['y0', 'a0', 'b0']
    initial_guess = [0.1, 0.1, 0.1] # Offset from truth (0,0,0)

    # Baseline params for the assimilator (same as true, but with wrong y0, a0, b0)
    baseline_params = TRUE_PARAMS.copy()
    baseline_params['y0'] = 0.1
    baseline_params['a0'] = 0.1
    baseline_params['b0'] = 0.1

    assimilator = MNDAssimilation(baseline_params, measurements)

    # 5. Perform Assimilation
    result = assimilator.assimilate(initial_guess, target_keys, initial_state)

    print("\n--- Recovery Results ---")
    print(f"True Parameters: y0=0, a0=0, b0=0")
    print(f"Recovered Parameters: {result['params']}")
    print(f"Final Combined RMSE: {result['rmse']:.6f}")

    # 6. Validate Trajectories
    # Compare the recovered trajectory vs ground truth
    recovered_trajectories = result['trajectories']
    rmse_x = np.sqrt(np.mean((recovered_trajectories[:, 1] - true_trajectories[:, 1])**2))
    rmse_s = np.sqrt(np.mean((recovered_trajectories[:, 0] - true_trajectories[:, 0])**2))

    print(f"Trajectory RMSE X: {rmse_x:.6f}")
    print(f"Trajectory RMSE S: {rmse_s:.6f}")

    if rmse_x < 1.0 and rmse_s < 1.0:
        print("\nMND Recovery Test PASSED: Parameters recovered and trajectory matched.")
        return True
    else:
        print("\nMND Recovery Test FAILED: Too high error.")
        return False

if __name__ == "__main__":
    test_mnd_recovery()
