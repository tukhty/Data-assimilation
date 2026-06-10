import numpy as np
from skopt import gp_minimize
from ode_model import solve_ode
from financial_model import BatchEconomics
from collections import OrderedDict as OD

class RegimeOptimizer:
    """
    Optimizer for finding the optimal dilution rate D(t) to maximize NPV.
    Uses Bayesian Optimization (Gaussian Processes) via skopt.
    """
    def __init__(self, baseline_params, initial_state, pricing_config=None):
        self.baseline_params = baseline_params
        self.initial_state = initial_state
        self.econ = BatchEconomics(pricing_config)

        # Search space for D(t) coefficients
        # We use the hyperbolic approximation from the original code (c0-c5)
        # bounds: (min, max)
        self.space = [
            (0.1, 0.4),      # c0: Base dilution rate
            (-0.01, 0.01),   # c1
            (-0.001, 0.001), # c2
            (-0.00002, 0.00002), # c3
            (-0.001, 0.001), # c4
            (-0.00002, 0.00002)  # c5
        ]

    def _d_profile(self, t, c):
        """
        Approximates D(t) using two hyperbolas (piecewise cubic)
        as seen in environment_vF11.py.
        """
        xb = 40.0 # Boundary point

        # Left side (t <= xb)
        d_left = c[0] + c[1]*t + c[2]*t**2 + c[3]*t**3

        # Right side (t > xb)
        m1 = 3*c[3]*xb**2 + 2*c[2]*xb + c[1]
        f2 = c[4]
        f3 = c[5]
        f1 = m1 - 3*f3*xb**2 - 2*f2*xb
        f0 = (c[0] + c[1]*xb + c[2]*xb**2 + c[3]*xb**3) - (f3*xb**3 + f2*xb**2 + f1*xb)

        d_right = f0 + f1*t + f2*t**2 + f3*t**3

        return np.where(t <= xb, d_left, d_right)

    def _objective(self, c):
        """
        Objective function for gp_minimize: maximize NPV (minimize -NPV).
        """
        # 1. Generate D profile
        t_span = np.arange(0.0, 80.0 + 0.01, 0.01)
        d_vals = self._d_profile(t_span, c)

        # 2. Solve ODE
        params = self.baseline_params.copy()
        params['D'] = d_vals

        try:
            trajectories = solve_ode(t_span, self.initial_state, params)

            # 3. Calculate Economics
            metrics = self.econ.calculate_metrics(trajectories, d_vals, 80.0)

            # Constraints:
            # X must be > 0 (no washout)
            if np.any(trajectories[:, 1] <= 0):
                return 1e9

            # Maximize Profit (Minimize -Profit)
            return -metrics['profit']

        except Exception:
            return 1e9

    def optimize(self, n_calls=30):
        """
        Runs Bayesian Optimization to find the best coefficients for D(t).
        """
        res = gp_minimize(
            self._objective,
            self.space,
            n_calls=n_calls,
            random_state=42
        )

        best_c = res.x
        best_profit = -res.fun

        # Final trajectory and metrics for the best result
        t_span = np.arange(0.0, 80.0 + 0.01, 0.01)
        d_vals = self._d_profile(t_span, best_c)
        params = self.baseline_params.copy()
        params['D'] = d_vals
        trajectories = solve_ode(t_span, self.initial_state, params)
        metrics = self.econ.calculate_metrics(trajectories, d_vals, 80.0)

        return {
            'optimal_coeffs': best_c,
            'max_profit': best_profit,
            'metrics': metrics,
            'trajectories': trajectories,
            'd_profile': d_vals
        }
