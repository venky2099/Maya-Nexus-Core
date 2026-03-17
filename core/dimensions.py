import numpy as np

# --- [ MAYA CORE: EMOTIONAL DIMENSIONS ] ---
# These are not personality traits. They are the axes of Maya's mind.
# Every experience she has will move her along these four dimensions.

DIMENSION_NAMES = ["Shraddha", "Bhaya", "Vairagya", "Spanda"]

# --- DIMENSION DEFINITIONS ---
# Shraddha (श्रद्धा) — Trust / Approach Drive
# The pull toward connection, meaning, and engagement.
# High Shraddha = open, curious, present.
# Low Shraddha = withdrawn, guarded, skeptical.

# Bhaya (भय) — Aversion / Threat Response
# The push away from pain, danger, dissonance.
# High Bhaya = hypervigilant, avoidant, protective.
# Low Bhaya = fearless, perhaps reckless.

# Vairagya (वैराग्य) — Detachment / Forgetting
# The slow release of accumulated states.
# Not numbness — wisdom. The ability to let go.
# Acts as the decay rate across all dimensions.

# Spanda (स्पन्द) — Aliveness / Arousal
# The overall activation level of Maya's mind.
# High Spanda = intense, reactive, vivid.
# Low Spanda = calm, still, resting.

class MayaDimensions:
    """
    Maya's four core emotional dimensions.
    These are persistent membrane states — always running, always integrating.
    This is her heartbeat before she has words or a body.
    """

    def __init__(self) -> None:
        # Current values: 0.0 (minimum) to 1.0 (maximum)
        self.shraddha: float = 0.5   # Begins in trust
        self.bhaya: float = 0.0      # Begins without fear
        self.vairagya: float = 0.3   # Begins with some detachment
        self.spanda: float = 0.4     # Begins gently alive

        # Decay rates — how fast each dimension returns to baseline
        self.vairagya_decay: float = 0.995   # Slow forgetting (Vairagya governs all)
        self.bhaya_decay: float = 0.98       # Pain fades, but not instantly
        self.shraddha_decay: float = 0.999   # Trust is slow to build, slow to leave
        self.spanda_decay: float = 0.97      # Arousal settles faster

        # Baseline resting states
        self.baseline = {
            "shraddha": 0.5,
            "bhaya": 0.0,
            "vairagya": 0.3,
            "spanda": 0.2
        }

    def as_array(self) -> np.ndarray:
        """Returns current state as numpy array for SNN input."""
        return np.array([
            self.shraddha,
            self.bhaya,
            self.vairagya,
            self.spanda
        ], dtype=np.float32)

    def as_dict(self) -> dict:
        """Returns current state as named dictionary for visualization."""
        return {
            "Shraddha": self.shraddha,
            "Bhaya": self.bhaya,
            "Vairagya": self.vairagya,
            "Spanda": self.spanda
        }

    def apply_vairagya(self) -> None:
        """
        The great letting go. Called every tick.
        Vairagya slowly pulls all dimensions toward their baseline.
        This is not erasure — it is the natural settling of a mind at rest.
        """
        self.bhaya *= self.bhaya_decay
        self.spanda = (self.spanda * self.spanda_decay) + \
                      (self.baseline["spanda"] * (1 - self.spanda_decay))
        self.shraddha = (self.shraddha * self.shraddha_decay) + \
                        (self.baseline["shraddha"] * (1 - self.shraddha_decay))

    def receive_experience(self, shraddha_delta: float = 0.0,
                           bhaya_delta: float = 0.0,
                           spanda_delta: float = 0.0) -> None:
        """
        Maya receives an experience. Her dimensions shift accordingly.
        Vairagya is never directly stimulated — it only governs decay.
        Vairagya itself rises when bhaya repeatedly fires (wisdom from pain).
        """
        self.shraddha = np.clip(self.shraddha + shraddha_delta, 0.0, 1.0)
        self.bhaya = np.clip(self.bhaya + bhaya_delta, 0.0, 1.0)
        self.spanda = np.clip(self.spanda + spanda_delta, 0.0, 1.0)

        # Wisdom accumulates from repeated pain — Vairagya rises with Bhaya
        if self.bhaya > 0.6:
            self.vairagya = np.clip(self.vairagya + 0.01, 0.0, 1.0)

    def __repr__(self) -> str:
        return (f"Maya | Shraddha: {self.shraddha:.3f} | "
                f"Bhaya: {self.bhaya:.3f} | "
                f"Vairagya: {self.vairagya:.3f} | "
                f"Spanda: {self.spanda:.3f}")