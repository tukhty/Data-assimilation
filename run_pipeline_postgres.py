import time
import json
import psycopg2
import numpy as np
from collections import OrderedDict as OD
from ode_model import solve_ode
from mnd_assimilation import MNDAssimilation
from regime_optimizer import RegimeOptimizer
from financial_model import BatchEconomics
from export_finance import export_to_google_sheets_format

# CONFIG
DB_CONF = "dbname=bioprotein user=admin password=password123 host=localhost"

class PostgresNode:
    def __init__(self, name):
        self.name = name

    def log_timestamp(self, batch_id, stage):
        ts = time.time()
        conn = psycopg2.connect(DB_CONF)
        cur = conn.cursor()
        cur.execute("INSERT INTO pipeline_timestamps (batch_id, stage, ts) VALUES (%s, %s, %s) ON CONFLICT (batch_id, stage) DO UPDATE SET ts = EXCLUDED.ts", (batch_id, stage, ts))
        conn.commit()
        cur.close()
        conn.close()
        return ts

    def signal_ready(self, batch_id, stage):
        conn = psycopg2.connect(DB_CONF)
        cur = conn.cursor()
        cur.execute("UPDATE pipeline_status SET status = 'ready' WHERE batch_id = %s AND stage = %s", (batch_id, stage))
        conn.commit()
        cur.close()
        conn.close()

    def wait_for_signal(self, batch_id, stage):
        while True:
            conn = psycopg2.connect(DB_CONF)
            cur = conn.cursor()
            cur.execute("SELECT status FROM pipeline_status WHERE batch_id = %s AND stage = %s", (batch_id, stage))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0] == 'ready':
                return True
            time.sleep(1)

def la_pipeline_postgres():
    """
    Main Orchestrator using PostgreSQL Polling (Variant A).
    """
    batch_id = "BATCH_2026_001"
    node = PostgresNode("Orchestrator")

    baseline_params = OD((
        ('dt', 0.01), ('D', 0.25), ('si', 100), ('gamma', 1.0),
        ('ga', 0.3), ('gb', 3.0), ('va', 0.0001), ('vb', 0.009),
        ('mu0', 0.3), ('mua', 0.1), ('mub', 0.7), ('Ks', 10.0),
        ('Ka', 1.0), ('Ia', 100.0), ('Kb', 0.1), ('Ib', 1.0),
        ('y0', 0.0), ('a0', 0.0), ('b0', 0.0)
    ))
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]

    t0 = node.log_timestamp(batch_id, "start")

    # Simulating stages with Polling
    print("[Assimilator] Processing...")
    measurements = np.random.rand(161, 3)
    assimilator = MNDAssimilation(baseline_params, measurements)
    res_assim = assimilator.assimilate([0.1, 0.1, 0.1], ['y0', 'a0', 'b0'], initial_state)
    t1 = node.log_timestamp(batch_id, "assimilation_done")

    print("[Optimizer] Processing...")
    optimizer = RegimeOptimizer(baseline_params, initial_state)
    for k, v in res_assim['params'].items():
        optimizer.baseline_params[k] = v
    res_opt = optimizer.optimize(n_calls=10)
    t2 = node.log_timestamp(batch_id, "optimization_done")

    print("[FinModel] Processing...")
    econ = BatchEconomics()
    metrics = econ.calculate_metrics(res_opt['trajectories'], res_opt['d_profile'], 80.0)
    t3 = node.log_timestamp(batch_id, "finmodel_done")

    t4 = node.log_timestamp(batch_id, "cycle_complete")

    export_to_google_sheets_format(res_opt['trajectories'], res_opt['d_profile'], metrics, econ.pricing)

    print("\n--- Pipeline Speed Metrics (Postgres) ---")
    print(f"Total Cycle Time: {t4 - t0:.4f} seconds")
    print(f"Assimilator: {t1 - t0:.4f}s")
    print(f"Optimizer: {t2 - t1:.4f}s")
    print(f"FinModel: {t3 - t2:.4f}s")
    print(f"Back-loop: {t4 - t3:.4f}s")

if __name__ == "__main__":
    la_pipeline_postgres()
