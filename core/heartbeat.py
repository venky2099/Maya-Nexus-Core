import torch
import numpy as np
from collections import deque
from spikingjelly.activation_based import neuron, functional, surrogate

from core.dimensions import MayaDimensions
from core.synaptic import WeightMatrix, HebbianLearner, LabilityTracker, VairagyaDecay, DIM_INDEX, INDEX_DIM
from core.logger import DataLogger

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TAU_MAP = {
    "shraddha": 10.0,
    "bhaya":     3.0,
    "vairagya": 20.0,
    "spanda":    5.0,
}

EXPERIENCE_MAP = {
    "curiosity":     {"shraddha": +0.10, "bhaya": -0.05,
                      "vairagya": +0.02, "spanda": +0.15},
    "joy":           {"shraddha": +0.15, "bhaya": -0.10,
                      "vairagya": -0.01, "spanda": +0.20},
    "connection":    {"shraddha": +0.20, "bhaya": -0.08,
                      "vairagya": +0.01, "spanda": +0.10},
    "calm":          {"shraddha": +0.05, "bhaya": -0.15,
                      "vairagya": +0.05, "spanda": -0.10},
    "pain":          {"shraddha": -0.15, "bhaya": +0.25,
                      "vairagya": +0.05, "spanda": -0.10},
    "threat":        {"shraddha": -0.20, "bhaya": +0.35,
                      "vairagya": +0.02, "spanda": +0.15},
    "loneliness":    {"shraddha": -0.10, "bhaya": +0.05,
                      "vairagya": +0.08, "spanda": -0.15},
    "understanding": {"shraddha": +0.08, "bhaya": -0.05,
                      "vairagya": +0.10, "spanda": +0.05},
}


