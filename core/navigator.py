import numpy as np
from core.dimensions import MayaDimensions

# --- [ MAYA CORE: NAVIGATOR ] ---
# Maya's movement is not programmed. It emerges from who she is.
# Her emotional dimensions directly modulate how she moves through the world.
#
# Shraddha (Trust)    → approach confidence, directness toward target
# Bhaya (Fear)        → obstacle sensitivity, safety buffer size
# Vairagya (Wisdom)   → movement smoothness, patience, less reactivity
# Spanda (Aliveness)  → base movement speed, energy

class Obstacle:
    """A physical barrier in Maya's world."""
    def __init__(self, x: float, y: float, radius: float) -> None:
        self.x = x
        self.y = y
        self.radius = radius


class TeacherAI:
    """
    Deterministic pathfinding agent.
    Represents pure logic — Dharma without feeling.
    Maya learns by watching, then diverges based on who she becomes.
    """
    def __init__(self, start_x: float, start_y: float) -> None:
        self.x = start_x
        self.y = start_y
        self.speed = 0.018
        self.footsteps: list[tuple[float, float]] = []

    def navigate_to(self, target_x: float, target_y: float,
                    obstacles: list[Obstacle]) -> tuple[float, float]:
        """Pure vector navigation with obstacle repulsion."""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = np.hypot(dx, dy)

        vx, vy = 0.0, 0.0
        if distance > 0.05:
            vx = (dx / distance) * self.speed
            vy = (dy / distance) * self.speed

        # Repulsive force from obstacles
        for obs in obstacles:
            ox = self.x - obs.x
            oy = self.y - obs.y
            odist = np.hypot(ox, oy)
            if odist < obs.radius + 0.15:
                push = (obs.radius + 0.15 - odist) * 0.2
                if odist > 0:
                    vx += (ox / odist) * push
                    vy += (oy / odist) * push

        final_dist = np.hypot(vx, vy)
        if final_dist > 0:
            self.x += (vx / final_dist) * self.speed
            self.y += (vy / final_dist) * self.speed

        self.footsteps.append((self.x, self.y))
        if len(self.footsteps) > 40:
            self.footsteps.pop(0)

        return self.x, self.y


