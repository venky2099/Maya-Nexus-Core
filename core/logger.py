import csv
import os
import time
import numpy as np
from core.synaptic import DIM_INDEX, INDEX_DIM

LOG_PATH = "memory/maya_research_log.csv"

DIM_NAMES  = ["shraddha", "bhaya", "vairagya", "spanda"]
SPIKE_COLS = [f"spike_{d}" for d in DIM_NAMES]
DIM_COLS   = [f"dim_{d}"   for d in DIM_NAMES]
W_COLS     = [f"W_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
              for i in range(4) for j in range(4) if i != j]
LAB_COLS   = [f"lab_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
              for i in range(4) for j in range(4) if i != j]
VEL_COLS   = [f"vel_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
              for i in range(4) for j in range(4) if i != j]

ALL_COLS = (
    ["tick", "timestamp", "experience"]
    + DIM_COLS
    + SPIKE_COLS
    + ["vairagya_decay_contribution"]
    + W_COLS
    + LAB_COLS
    + VEL_COLS
    + ["experiment_phase"]
)


class DataLogger:
    """
    Research data logger for Maya's Phase 3 experiment.

    Records every tick:
    - All 4 dimension values
    - All 4 spike flags
    - Full 4x4 W matrix (off-diagonal only — 12 values)
    - All 4x4 lability values (off-diagonal)
    - Velocity (delta W per tick) — 12 values
    - Vairagya decay contribution this tick
    - Experience injected (empty string if none)
    - Experiment phase label (A/B/C/D or 'live')

    This is the results data. Without this we cannot publish.
    """

    def __init__(self, log_path: str = LOG_PATH) -> None:
        self.log_path            = log_path
        self.tick_count          = 0
        self.current_phase       = "live"
        self.w_snapshot_interval = 100
        self._last_w_snapshot    = 0
        self._in_experiment      = False
        self._prev_W             = np.zeros((4, 4), dtype=np.float64)

        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._init_csv()
        print(f"--- DATALOGGER: recording to {log_path} ---")

    def _init_csv(self) -> None:
        file_exists = os.path.exists(self.log_path)
        self._file  = open(self.log_path, "a", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=ALL_COLS)
        if not file_exists:
            self._writer.writeheader()
            self._file.flush()

    def set_phase(self, phase: str) -> None:
        self.current_phase       = phase
        self._in_experiment      = phase in {"A", "B", "C", "D"}
        self.w_snapshot_interval = 1 if self._in_experiment else 100
        print(f"--- DATALOGGER: phase → {phase} ---")

    def log(self,
            tick:       int,
            dim_values: dict,
            spikes:     dict,
            W:          np.ndarray,
            lability:   np.ndarray,
            vairagya:   float,
            experience: str = "") -> None:

        self.tick_count += 1
        should_log_W = (
            self._in_experiment or
            (self.tick_count - self._last_w_snapshot >= self.w_snapshot_interval)
        )
        if should_log_W:
            self._last_w_snapshot = self.tick_count

        row = {
            "tick":                        tick,
            "timestamp":                   time.time(),
            "experience":                  experience,
            "experiment_phase":            self.current_phase,
            "vairagya_decay_contribution": round(0.0001 * vairagya, 6),
        }

        # Dimension values
        for d in DIM_NAMES:
            row[f"dim_{d}"] = round(dim_values.get(d.capitalize(), 0.0), 6)

        # Spike flags
        for d in DIM_NAMES:
            row[f"spike_{d}"] = int(spikes.get(d, False))

        # W matrix
        for i in range(4):
            for j in range(4):
                if i == j:
                    continue
                key = f"W_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
                row[key] = round(float(W[i][j]), 6) if should_log_W else ""

        # Lability
        for i in range(4):
            for j in range(4):
                if i == j:
                    continue
                key = f"lab_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
                row[key] = round(float(lability[i][j]), 6) if should_log_W else ""

        # ── Velocity — delta W per tick ──
        for i in range(4):
            for j in range(4):
                if i == j:
                    continue
                key   = f"vel_{INDEX_DIM[i]}_{INDEX_DIM[j]}"
                delta = float(W[i][j]) - float(self._prev_W[i][j])
                row[key] = round(delta, 8) if should_log_W else ""

        # Update previous W snapshot
        if should_log_W:
            self._prev_W = W.copy()

        self._writer.writerow(row)

        if self.tick_count % 100 == 0:
            self._file.flush()

    def close(self) -> None:
        self._file.flush()
        self._file.close()
        print(f"--- DATALOGGER: closed. {self.tick_count} ticks recorded ---")