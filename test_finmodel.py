import numpy as np
from ode_model import solve_ode
from financial_model import BatchEconomics
from collections import OrderedDict as OD

def test_financial_model():
    print("Running Financial Model Test...")

    # 1. Setup Baseline Parameters
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
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]
    t_span = np.arange(0.0, 80.0 + 0.01, 0.01)

    # Generate trajectory
    trajectories = solve_ode(t_span, initial_state, PARAMS)

    # 2. Initialize Economics
    econ = BatchEconomics()

    # Calculate for baseline (D = 0.25)
    metrics = econ.calculate_metrics(trajectories, 0.25, 80.0)

    print("\n--- Baseline Metrics ---")
    print(f"Total Protein: {metrics['total_protein_kg']:.2f} kg")
    print(f"OPEX: {metrics['opex']:.2f} Rub")
    print(f"Cost per kg: {metrics['cost_per_kg']:.2f} Rub/kg")
    print(f"Margin: {metrics['margin']:.2f}%")

    # 3. Sensitivity Analysis for Methane Price
    sensitivity = econ.sensitivity_analysis(trajectories, 0.25, 80.0, param='methane_price')
    print("\n--- Methane Price Sensitivity (Cost/kg) ---")
    for var, cost in sensitivity.items():
        print(f"{var}: {cost:.2f} Rub/kg")

    # Sanity check: cost should increase as methane price increases
    if sensitivity['130%'] > sensitivity['70%']:
        print("\nFinancial model sensitivity test PASSED.")
        return True
    else:
        print("\nFinancial model sensitivity test FAILED.")
        return False

if __name__ == "__main__":
    test_financial_model()