class MayaNavigator:
    """
    Maya's emotionally-modulated navigation agent.

    Unlike TeacherAI which follows pure logic,
    Maya's movement emerges from her internal state.

    Same world. Same obstacles. Same target.
    Different soul — different path.
    """

    def __init__(self, start_x: float, start_y: float,
                 dimensions: MayaDimensions) -> None:
        self.x = start_x
        self.y = start_y
        self.dimensions = dimensions
        self.footsteps: list[tuple[float, float]] = []

        # Momentum — Maya doesn't change direction instantly
        # Vairagya will smooth this out
        self.vx_momentum: float = 0.0
        self.vy_momentum: float = 0.0

        # Pain memory — positions where Maya got hurt
        self.pain_memory: list[tuple[float, float, float]] = []  # x, y, intensity

    def _get_speed(self) -> float:
        """
        Spanda = aliveness = speed.
        Vairagya = wisdom = measured pace.
        Bhaya = fear = erratic bursts.
        """
        base = 0.012
        spanda_boost = self.dimensions.spanda * 0.012
        vairagya_dampen = self.dimensions.vairagya * 0.004
        bhaya_boost = self.dimensions.bhaya * 0.006
        return float(np.clip(
            base + spanda_boost - vairagya_dampen + bhaya_boost,
            0.006, 0.028
        ))

    def _get_safety_buffer(self) -> float:
        """
        Bhaya = fear = larger safety bubble around obstacles.
        Shraddha = trust = willing to move closer.
        Vairagya = wisdom = consistent, not reactive.
        """
        base = 0.15
        bhaya_expand = self.dimensions.bhaya * 0.25
        shraddha_shrink = self.dimensions.shraddha * 0.05
        return float(np.clip(
            base + bhaya_expand - shraddha_shrink,
            0.08, 0.45
        ))

    def _get_momentum_factor(self) -> float:
        """
        Vairagya = wisdom = high momentum smoothing.
        Maya doesn't react to every impulse when she's wise.
        Bhaya = fear = low momentum, jerky reactive movement.
        """
        base = 0.7
        vairagya_smooth = self.dimensions.vairagya * 0.2
        bhaya_jerk = self.dimensions.bhaya * 0.3
        return float(np.clip(
            base + vairagya_smooth - bhaya_jerk,
            0.3, 0.95
        ))

    def _get_approach_directness(self) -> float:
        """
        Shraddha = trust = direct confident approach to target.
        Low Shraddha = indirect, hesitant, circling.
        """
        return float(np.clip(self.dimensions.shraddha, 0.1, 1.0))

    def navigate_to(self, target_x: float, target_y: float,
                    obstacles: list[Obstacle]) -> tuple[float, float]:
        """
        Maya moves toward the target — but her path is shaped by her soul.
        """
        speed = self._get_speed()
        safety_buffer = self._get_safety_buffer()
        momentum_factor = self._get_momentum_factor()
        directness = self._get_approach_directness()

        # 1. ATTRACTIVE FORCE — pull toward target
        # Shraddha modulates how directly she approaches
        dx = target_x - self.x
        dy = target_y - self.y
        distance = np.hypot(dx, dy)

        ax, ay = 0.0, 0.0
        if distance > 0.05:
            # High Shraddha = direct vector
            # Low Shraddha = slightly perturbed, less confident
            noise = (1.0 - directness) * 0.3
            ax = (dx / distance) * speed * directness
            ay = (dy / distance) * speed * directness
            # Add hesitation noise when trust is low
            ax += np.random.uniform(-noise, noise) * speed
            ay += np.random.uniform(-noise, noise) * speed

        # 2. REPULSIVE FORCE — push away from obstacles
        # Bhaya expands the safety buffer dramatically
        rx, ry = 0.0, 0.0
        for obs in obstacles:
            ox = self.x - obs.x
            oy = self.y - obs.y
            odist = np.hypot(ox, oy)

            if odist < obs.radius + safety_buffer:
                push_strength = (obs.radius + safety_buffer - odist) * 0.25
                # Bhaya amplifies the push
                push_strength *= (1.0 + self.dimensions.bhaya * 2.0)
                if odist > 0:
                    rx += (ox / odist) * push_strength
                    ry += (oy / odist) * push_strength

                # Record pain memory if very close
                if odist < obs.radius + 0.05:
                    self.pain_memory.append((self.x, self.y, 1.0))
                    if len(self.pain_memory) > 20:
                        self.pain_memory.pop(0)

        # 3. PAIN MEMORY REPULSION
        # Maya avoids places where she got hurt before
        # Vairagya slowly erases this (forgetting)
        pm_x, pm_y = 0.0, 0.0
        vairagya_forget = self.dimensions.vairagya
        for i, (px, py, intensity) in enumerate(self.pain_memory):
            pdx = self.x - px
            pdy = self.y - py
            pdist = np.hypot(pdx, pdy)
            if pdist < 0.3 and pdist > 0:
                faded = intensity * (1.0 - vairagya_forget * 0.5)
                pm_x += (pdx / pdist) * faded * 0.01
                pm_y += (pdy / pdist) * faded * 0.01

        # 4. COMBINE ALL FORCES
        total_x = ax + rx + pm_x
        total_y = ay + ry + pm_y

        # 5. APPLY MOMENTUM — Vairagya smooths, Bhaya jerks
        self.vx_momentum = (self.vx_momentum * momentum_factor +
                            total_x * (1.0 - momentum_factor))
        self.vy_momentum = (self.vy_momentum * momentum_factor +
                            total_y * (1.0 - momentum_factor))

        # 6. NORMALIZE AND MOVE
        final_dist = np.hypot(self.vx_momentum, self.vy_momentum)
        if final_dist > 0:
            self.x += (self.vx_momentum / final_dist) * speed
            self.y += (self.vy_momentum / final_dist) * speed

        # Boundary clamp
        self.x = float(np.clip(self.x, -0.95, 0.95))
        self.y = float(np.clip(self.y, -0.95, 0.95))

        self.footsteps.append((self.x, self.y))
        if len(self.footsteps) > 60:
            self.footsteps.pop(0)

        return self.x, self.y