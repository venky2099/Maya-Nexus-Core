import numpy as np

# Dimension index mapping — consistent everywhere
DIM_INDEX = {
    "shraddha": 0,
    "bhaya":    1,
    "vairagya": 2,
    "spanda":   3,
}
INDEX_DIM = {v: k for k, v in DIM_INDEX.items()}

class WeightMatrix:
    """
    4x4 synaptic weight matrix between Maya's four LIF neurons.

    W[i][j] = learned influence of neuron i on neuron j.
    Positive = excitatory. Negative = inhibitory.
    All weights initialised at 0.0 — no hardcoded connections.
    Every association that forms is earned through co-activation.

    This is the core data structure of Maya's learned experience.
    """

    def __init__(self) -> None:
        self.W = np.zeros((4, 4), dtype=np.float64)
        self.W_clip = 1.0   # hard clamp

    def apply_input(self, dim_values: np.ndarray) -> np.ndarray:
        """
        Given current dimension values, compute synaptic influence.
        Returns a 4-element delta array to add to next pulse input.
        W.T @ dim_values = influence each neuron receives from others.
        """
        influence = self.W.T @ dim_values
        return np.clip(influence, -self.W_clip, self.W_clip)

    def clamp(self) -> None:
        """Keep all weights in [-1.0, 1.0]."""
        np.clip(self.W, -self.W_clip, self.W_clip, out=self.W)

    def as_dict(self) -> dict:
        """Serialisable snapshot for logging."""
        return {
            f"W_{INDEX_DIM[i]}_{INDEX_DIM[j]}": float(self.W[i][j])
            for i in range(4) for j in range(4)
        }

    def snapshot(self) -> np.ndarray:
        """Return copy of W for heatmap visualization."""
        return self.W.copy()


class HebbianLearner:
    """
    Hebbian learning rule for Maya's synaptic weight matrix.

    Core rule: W[A][B] += rate * spike_A * spike_B

    If A and B fire together repeatedly, their connection strengthens.
    If only A fires without B, no update.

    This is unsupervised — no teacher signal, no loss function.
    Maya's connections form purely from the pattern of her experience.

    pain_override: when pain is active, rate is multiplied by lability
    so pain-involved pathways rewrite faster. This is metaplasticity.
    """

    def __init__(self, base_rate: float = 0.01) -> None:
        self.base_rate = base_rate

    def update(self,
               W: np.ndarray,
               spikes: np.ndarray,
               lability: np.ndarray) -> None:
        """
        Apply Hebbian update to W in-place.

        spikes: 4-element binary array — 1.0 if neuron fired, else 0.0
        lability: 4x4 matrix — elevated rate multiplier on pain-tagged synapses
        """
        for i in range(4):
            for j in range(4):
                if i == j:
                    continue  # no self-connections

                # Effective rate: base × (1 + lability boost)
                effective_rate = self.base_rate * (1.0 + lability[i][j])

                # Hebbian update
                delta = effective_rate * spikes[i] * spikes[j]
                W[i][j] += delta

        np.clip(W, -1.0, 1.0, out=W)

class LabilityTracker:
    """
    Per-synapse lability state — Maya's pain memory at the synaptic level.

    When pain or threat is injected:
    - Synapses involving Bhaya and Shraddha are tagged with lability = 1.0
    - This multiplies the Hebbian rate by up to 5x on those pathways
    - Lability decays at 0.98 per tick back toward 0.0

    Effect: pain forces faster synaptic rewriting on the pathways that matter.
    Unimportant pathways (never pain-tagged) learn at base rate only.

    This is metaplasticity — pain changes how fast Maya can change.
    It is the primary novel contribution of this architecture.

    Literature gap confirmed: no published SNN implements continuous
    per-synapse lability with pain-signal gating. Maya does.
    """

    PAIN_EXPERIENCES   = {"pain", "threat"}
    LABILITY_DECAY     = 0.98      # per tick
    PAIN_BOOST         = 5.0       # peak multiplier on pain injection
    LABILITY_THRESHOLD = 0.5       # above this: synapse is pain-protected

    # Which synapses get tagged on pain injection
    # Pain involves Bhaya(1) and suppresses Shraddha(0)
    # Also elevates lability on Spanda(3) — pain disrupts aliveness
    PAIN_SYNAPSES = [
        (1, 0),  # Bhaya → Shraddha
        (0, 1),  # Shraddha → Bhaya
        (1, 3),  # Bhaya → Spanda
        (3, 1),  # Spanda → Bhaya
        (1, 2),  # Bhaya → Vairagya (pain builds wisdom)
    ]

    def __init__(self) -> None:
        self.lability = np.zeros((4, 4), dtype=np.float64)
        self.ticks_since_pain: int = 9999

    def inject_pain(self, intensity: float = 1.0) -> None:
        """
        Called when pain or threat experience is injected.
        Tags relevant synapses with elevated lability.
        intensity: 0.0-1.0 — scales the lability boost.
        """
        boost = intensity * self.PAIN_BOOST
        for (i, j) in self.PAIN_SYNAPSES:
            self.lability[i][j] = min(
                1.0, self.lability[i][j] + boost * 0.2)
        self.ticks_since_pain = 0

    def tick(self) -> None:
        """
        Called every pulse(). Decays all lability values toward 0.
        Pain-tagged synapses remain elevated for ~50 ticks before
        falling below LABILITY_THRESHOLD.
        """
        self.lability *= self.LABILITY_DECAY
        self.ticks_since_pain += 1

    def is_pain_active(self) -> bool:
        """True if within ~50 ticks of last pain injection."""
        return self.ticks_since_pain < 50

    def is_protected(self, i: int, j: int) -> bool:
        """
        True if synapse (i,j) is pain-tagged above threshold.
        Protected synapses are exempt from Vairagya decay.
        """
        return bool(self.lability[i][j] > self.LABILITY_THRESHOLD)

    def snapshot(self) -> np.ndarray:
        return self.lability.copy()

class VairagyaDecay:
    """
    Vairagya-accelerated heterosynaptic decay on synaptic weights.

    Every tick, all weights decay toward zero:
        W[i][j] *= (1.0 - vairagya_decay_rate * vairagya_value)

    EXCEPT: if lability[i][j] > LABILITY_THRESHOLD (pain-protected),
    that synapse is exempt from decay this tick.

    Biological interpretation:
    - Vairagya = wisdom/detachment = graceful forgetting
    - Pain-marked synapses = traumatic memory = resistant to forgetting
    - This asymmetry is heterosynaptic: different synapses decay
      at different rates depending on their pain history

    This completes the novel contribution:
    Pain writes fast (metaplasticity).
    Vairagya erases slow (heterosynaptic decay).
    But pain-written memories resist erasure.
    """

    VAIRAGYA_DECAY_RATE: float = 0.0001  # per tick — slow, dignified

    def apply(self,
              W: np.ndarray,
              vairagya_value: float,
              lability: LabilityTracker) -> None:
        """
        Apply Vairagya decay to W in-place.
        Pain-protected synapses are skipped.
        """
        decay = self.VAIRAGYA_DECAY_RATE * vairagya_value

        for i in range(4):
            for j in range(4):
                if i == j:
                    continue
                if lability.is_protected(i, j):
                    # Pain-tagged synapse — exempt from decay this tick
                    continue
                W[i][j] *= (1.0 - decay)