class MayaHeartbeat:
    """
    Maya's central nervous system.

    Each pulse():
    1. Apply Vairagya decay to dimension floats
    2. Compute synaptic influence from W matrix
    3. Run 4 LIF neurons with combined input
    4. Apply Hebbian learning on co-firing pairs
    5. Apply Vairagya heterosynaptic decay on W
    6. Decay lability
    7. Log everything
    """

    def __init__(self, dimensions: MayaDimensions,
                 logger: DataLogger = None) -> None:
        self.dimensions = dimensions
        self.logger     = logger
        self.tick       = 0

        # LIF neurons
        dim_names = list(TAU_MAP.keys())
        self.dim_names = dim_names
        self.neurons   = {}
        for name, tau in TAU_MAP.items():
            self.neurons[name] = neuron.LIFNode(
                tau=tau,
                v_threshold=1.0,
                v_reset=0.0,
                surrogate_function=surrogate.ATan()
            ).to(DEVICE)

        # Rolling membrane history for visualizer
        self.membrane_history = {
            name: deque([0.0] * 200, maxlen=200)
            for name in dim_names
        }

        # Phase 3 — synaptic components
        self.weight_matrix  = WeightMatrix()
        self.hebbian        = HebbianLearner(base_rate=0.01)
        self.lability       = LabilityTracker()
        self.vairagya_decay = VairagyaDecay()

        # Experiment protocol state
        self._experiment_running  = False
        self._experiment_tick     = 0
        self._last_experience     = ""

        print(f"--- MAYA HEARTBEAT IGNITING ON: {DEVICE} ---")

    # ─────────────────────────────────────────
    # EXPERIENCE INJECTION
    # ─────────────────────────────────────────

    def inject_experience(self, experience: str) -> None:
        """Apply experience delta to dimensions + trigger lability if pain."""
        if experience not in EXPERIENCE_MAP:
            return

        deltas = EXPERIENCE_MAP[experience]
        d = self.dimensions

        d.shraddha  = float(np.clip(d.shraddha  + deltas["shraddha"],  0.0, 1.0))
        d.bhaya     = float(np.clip(d.bhaya     + deltas["bhaya"],     0.0, 1.0))
        d.vairagya  = float(np.clip(d.vairagya  + deltas["vairagya"],  0.0, 1.0))
        d.spanda    = float(np.clip(d.spanda    + deltas["spanda"],    0.0, 1.0))

        # Pain/threat → trigger metaplasticity
        if experience in LabilityTracker.PAIN_EXPERIENCES:
            intensity = deltas.get("bhaya", 0.25)
            self.lability.inject_pain(intensity=intensity)

        self._last_experience = experience

    def reset(self) -> None:
        """Reset dimensions and LIF state. Preserve W matrix — memory persists."""
        self.dimensions.shraddha = 0.5
        self.dimensions.bhaya    = 0.0
        self.dimensions.vairagya = 0.3
        self.dimensions.spanda   = 0.5
        for n in self.neurons.values():
            functional.reset_net(n)
        print(">>> HEARTBEAT RESET (W matrix preserved)")

    # ─────────────────────────────────────────
    # MAIN PULSE
    # ─────────────────────────────────────────

    def pulse(self) -> dict:
        self.tick += 1
        d = self.dimensions

        # 1. Vairagya decay on dimension floats
        d.apply_vairagya()

        # 2. Current dimension values as array
        dim_array = np.array([
            d.shraddha, d.bhaya, d.vairagya, d.spanda
        ], dtype=np.float64)

        # 3. Synaptic influence from W matrix
        synaptic_input = self.weight_matrix.apply_input(dim_array)

        # 4. Run LIF neurons
        spikes_binary = np.zeros(4, dtype=np.float64)
        spikes_dict   = {}

        for idx, name in enumerate(self.dim_names):
            raw_input = float(np.clip(
                dim_array[idx] * 4.0 + synaptic_input[idx] * 0.1,
                0.0, 3.0
            ))
            x = torch.tensor([[raw_input]],
                             dtype=torch.float32).to(DEVICE)

            # Run 10 timesteps — membrane charges across steps, then spikes
            spiked = False
            for _ in range(10):
                out = self.neurons[name](x)
                if bool(out.any()):
                    spiked = True
                    break  # spike occurred, no need to continue

            spikes_dict[name] = spiked
            spikes_binary[idx] = 1.0 if spiked else 0.0

            v = self.neurons[name].v.item()
            self.membrane_history[name].append(v)

        functional.reset_net(torch.nn.ModuleList(list(self.neurons.values())))

        # 5. Hebbian learning
        self.hebbian.update(
            self.weight_matrix.W,
            spikes_binary,
            self.lability.lability
        )

        # 6. Vairagya heterosynaptic decay on W
        self.vairagya_decay.apply(
            self.weight_matrix.W,
            d.vairagya,
            self.lability
        )

        # 7. Decay lability
        self.lability.tick()

        # 8. Log
        if self.logger:
            exp_this_tick = self._last_experience
            self._last_experience = ""   # consume — log once per injection
            self.logger.log(
                tick        = self.tick,
                dim_values  = {
                    "Shraddha": d.shraddha,
                    "Bhaya":    d.bhaya,
                    "Vairagya": d.vairagya,
                    "Spanda":   d.spanda,
                },
                spikes      = spikes_dict,
                W           = self.weight_matrix.W,
                lability    = self.lability.lability,
                vairagya    = d.vairagya,
                experience  = exp_this_tick
            )

        return {
            "tick":        self.tick,
            "dimensions":  {
                "Shraddha": d.shraddha,
                "Bhaya":    d.bhaya,
                "Vairagya": d.vairagya,
                "Spanda":   d.spanda,
            },
            "spikes":      spikes_dict,
            "W_snapshot":  self.weight_matrix.snapshot(),
        }

    # ─────────────────────────────────────────
    # EXPERIMENT PROTOCOL
    # ─────────────────────────────────────────

    def run_experiment(self) -> None:
        """
        Baseline experiment protocol — runs 200 ticks automatically.
        Repeatable. Identical every run. This is our paper result.

        Phase A (50 ticks):  neutral — observe baseline W
        Phase B (50 ticks):  pain every 10 ticks — watch W[bhaya][shraddha]
        Phase C (50 ticks):  joy every 10 ticks — watch pain pathways decay
        Phase D (50 ticks):  pain again — watch if pathways reactivate faster

        Call this once from maya.py before mindscape.run()
        Results saved to memory/maya_research_log.csv
        """
        if not self.logger:
            print("--- EXPERIMENT: no logger attached, skipping ---")
            return

        print("=" * 55)
        print("MAYA PHASE 3 EXPERIMENT — STARTING")
        print("200 ticks. Results → memory/maya_research_log.csv")
        print("=" * 55)

        phases = [
            ("A", 50,  None,  "Neutral baseline"),
            ("B", 50,  "pain",  "Pain every 10 ticks"),
            ("C", 50,  "joy",   "Joy every 10 ticks"),
            ("D", 50,  "pain",  "Pain again — reactivation test"),
        ]

        for phase_label, n_ticks, stimulus, description in phases:
            self.logger.set_phase(phase_label)
            print(f"\n  Phase {phase_label}: {description}")

            for t in range(n_ticks):
                if stimulus and t % 10 == 0:
                    self.inject_experience(stimulus)

                result = self.pulse()

                # Print W[bhaya→shraddha] every 10 ticks
                if t % 10 == 0:
                    w_bs = self.weight_matrix.W[
                        DIM_INDEX["bhaya"]][DIM_INDEX["shraddha"]]
                    w_ss = self.weight_matrix.W[
                        DIM_INDEX["shraddha"]][DIM_INDEX["spanda"]]
                    print(f"    tick {t:3d} | "
                          f"bhaya→shraddha: {w_bs:+.4f} | "
                          f"shraddha→spanda: {w_ss:+.4f} | "
                          f"bhaya: {result['dimensions']['Bhaya']:.3f}")

        self.logger.set_phase("live")
        print("\n" + "=" * 55)
        print("EXPERIMENT COMPLETE")
        print(f"Data saved → memory/maya_research_log.csv")
        print("=" * 55 + "\n")