import numpy as np
from collections import OrderedDict as OD

class BatchEconomics:
    """
    Financial model for calculating the economics of a single fermentation batch.
    Focuses on protein production using a jet-loop fermenter.
    """
    def __init__(self, pricing_config=None):
        # Default pricing configuration if none provided
        if pricing_config is None:
            self.pricing = OD((
                ('methane_price', 5.0),      # Rub/m3 (example)
                ('electricity_price', 6.0),  # Rub/kWh
                ('labor_cost', 50000),       # Rub/batch
                ('amortization', 20000),     # Rub/batch
                ('protein_value', 1500.0),   # Rub/kg (Target selling price)
                ('methane_density', 0.65),   # kg/m3
                ('energy_per_kg_biomass', 2.5), # kWh/kg (specific for jet-loop)
                ('protein_content', 0.68),   # Fraction of dry biomass
            ))
        else:
            self.pricing = pricing_config

    def calculate_metrics(self, trajectories, d_profile, batch_duration):
        """
        Calculates financial metrics based on assimilated trajectories and optimal D profile.

        trajectories: ndarray [S, X, Y, A, B]
        d_profile: function or array of D(t)
        batch_duration: duration in hours
        """
        # 1. Biomass Production
        final_x = trajectories[-1, 1] # Final concentration of X (g/L)
        volume = 1000.0 # Assume 1 m3 for the pilot
        total_biomass_kg = (final_x * volume) / 1000.0
        total_protein_kg = total_biomass_kg * self.pricing['protein_content']

        # 2. Methane Consumption
        # Integral of D * (Si - S) over time
        t_span = np.arange(0, batch_duration, 0.01)
        # Calculate D as a vector
        if callable(d_profile):
            d_vals = np.array([d_profile(t) for t in t_span])
        elif isinstance(d_profile, np.ndarray):
            d_vals = d_profile
        else:
            d_vals = np.full(len(t_span), d_profile)

        # Methane feed: sum(D * Si * dt * Volume)
        si = 100.0 # Default Si
        total_methane_m3 = np.sum(d_vals * si * 0.01 * volume) / 1000.0 # simplified conversion

        # 3. Costs
        methane_cost = total_methane_m3 * self.pricing['methane_price']
        energy_cost = total_biomass_kg * self.pricing['energy_per_kg_biomass'] * self.pricing['electricity_price']
        opex = methane_cost + energy_cost + self.pricing['labor_cost'] + self.pricing['amortization']

        # 4. Revenue and NPV (simplified for one batch)
        revenue = total_protein_kg * self.pricing['protein_value']
        profit = revenue - opex
        cost_per_kg = opex / total_protein_kg if total_protein_kg > 0 else float('inf')

        return {
            'total_protein_kg': total_protein_kg,
            'total_methane_m3': total_methane_m3,
            'opex': opex,
            'revenue': revenue,
            'profit': profit,
            'cost_per_kg': cost_per_kg,
            'margin': (profit / revenue) * 100 if revenue > 0 else 0
        }

    def sensitivity_analysis(self, trajectories, d_profile, batch_duration, param='methane_price'):
        """
        Analyzes how the cost_per_kg changes with the specified parameter variance.
        """
        results = {}
        original_val = self.pricing[param]
        for var in [0.7, 0.9, 1.0, 1.1, 1.3]: # -30% to +30%
            self.pricing[param] = original_val * var
            metrics = self.calculate_metrics(trajectories, d_profile, batch_duration)
            results[f"{int(var*100)}%"] = metrics['cost_per_kg']

        # Reset parameter
        self.pricing[param] = original_val
        return results
