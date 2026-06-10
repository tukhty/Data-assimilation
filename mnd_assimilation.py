import numpy as np
from scipy.optimize import minimize
from ode_model import solve_ode
from collections import OrderedDict as OD

class MNDAssimilation:
    """
    Multivariate Normal Distribution (MND) based data assimilation.
    Recovers unknown parameters by minimizing the difference between
    model trajectories and measurements.
    """
    def __init__(self, model_params, measurements, dt=0.01):
        self.model_params = model_params  # Baseline parameters
        self.measurements = measurements # Array of [t, x, s]
        self.dt = dt

    def _objective(self, theta, param_keys):
        """
        Calculates the RMSE between assimilated trajectory and measurements.
        """
        current_params = self.model_params.copy()
        for key, val in zip(param_keys, theta):
            current_params[key] = val

        t_span = np.arange(0.0, self.measurements[-1, 0] + self.dt, self.dt)

        try:
            trajectories = solve_ode(t_span, self.initial_state, current_params)
            interp_s = np.interp(self.measurements[:, 0], t_span, trajectories[:, 0])
            interp_x = np.interp(self.measurements[:, 0], t_span, trajectories[:, 1])

            rmse_s = np.sqrt(np.mean((interp_s - self.measurements[:, 1])**2))
            rmse_x = np.sqrt(np.mean((interp_x - self.measurements[:, 2])**2))

            return rmse_s + rmse_x
        except Exception:
            return 1e6

    def assimilate(self, initial_guess, param_keys, initial_state):
        self.initial_state = initial_state

        res = minimize(
            self._objective,
            initial_guess,
            args=(param_keys,),
            method='L-BFGS-B',
            bounds=[(None, None)] * len(param_keys)
        )

        best_theta = res.x
        t_span = np.arange(0.0, self.measurements[-1, 0] + self.dt, self.dt)
        final_trajectories = solve_ode(t_span, self.initial_state, {**self.model_params, **dict(zip(param_keys, best_theta))})

        return {
            'params': dict(zip(param_keys, best_theta)),
            'trajectories': final_trajectories,
            'rmse': res.fun
        }

def generate_synthetic_data(initial_state, params, t_max=80.0, noise_level=0.05):
    """
    Generates synthetic measurements with added Gaussian noise.
    """
    t_span = np.arange(0.0, t_max + 0.01, 0.01)
    trajectories = solve_ode(t_span, initial_state, params)

    interval = 0.5
    indices = np.arange(0, len(t_span), int(interval/0.01))

    measurements = []
    for idx in indices:
        t = t_span[idx]
        s = trajectories[idx, 0]
        x = trajectories[idx, 1]
        s_noise = s + np.random.normal(0, noise_level * s)
        x_noise = x + np.random.normal(0, noise_level * x)
        measurements.append([t, s_noise, x_noise])

    return np.array(measurements), trajectories
