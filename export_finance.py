import numpy as np
import pandas as pd
from financial_model import BatchEconomics
from collections import OrderedDict as OD

def export_to_google_sheets_format(trajectories, d_profile, metrics, pricing_config):
    """
    Exports the financial model calculations to an Excel file (.xlsx)
    which can be easily imported into Google Sheets.
    Includes 'formula' placeholders for transparency.
    """
    # 1. Data for trajectories
    df_traj = pd.DataFrame(trajectories, columns=['S', 'X', 'Y', 'A', 'B'])
    df_traj['t'] = np.arange(0, len(df_traj)) * 0.01

    # 2. Summary Economics
    summary_data = {
        'Metric': ['Total Protein (kg)', 'OPEX (Rub)', 'Cost per kg (Rub/kg)', 'Margin (%)', 'Revenue (Rub)'],
        'Value': [
            metrics['total_protein_kg'],
            metrics['opex'],
            metrics['cost_per_kg'],
            metrics['margin'],
            metrics['revenue']
        ],
        'Formula': [
            '=X_final * Vol * ProteinContent',
            '=MethaneCost + EnergyCost + Labor + Amort',
            '=OPEX / TotalProtein',
            '=(Profit/Revenue)*100',
            '=TotalProtein * ProteinValue'
        ]
    }
    df_summary = pd.DataFrame(summary_data)

    # 3. Pricing Configuration
    df_pricing = pd.DataFrame(list(pricing_config.items()), columns=['Parameter', 'Value'])

    with pd.ExcelWriter('financial_report.xlsx', engine='openpyxl') as writer:
        df_traj.to_excel(writer, sheet_name='Trajectories', index=False)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        df_pricing.to_excel(writer, sheet_name='Pricing', index=False)

    print("Financial report exported to financial_report.xlsx (Ready for Google Sheets import).")
