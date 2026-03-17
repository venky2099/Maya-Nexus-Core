"""
Maya — Baseline Experiment Protocol
Reproducible Phase A→D experiment with seeded random state.

Usage:
    python experiments/baseline_protocol.py --seed 42 --output results/run_001/
    python experiments/baseline_protocol.py --seed 123 --output results/run_002/
    python experiments/baseline_protocol.py --seed 7 --output results/run_003/
"""

import argparse
import os
import sys
import random
import numpy as np
import torch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dimensions import MayaDimensions
from core.heartbeat import MayaHeartbeat
from core.logger import DataLogger

# ── Protocol constants — never change these between runs ──
PROTOCOL = [
    ("A", 50, None,    "Neutral baseline"),
    ("B", 50, "pain",  "Pain every 10 ticks"),
    ("C", 50, "joy",   "Joy every 10 ticks"),
    ("D", 50, "pain",  "Pain again — reactivation test"),
]
STIMULUS_INTERVAL = 10   # ticks between stimuli


def run(seed: int, output_dir: str) -> None:
    # ── Seed everything ──
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "maya_research_log.csv")

    print(f"\n{'='*55}")
    print(f"MAYA BASELINE PROTOCOL — seed={seed}")
    print(f"Output: {log_path}")
    print(f"{'='*55}")

    dimensions = MayaDimensions()
    logger     = DataLogger(log_path=log_path)
    heartbeat  = MayaHeartbeat(dimensions, logger=logger)

    for phase_label, n_ticks, stimulus, description in PROTOCOL:
        logger.set_phase(phase_label)
        print(f"\n  Phase {phase_label}: {description}")

        for t in range(n_ticks):
            if stimulus and t % STIMULUS_INTERVAL == 0:
                heartbeat.inject_experience(stimulus)

            result = heartbeat.pulse()

            if t % 10 == 0:
                from core.synaptic import DIM_INDEX
                w_bs = heartbeat.weight_matrix.W[
                    DIM_INDEX["bhaya"]][DIM_INDEX["shraddha"]]
                w_ss = heartbeat.weight_matrix.W[
                    DIM_INDEX["shraddha"]][DIM_INDEX["spanda"]]
                print(f"    tick {t:3d} | "
                      f"fear→trust: {w_bs:+.4f} | "
                      f"trust→aliveness: {w_ss:+.4f} | "
                      f"fear: {result['dimensions']['Bhaya']:.3f}")

    logger.close()
    print(f"\n{'='*55}")
    print(f"COMPLETE — seed={seed} → {log_path}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed",   type=int, default=42)
    parser.add_argument("--output", type=str, default="results/run_001/")
    args = parser.parse_args()
    run(args.seed, args.output)