import numpy as np
from collections import OrderedDict as OD
from ode_model import solve_ode
from mnd_assimilation import MNDAssimilation, generate_synthetic_data
from regime_optimizer import RegimeOptimizer
from financial_model import BatchEconomics
from export_finance import export_to_google_sheets_format

def run_e2e_test():
    print("=== STARTING END-TO-END MVP TEST ===")

    # 1. Setup Ground Truth
    TRUE_PARAMS = OD((
        ('dt', 0.01), ('D', 0.25), ('si', 100), ('gamma', 1.0),
        ('ga', 0.3), ('gb', 3.0), ('va', 0.0001), ('vb', 0.009),
        ('mu0', 0.3), ('mua', 0.1), ('mub', 0.7), ('Ks', 10.0),
        ('Ka', 1.0), ('Ia', 100.0), ('Kb', 0.1), ('Ib', 1.0),
        ('y0', 0.0), ('a0', 0.0), ('b0', 0.0)
    ))
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]

    # 2. Generate Synthetic Data (Simulation of Digital Twin)
    print("[1/5] Generating synthetic measurements...")
    measurements, true_trajectories = generate_synthetic_data(initial_state, TRUE_PARAMS, noise_level=0.02)

    # 3. Assimilation (Recovering parameters)
    print("[2/5] Running Data Assimilation (MND)...")
    baseline_params = TRUE_PARAMS.copy()
    baseline_params['y0'], baseline_params['a0'], baseline_params['b0'] = 0.1, 0.1, 0.1

    assimilator = MNDAssimilation(baseline_params, measurements)
    res_assim = assimilator.assimilate([0.1, 0.1, 0.1], ['y0', 'a0', 'b0'], initial_state)

    # 4. Optimization (Finding optimal D profile)
    print("[3/5] Running Regime Optimization (Bayesian)...")
    optimizer = RegimeOptimizer(baseline_params, initial_state)
    for k, v in res_assim['params'].items():
        optimizer.baseline_params[k] = v

    res_opt = optimizer.optimize(n_calls=20)

    # 5. Financial Evaluation
    print("[4/5] Calculating Economics...")
    econ = BatchEconomics()
    metrics = econ.calculate_metrics(res_opt['trajectories'], res_opt['d_profile'], 80.0)

    # 6. Final Export
    print("[5/5] Exporting to Financial Report...")
    export_to_google_sheets_format(res_opt['trajectories'], res_opt['d_profile'], metrics, econ.pricing)

    print("\n=== FINAL E2E RESULTS ===")
    print(f"Max Profit: {res_opt['max_profit']:.2f} Rub")
    print(f"Cost per kg: {metrics['cost_per_kg']:.2f} Rub/kg")
    print(f"Protein Output: {metrics['total_protein_kg']:.2f} kg")

    # Comparison with baseline (D=0.25)
    baseline_profit = -optimizer._objective([0.25, 0, 0, 0, 0, 0])
    print(f"Baseline Profit: {baseline_profit:.2f} Rub")

    success = res_opt['max_profit'] > baseline_profit
    if success:
        print("\nE2E TEST PASSED: System successfully improved the production regime.")
    else:
        print("\nE2E TEST FAILED: Optimization did not outperform baseline.")

    return success

if __name__ == "__main__":
    run_e2e_test()
