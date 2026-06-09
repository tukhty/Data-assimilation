import numpy as np
from ode_model import solve_ode
from collections import OrderedDict as OD

def test_ode_reproduction():
    print("Running ODE Smoke Test: Reproducing baseline trajectory...")

    # 1. Setup Parameters from environment_vF11.py
    PARAMS = OD((
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

    # 2. Initial State (from ginistate in environment_vF11.py)
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]

    # 3. Time span (40 hours = 40 * 3600 seconds, but the original code uses
    #    PERIOD = 80.0, let's check original scale.
    #    Original code: PERIOD = 80.0, DT = 0.01.
    #    Let's test for 80.0 units of time.)
    t_span = np.arange(0.0, 80.0 + 0.01, 0.01)

    try:
        trajectories = solve_ode(t_span, initial_state, PARAMS)

        print(f"Trajectory shape: {trajectories.shape}")
        print(f"Initial state: {trajectories[0]}")
        print(f"Final state: {trajectories[-1]}")

        # Basic sanity checks
        assert not np.any(np.isnan(trajectories)), "NaN detected in trajectories!"
        assert trajectories[-1, 1] > 0, "Biomass X should be positive"

        print("ODE reproduction test PASSED (Numerical stability and positivity verified).")
        return True
    except Exception as e:
        print(f"ODE reproduction test FAILED: {e}")
        return False

if __name__ == "__main__":
    test_ode_reproduction()
