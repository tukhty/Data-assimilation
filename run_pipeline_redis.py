import time
import json
import redis
import psycopg2
import numpy as np
from collections import OrderedDict as OD
from ode_model import solve_ode
from mnd_assimilation import MNDAssimilation
from regime_optimizer import RegimeOptimizer
from financial_model import BatchEconomics
from export_finance import export_to_google_sheets_format

# CONFIG
REDIS_CONF = {'host': 'localhost', 'port': 6379, 'db': 0}
DB_CONF = "dbname=bioprotein user=admin password=password123 host=localhost"

class PipelineNode:
    def __init__(self, name):
        self.name = name
        self.redis = redis.Redis(**REDIS_CONF)

    def log_timestamp(self, batch_id, stage):
        ts = time.time()
        self.redis.hset(f"ts:{batch_id}", stage, ts)
        return ts

    def publish(self, channel, data):
        self.redis.publish(channel, json.dumps(data))

    def subscribe(self, channel, timeout=30):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        print(f"[{self.name}] Waiting for event on {channel}...")
        for message in pubsub.listen():
            if message['type'] == 'message':
                return json.loads(message['data'])
        return None

def la_pipeline_redis():
    """
    Main Orchestrator using Redis Pub/Sub for high-speed communication.
    """
    batch_id = "BATCH_2026_001"
    node = PipelineNode("Orchestrator")

    # Initial parameters for the Digital Twin
    baseline_params = OD((
        ('dt', 0.01), ('D', 0.25), ('si', 100), ('gamma', 1.0),
        ('ga', 0.3), ('gb', 3.0), ('va', 0.0001), ('vb', 0.009),
        ('mu0', 0.3), ('mua', 0.1), ('mub', 0.7), ('Ks', 10.0),
        ('Ka', 1.0), ('Ia', 100.0), ('Kb', 0.1), ('Ib', 1.0),
        ('y0', 0.0), ('a0', 0.0), ('b0', 0.0)
    ))
    initial_state = [67.2180, 30.9196, 0.355404, 0.011528, 0.0557069]

    # 1. START -> ASSIMILATION
    t0 = node.log_timestamp(batch_id, "start")
    # In a real scenario, this would be triggered by a Redis event 'measurements.ready'
    # For MVP we simulate it:
    measurements = np.random.rand(161, 3) # Mock measurements [t, s, x]
    node.publish("assimilation.start", {"batch_id": batch_id, "data": measurements.tolist()})

    # Simulating the Assimilation Module
    print("[Assimilator] Processing...")
    assimilator = MNDAssimilation(baseline_params, measurements)
    res_assim = assimilator.assimilate([0.1, 0.1, 0.1], ['y0', 'a0', 'b0'], initial_state)
    t1 = node.log_timestamp(batch_id, "assimilation_done")

    # 2. ASSIMILATION -> OPTIMIZER
    node.publish("optimizer.start", {"batch_id": batch_id, "params": res_assim['params']})
    print("[Optimizer] Processing...")
    optimizer = RegimeOptimizer(baseline_params, initial_state)
    # Override params with assimilated ones
    for k, v in res_assim['params'].items():
        optimizer.baseline_params[k] = v

    res_opt = optimizer.optimize(n_calls=10) # Fast run for MVP
    t2 = node.log_timestamp(batch_id, "optimization_done")

    # 3. OPTIMIZER -> FINMODEL
    node.publish("finmodel.start", {"batch_id": batch_id, "d_profile": res_opt['d_profile'].tolist()})
    print("[FinModel] Processing...")
    econ = BatchEconomics()
    metrics = econ.calculate_metrics(res_opt['trajectories'], res_opt['d_profile'], 80.0)
    t3 = node.log_timestamp(batch_id, "finmodel_done")

    # 4. FINMODEL -> DIGITAL TWIN (Back-loop for refinement or execution)
    node.publish("digital_twin.update", {"batch_id": batch_id, "optimal_d": res_opt['optimal_coeffs']})
    t4 = node.log_timestamp(batch_id, "cycle_complete")

    # 5. Export to Excel for Approval
    export_to_google_sheets_format(res_opt['trajectories'], res_opt['d_profile'], metrics, econ.pricing)

    # Report speed
    print("\n--- Pipeline Speed Metrics ---")
    print(f"Total Cycle Time: {t4 - t0:.4f} seconds")
    print(f"Assimilator: {t1 - t0:.4f}s")
    print(f"Optimizer: {t2 - t1:.4f}s")
    print(f"FinModel: {t3 - t2:.4f}s")
    print(f"Back-loop to Twin: {t4 - t3:.4f}s")

if __name__ == "__main__":
    la_pipeline_redis()
