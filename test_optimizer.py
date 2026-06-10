import numpy as np
from regime_optimizer import RegimeOptimizer
from collections import OrderedDict as OD

def test_optimizer():
    print("Running Regime Optimizer Test (Bayesian)...")

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

    # 2. Initialize Optimizer
    optimizer = RegimeOptimizer(PARAMS, initial_state)

    # 3. Run Optimization
    print("Optimizing... (this may take a minute)")
    result = optimizer.optimize(n_calls=20)

    print("\n--- Optimization Results ---")
    print(f"Max Profit: {result['max_profit']:.2f} Rub")
    print(f"Cost per kg: {result['metrics']['cost_per_kg']:.2f} Rub/kg")
    print(f"Protein produced: {result['metrics']['total_protein_kg']:.2f} kg")

    # Baseline comparison (D=0.25)
    baseline_profit = -optimizer._objective([0.25, 0, 0, 0, 0, 0])
    print(f"Baseline Profit (D=0.25): {baseline_profit:.2f} Rub")

    if result['max_profit'] >= baseline_profit:
        print("\nOptimizer successfully found a regime equal or better than baseline.")
        return True
    else:
        print("\nOptimizer failed to improve baseline.")
        return False

if __name__ == "__main__":
    test_optimizer()
