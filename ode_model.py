import numpy as np
from scipy.integrate import odeint
from collections import OrderedDict as OD

# Constants used in the ODE system
EPSILON = 1.0e-10

def ode_system(t, state, dt, D_func, si, gamma, ga, gb, va, vb, mu0, mua, mub, Ks, Ka, Ia, Kb, Ib, y0_base, a0_base, b0_base):
    """
    The ODE system describing the fermentation process.
    """
    s, x, y, a, b = state

    # Adjusted values
    y_adj = y + y0_base
    a_adj = a + a0_base
    b_adj = b + b0_base

    # Dilution rate handling
    if isinstance(D_func, np.ndarray):
        idx = int((t + EPSILON) // dt)
        if idx >= len(D_func):
            D = D_func[-1]
        else:
            D = D_func[idx]
    else:
        D = D_func(t) if callable(D_func) else D_func

    # Growth rates
    mux = mu0 * s / (s + Ks) * Ia / (Ia + a_adj) * Ib / (Ib + b_adj)
    muy = (mua * a_adj / Ka + mub * b_adj / Kb) / (1 + a_adj / Ka + b_adj / Kb)

    # Metabolic rates
    qa = ga / (1 + a_adj / Ka + b_adj / Kb) * mua * a_adj / Ka
    qb = gb / (1 + a_adj / Ka + b_adj / Kb) * mub * b_adj / Kb

    # ODEs
    ds = D * (si - s) - gamma * mux * x
    dx = (mux - D) * x
    dy = (muy - D) * y
    da = va * x - D * a - qa * y
    db = vb * x - D * b - qb * y

    return [ds, dx, dy, da, db]

def solve_ode(t_span, initial_state, params):
    """
    Helper to solve the ODE system over a time span.
    """
    D = params.get('D', 0.25)
    dt = params.get('dt', 0.01)

    args = (
        dt, D,
        params['si'], params['gamma'], params['ga'], params['gb'],
        params['va'], params['vb'], params['mu0'], params['mua'], params['mub'],
        params['Ks'], params['Ka'], params['Ia'], params['Kb'], params['Ib'],
        params['y0'], params['a0'], params['b0']
    )

    return odeint(ode_system, initial_state, t_span, args=args, tfirst=True)
