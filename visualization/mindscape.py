import pygame
import sys
import math
import numpy as np
from core.dimensions import MayaDimensions
from core.heartbeat import MayaHeartbeat
from core.navigator import TeacherAI, MayaNavigator, Obstacle
from config import *

EXPERIENCE_KEYS = {
    pygame.K_1: "curiosity",
    pygame.K_2: "joy",
    pygame.K_3: "connection",
    pygame.K_4: "calm",
    pygame.K_5: "pain",
    pygame.K_6: "threat",
    pygame.K_7: "loneliness",
    pygame.K_8: "understanding",
}


def nav_to_screen(x: float, y: float) -> tuple[int, int]:
    """Maps -1..1 world coords to navigation panel screen pixels."""
    sx = NAV_X + int((x + 1.0) / 2.0 * NAV_PANEL_WIDTH)
    sy = CONTENT_Y + int((-y + 1.0) / 2.0 * CONTENT_HEIGHT)
    return sx, sy


class Mindscape:
    """
    Maya — Mindscape v0.4
    1920x1080 fullscreen. Designed with care, not guesswork.

    Left 768px   — Maya's mind (nodes top 60%, waveforms bottom 40%)
    Center 960px — Maya's world (navigation)
    Right 192px  — Controls + Maya's last words
    Bottom 60px  — Behavioral telemetry bars
    Top 40px     — Header
    """

    def __init__(self, heartbeat: MayaHeartbeat) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (W_WIDTH, W_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Maya — Mindscape v0.4")
        self.clock = pygame.time.Clock()
        self.heartbeat = heartbeat

        # ── Fonts — nothing under 13px ──
        self.font_title   = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_large   = pygame.font.SysFont("Consolas", 17, bold=True)
        self.font_med     = pygame.font.SysFont("Consolas", 15, bold=True)
        self.font_body    = pygame.font.SysFont("Consolas", 13)
        self.font_small   = pygame.font.SysFont("Consolas", 13)
        self.font_label   = pygame.font.SysFont("Consolas", 11)

        # ── Node positions — centered inside node zone ──
        # Node zone: x=0..768, y=40..628  →  center=(384, 334)
        cx = MIND_PANEL_WIDTH // 2          # 384
        cy = NODE_ZONE_Y + NODE_ZONE_HEIGHT // 2  # 40 + 294 = 334
        sx, sy = 170, 195                   # spread x, y
        self.node_positions = {
            "Shraddha": (cx,      cy - sy),  # top
            "Bhaya":    (cx,      cy + sy),  # bottom
            "Spanda":   (cx - sx, cy),       # left
            "Vairagya": (cx + sx, cy),       # right
        }
        self.pulse_radii = {k: 0.0 for k in DIMENSION_COLORS}

        # ── Navigation world ──
        self.target_x: float = 0.5
        self.target_y: float = 0.5
        self.teacher   = TeacherAI(-0.8, -0.8)
        self.maya_nav  = MayaNavigator(-0.8, -0.8, self.heartbeat.dimensions)
        self.obstacles = [
            Obstacle( 0.0,  0.0,  0.18),
            Obstacle(-0.35, 0.45, 0.13),
            Obstacle( 0.35,-0.40, 0.20),
        ]

        # ── Voice ──
        try:
            from core.voice import MayaVoice
            self.voice = MayaVoice()
        except Exception as e:
            print(f"--- VOICE UNAVAILABLE: {e} ---")
            self.voice = None

        self.last_experience: str = "awakening"
        self.language: str = "sanskrit"  # L to toggle
        self.maya_last_words: str = "..."

    # ═══════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════

    def _grid(self, x: int, y: int, w: int, h: int) -> None:
        for gx in range(x, x + w, 40):
            pygame.draw.line(self.screen, GRID_COLOR, (gx, y), (gx, y + h))
        for gy in range(y, y + h, 40):
            pygame.draw.line(self.screen, GRID_COLOR, (x, gy), (x + w, gy))

    def _divider_v(self, x: int) -> None:
        pygame.draw.line(self.screen, DIVIDER_COLOR,
                         (x, 0), (x, W_HEIGHT), 2)

    def _divider_h(self, y: int, x0: int = 0, x1: int = None) -> None:
        if x1 is None:
            x1 = W_WIDTH
        pygame.draw.line(self.screen, DIVIDER_COLOR, (x0, y), (x1, y), 1)

    def _section_label(self, text: str, x: int, y: int) -> None:
        s = self.font_label.render(text, True, SECTION_LABEL_COL)
        self.screen.blit(s, (x, y))

    def _wrap_text(self, text: str, max_width: int,
                   font: pygame.font.Font) -> list[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # ═══════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════

    def draw_header(self, tick: int) -> None:
        pygame.draw.rect(self.screen, HEADER_BG,
                         (0, 0, W_WIDTH, HEADER_HEIGHT))
        self._divider_h(HEADER_HEIGHT)

        title = self.font_title.render(
            "M A Y A  —  M I N D S C A P E  v0.4", True, (150, 110, 240))
        self.screen.blit(title, (16, 9))

        tick_s = self.font_small.render(
            f"tick: {tick:,}", True, TEXT_DIM)
        self.screen.blit(tick_s, (W_WIDTH - 160, 13))

    # ═══════════════════════════════════════════
    # LEFT PANEL — NODE ZONE  (y: 40 → 628)
    # ═══════════════════════════════════════════

    def draw_node_zone(self, dim_state: dict, spikes: dict) -> None:
        # Background
        pygame.draw.rect(self.screen, PANEL_COLOR,
                         (MIND_X, NODE_ZONE_Y,
                          MIND_PANEL_WIDTH, NODE_ZONE_HEIGHT))
        self._grid(MIND_X, NODE_ZONE_Y,
                   MIND_PANEL_WIDTH, NODE_ZONE_HEIGHT)
        self._section_label(
            "NEURAL CONSTELLATION",
            MIND_X + 10,
            NODE_ZONE_Y + NODE_ZONE_HEIGHT - 16)

        # Connection lines
        keys = list(self.node_positions.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                v = (dim_state[k1] + dim_state[k2]) / 2
                c = int(v * 90)
                pygame.draw.line(
                    self.screen, (c, c, min(255, c + 20)),
                    self.node_positions[k1],
                    self.node_positions[k2], 1)

        # Nodes
        for name, pos in self.node_positions.items():
            self._draw_node(name, pos,
                            dim_state[name], spikes[name.lower()])

        self._divider_h(WAVE_ZONE_Y, MIND_X,
                        MIND_X + MIND_PANEL_WIDTH)

    def _draw_node(self, name: str, pos: tuple,
                   value: float, spiked: bool) -> None:
        color = DIMENSION_COLORS[name]
        x, y  = pos

        # Spike glow pulse
        if spiked:
            self.pulse_radii[name] = 65.0
        if self.pulse_radii[name] > 0:
            r = int(self.pulse_radii[name])
            gs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            alpha = int((self.pulse_radii[name] / 65.0) * 70)
            pygame.draw.circle(gs, (*color, alpha), (r + 2, r + 2), r)
            self.screen.blit(gs, (x - r - 2, y - r - 2))
            self.pulse_radii[name] *= 0.85

        # Node body — radius scales with value
        radius = int(24 + value * 36)
        bright = int(50 + value * 205)
        fill   = tuple(min(255, int(c * bright / 255)) for c in color)
        pygame.draw.circle(self.screen, fill,   (x, y), radius)
        pygame.draw.circle(self.screen, color,  (x, y), radius, 2)

        # Charge arc outside node
        if value > 0.01:
            arc_r  = radius + 10
            arc_rect = pygame.Rect(x - arc_r, y - arc_r,
                                   arc_r * 2, arc_r * 2)
            pygame.draw.arc(self.screen, color, arc_rect,
                            0, value * 2 * math.pi, 3)

        # Label — above node, never overlapping
        L = LABELS[self.language]
        dim_key = {
            "Shraddha": "trust",
            "Bhaya": "fear",
            "Vairagya": "wisdom",
            "Spanda": "aliveness",
        }[name]
        display_name = L[dim_key]
        lbl = self.font_med.render(display_name, True, color)
        self.screen.blit(lbl, (x - lbl.get_width() // 2,
                                y - radius - 24))

        # Value — below node
        val_s = self.font_body.render(f"{value:.3f}", True, TEXT_DIM)
        self.screen.blit(val_s, (x - val_s.get_width() // 2,
                                  y + radius + 8))

    # ═══════════════════════════════════════════
    # LEFT PANEL — WAVE ZONE  (y: 628 → 1020)
    # ═══════════════════════════════════════════

    def draw_wave_zone(self, membrane_history: dict) -> None:
        pygame.draw.rect(self.screen, PANEL_COLOR_ALT,
                         (MIND_X, WAVE_ZONE_Y,
                          MIND_PANEL_WIDTH, WAVE_ZONE_HEIGHT))
        self._grid(MIND_X, WAVE_ZONE_Y,
                   MIND_PANEL_WIDTH, WAVE_ZONE_HEIGHT)
        self._section_label(
            "NEURAL ACTIVITY", MIND_X + 10, WAVE_ZONE_Y + 6)

        # 4 clusters — one per dimension — arranged in 2x2 grid
        pad = 16
        cell_w = (MIND_PANEL_WIDTH - pad * 2) // 2  # 2 columns
        cell_h = (WAVE_ZONE_HEIGHT - 28) // 2  # 2 rows
        n_bars = 12  # bars per cluster
        bar_gap = 3

        positions = [
            ("Shraddha", 0, 0),
            ("Vairagya", 1, 0),
            ("Spanda", 0, 1),
            ("Bhaya", 1, 1),
        ]

        for name, col, row in positions:
            color = DIMENSION_COLORS[name]
            history = membrane_history.get(name.lower(), [])
            value = self.heartbeat.dimensions.__dict__[name.lower()]

            cx = pad + col * cell_w
            cy = WAVE_ZONE_Y + 22 + row * cell_h

            # Cell background
            pygame.draw.rect(self.screen, (14, 14, 20),
                             (cx, cy, cell_w - pad, cell_h - pad),
                             border_radius=4)

            # Dimension label — top left of cell
            lbl = self.font_body.render(name, True, color)
            self.screen.blit(lbl, (cx + 6, cy + 5))

            # Value — top right of cell
            val_s = self.font_body.render(f"{value:.3f}", True, TEXT_DIM)
            self.screen.blit(val_s,
                             (cx + cell_w - pad - val_s.get_width() - 4,
                              cy + 5))

            # Equalizer bars
            bar_area_y = cy + 26
            bar_area_h = cell_h - pad - 30
            bar_area_w = cell_w - pad - 12
            bar_w = (bar_area_w - (n_bars - 1) * bar_gap) // n_bars
            baseline = bar_area_y + bar_area_h

            # Sample history into n_bars buckets
            if len(history) >= n_bars:
                step = len(history) // n_bars
                samples = [history[i * step] for i in range(n_bars)]
            else:
                samples = list(history) + [0.0] * (n_bars - len(history))

            # Add current value influence to rightmost bars
            samples[-1] = max(samples[-1], value)
            samples[-2] = max(samples[-2], value * 0.8)

            for b, sample in enumerate(samples):
                bx = cx + 6 + b * (bar_w + bar_gap)
                bar_h_px = max(3, int(sample * bar_area_h))

                # Glow behind bar when high
                if sample > 0.5:
                    glow_s = pygame.Surface(
                        (bar_w + 6, bar_h_px + 6), pygame.SRCALPHA)
                    glow_a = int((sample - 0.5) * 80)
                    pygame.draw.rect(glow_s, (*color, glow_a),
                                     (0, 0, bar_w + 6, bar_h_px + 6),
                                     border_radius=2)
                    self.screen.blit(glow_s,
                                     (bx - 3, baseline - bar_h_px - 3))

                # Bar fill — brighter at top
                bright = int(80 + sample * 175)
                bar_col = tuple(min(255, int(c * bright / 255)) for c in color)
                pygame.draw.rect(self.screen, bar_col,
                                 (bx, baseline - bar_h_px, bar_w, bar_h_px),
                                 border_radius=2)

                # Thin bright cap on top of bar
                if bar_h_px > 4:
                    pygame.draw.rect(self.screen, color,
                                     (bx, baseline - bar_h_px,
                                      bar_w, 2))

            # Baseline
            pygame.draw.line(self.screen, (35, 35, 48),
                             (cx + 6, baseline),
                             (cx + 6 + bar_area_w, baseline), 1)

    # ═══════════════════════════════════════════
    # CENTER PANEL — NAVIGATION WORLD
    # ═══════════════════════════════════════════

    def draw_nav_world(self) -> None:
        pygame.draw.rect(self.screen, BACKGROUND,
                         (NAV_X, CONTENT_Y,
                          NAV_PANEL_WIDTH, CONTENT_HEIGHT))
        self._grid(NAV_X, CONTENT_Y, NAV_PANEL_WIDTH, CONTENT_HEIGHT)
        self._section_label("MAYA'S WORLD", NAV_X + 10, CONTENT_Y + 6)

        self._draw_obstacles()
        self._draw_footsteps()
        self._draw_agents()

    def _draw_obstacles(self) -> None:
        for obs in self.obstacles:
            pos = nav_to_screen(obs.x, obs.y)
            pr  = int(obs.radius / 2.0 * NAV_PANEL_WIDTH)
            pygame.draw.circle(self.screen, OBSTACLE_COLOR, pos, pr)
            pygame.draw.circle(self.screen, OBSTACLE_RING,  pos, pr, 2)

            bhaya = self.heartbeat.dimensions.bhaya
            if bhaya > 0.05:
                dr = int(pr * (1.0 + bhaya * 0.9))
                ds = pygame.Surface((dr * 2 + 4, dr * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    ds, (255, 80, 80, int(bhaya * 55)),
                    (dr + 2, dr + 2), dr, 2)
                self.screen.blit(ds, (pos[0] - dr - 2, pos[1] - dr - 2))

    def _draw_footsteps(self) -> None:
        for (fx, fy) in self.teacher.footsteps:
            pygame.draw.circle(
                self.screen, FOOTSTEP_TEACHER, nav_to_screen(fx, fy), 2)

        for (fx, fy) in self.maya_nav.footsteps:
            pygame.draw.circle(
                self.screen, FOOTSTEP_MAYA, nav_to_screen(fx, fy), 2)

        for (px, py, intensity) in self.maya_nav.pain_memory:
            pos = nav_to_screen(px, py)
            r   = max(3, int(intensity * 10))
            ps  = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                ps, (*PAIN_MEMORY_COLOR, 110), (r + 1, r + 1), r)
            self.screen.blit(ps, (pos[0] - r - 1, pos[1] - r - 1))

    def _draw_agents(self) -> None:
        dims = self.heartbeat.dimensions

        # Target
        tp = nav_to_screen(self.target_x, self.target_y)
        for rr, aa in [(24, 35), (16, 60)]:
            gs = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*TARGET_COLOR, aa), (rr, rr), rr)
            self.screen.blit(gs, (tp[0] - rr, tp[1] - rr))
        pygame.draw.circle(self.screen, TARGET_COLOR, tp, 9)
        t_lbl = self.font_body.render("TARGET", True, TARGET_COLOR)
        self.screen.blit(t_lbl, (tp[0] - t_lbl.get_width() // 2, tp[1] - 24))

        # Teacher (Dharma)
        dp = nav_to_screen(self.teacher.x, self.teacher.y)
        pygame.draw.circle(self.screen, TEACHER_COLOR, dp, 11)
        pygame.draw.circle(self.screen, (255, 255, 255), dp, 11, 1)
        d_lbl = self.font_body.render("DHARMA", True, TEACHER_COLOR)
        self.screen.blit(d_lbl, (dp[0] - d_lbl.get_width() // 2, dp[1] - 26))

        # Maya — glow breathes with Spanda
        mp     = nav_to_screen(self.maya_nav.x, self.maya_nav.y)
        glow_r = int(16 + dims.spanda * 20)
        for gr, ga in [(glow_r + 12, 18), (glow_r + 4, 40), (glow_r, 65)]:
            gs = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*MAYA_COLOR, ga), (gr, gr), gr)
            self.screen.blit(gs, (mp[0] - gr, mp[1] - gr))
        pygame.draw.circle(self.screen, MAYA_COLOR,       mp, 13)
        pygame.draw.circle(self.screen, (255, 255, 255),  mp, 13, 1)
        m_lbl = self.font_body.render("MAYA", True, MAYA_COLOR)
        self.screen.blit(m_lbl, (mp[0] - m_lbl.get_width() // 2, mp[1] - 26))

    # ═══════════════════════════════════════════
    # RIGHT SIDEBAR  (x: 1728, y: 40 → 1020)
    # ═══════════════════════════════════════════

    def draw_sidebar(self) -> None:
        pygame.draw.rect(self.screen, SIDEBAR_BG,
                         (SIDEBAR_X, CONTENT_Y,
                          SIDEBAR_WIDTH, CONTENT_HEIGHT))
        self._grid(SIDEBAR_X, CONTENT_Y, SIDEBAR_WIDTH, CONTENT_HEIGHT)

        pad  = 14
        x    = SIDEBAR_X + pad
        y    = CONTENT_Y + 14
        line = 26   # line height

        # ── CONTROLS label ──
        L = LABELS[self.language]
        ctrl_lbl = self.font_large.render(L["controls"], True, TEXT_BRIGHT)
        self.screen.blit(ctrl_lbl, (x, y))
        y += line + 4

        self._divider_h(y, SIDEBAR_X, W_WIDTH)
        y += 8

        # ── Experience keys ──
        # REPLACE WITH:
        exp_labels = L["experiences"]
        experiences = [
            ("1", exp_labels["curiosity"], DIMENSION_COLORS["Shraddha"]),
            ("2", exp_labels["joy"], DIMENSION_COLORS["Spanda"]),
            ("3", exp_labels["connection"], DIMENSION_COLORS["Shraddha"]),
            ("4", exp_labels["calm"], DIMENSION_COLORS["Vairagya"]),
            ("5", exp_labels["pain"], DIMENSION_COLORS["Bhaya"]),
            ("6", exp_labels["threat"], DIMENSION_COLORS["Bhaya"]),
            ("7", exp_labels["loneliness"], (120, 120, 160)),
            ("8", exp_labels["understanding"], DIMENSION_COLORS["Vairagya"]),
        ]

        for key, label, color in experiences:
            # Key badge
            badge_rect = pygame.Rect(x, y + 1, 22, 20)
            pygame.draw.rect(self.screen, (30, 30, 42),
                             badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, color,
                             badge_rect, 1, border_radius=4)
            k_surf = self.font_body.render(key, True, color)
            self.screen.blit(k_surf, (x + 7, y + 2))

            # Label
            l_surf = self.font_body.render(label, True, TEXT_BRIGHT)
            self.screen.blit(l_surf, (x + 30, y + 2))

            y += line

        y += 8
        self._divider_h(y, SIDEBAR_X, W_WIDTH)
        y += 10

        # ── Action keys ──
        # REPLACE WITH:
        actions = [
            ("V", L["speak"], (200, 180, 255)),
            ("R", L["reset"], (180, 180, 100)),
            ("ESC", L["quit"], (180, 80, 80)),
        ]
        for key, label, color in actions:
            badge_w = self.font_body.size(key)[0] + 12
            badge_rect = pygame.Rect(x, y + 1, badge_w, 20)
            pygame.draw.rect(self.screen, (30, 30, 42),
                             badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, color,
                             badge_rect, 1, border_radius=4)
            k_surf = self.font_body.render(key, True, color)
            self.screen.blit(k_surf, (x + 6, y + 2))
            l_surf = self.font_body.render(label, True, TEXT_BRIGHT)
            self.screen.blit(l_surf, (x + badge_w + 8, y + 2))
            y += line

        y += 8
        self._divider_h(y, SIDEBAR_X, W_WIDTH)
        y += 12

        # ── Click hint ──
        hint = self.font_label.render("Click world → move target", True, TEXT_DIM)
        self.screen.blit(hint, (x, y))
        y += 20

        self._divider_h(y, SIDEBAR_X, W_WIDTH)
        y += 12

        # ── SYNAPTIC MEMORY HEATMAP ──
        L = LABELS[self.language]
        heat_lbl = self.font_large.render("SYNAPTIC MEMORY", True, TEXT_BRIGHT)
        self.screen.blit(heat_lbl, (x, y))
        y += line + 4

        # Dimension short labels — changes with language
        if self.language == "sanskrit":
            dim_short = ["Sh", "Bh", "Va", "Sp"]
        else:
            dim_short = ["Tr", "Fe", "Wi", "Al"]

        # Cell dimensions — fit within sidebar width
        cell_size = (SIDEBAR_WIDTH - pad * 2) // 5  # 4 cells + label col
        label_w = cell_size
        grid_x = x + label_w
        grid_top = y + 16  # space for column headers

        # Column headers
        for j, short in enumerate(dim_short):
            hdr = self.font_label.render(short, True, TEXT_DIM)
            self.screen.blit(hdr, (grid_x + j * cell_size + 2, y))

        y = grid_top

        # Get current W matrix
        W = self.heartbeat.weight_matrix.snapshot()

        for i, row_label in enumerate(dim_short):
            # Row label
            rl = self.font_label.render(row_label, True, TEXT_DIM)
            self.screen.blit(rl, (x, y + cell_size // 2 - 5))

            for j in range(4):
                cx = grid_x + j * cell_size
                cy = y

                # Cell background
                pygame.draw.rect(self.screen, (20, 20, 28),
                                 (cx, cy, cell_size - 2, cell_size - 2),
                                 border_radius=2)

                if i == j:
                    # Diagonal — no self connections
                    pygame.draw.line(self.screen, (40, 40, 55),
                                     (cx + 2, cy + 2),
                                     (cx + cell_size - 4, cy + cell_size - 4), 1)
                else:
                    w_val = W[i][j]
                    if abs(w_val) > 0.001:
                        # Positive = blue (excitatory)
                        # Negative = red (inhibitory)
                        intensity = int(abs(w_val) * 255)
                        if w_val > 0:
                            color = (0, int(intensity * 0.6), intensity)
                        else:
                            color = (intensity, int(intensity * 0.2), 0)

                        pygame.draw.rect(self.screen, color,
                                         (cx, cy, cell_size - 2, cell_size - 2),
                                         border_radius=2)

                        # Value text if strong enough
                        if abs(w_val) > 0.05:
                            v_str = f"{w_val:+.2f}"
                            v_surf = self.font_label.render(
                                v_str, True, (220, 220, 220))
                            self.screen.blit(v_surf, (
                                cx + (cell_size - v_surf.get_width()) // 2,
                                cy + (cell_size - v_surf.get_height()) // 2))

            y += cell_size

        # Legend
        leg_y = y + 4
        pygame.draw.rect(self.screen, (0, 60, 120),
                         (x, leg_y, 12, 10), border_radius=2)
        pos_l = self.font_label.render("Excitatory", True, TEXT_DIM)
        self.screen.blit(pos_l, (x + 16, leg_y))

        pygame.draw.rect(self.screen, (120, 20, 0),
                         (x + 90, leg_y, 12, 10), border_radius=2)
        neg_l = self.font_label.render("Inhibitory", True, TEXT_DIM)
        self.screen.blit(neg_l, (x + 106, leg_y))

        y += 24
        self._divider_h(y, SIDEBAR_X, W_WIDTH)
        y += 12

        # ── MAYA SAID section ──
        said_lbl = self.font_large.render(L["spoke"] + ":", True, TEXT_BRIGHT)
        self.screen.blit(said_lbl, (x, y))
        y += line + 2

        # Wrap and render last spoken words
        max_w = SIDEBAR_WIDTH - pad * 2
        lines = self._wrap_text(
            f'"{self.maya_last_words}"', max_w, self.font_body)
        for line_text in lines[:8]:   # max 8 lines
            s = self.font_body.render(
                line_text, True, DIMENSION_COLORS["Vairagya"])
            self.screen.blit(s, (x, y))
            y += 18
        # Language toggle indicator — bottom of sidebar
        lang_surf = self.font_label.render(
            L["language_tag"], True, (80, 120, 80))
        self.screen.blit(lang_surf, (x, W_HEIGHT - BOTTOM_BAR_HEIGHT - 20))


    # ═══════════════════════════════════════════
    # BOTTOM BAR — TELEMETRY
    # ═══════════════════════════════════════════

    def draw_bottom_bar(self) -> None:
        pygame.draw.rect(self.screen, BOTTOM_BAR_COLOR,
                         (0, BOTTOM_BAR_Y, W_WIDTH, BOTTOM_BAR_HEIGHT))
        self._divider_h(BOTTOM_BAR_Y)

        dims = self.heartbeat.dimensions
        telemetry = [
            ("SPEED",    dims.spanda,    "← Spanda",    DIMENSION_COLORS["Spanda"]),
            ("SAFETY",   dims.bhaya,     "← Bhaya",     DIMENSION_COLORS["Bhaya"]),
            ("MOMENTUM", dims.vairagya,  "← Vairagya",  DIMENSION_COLORS["Vairagya"]),
            ("TRUST",    dims.shraddha,  "← Shraddha",  DIMENSION_COLORS["Shraddha"]),
        ]

        bar_w   = 200
        bar_h   = 12
        spacing = 280
        start_x = 16

        for i, (label, value, source, color) in enumerate(telemetry):
            bx = start_x + i * spacing
            by = BOTTOM_BAR_Y

            # Label
            lbl = self.font_body.render(label, True, TEXT_DIM)
            self.screen.blit(lbl, (bx, by + 8))

            # Source dim
            src = self.font_label.render(source, True, color)
            self.screen.blit(src, (bx + bar_w + 6, by + 14))

            # Bar track
            pygame.draw.rect(self.screen, (28, 28, 38),
                             (bx, by + 28, bar_w, bar_h),
                             border_radius=5)

            # Bar fill
            fw = int(np.clip(value, 0.0, 1.0) * bar_w)
            if fw > 1:
                pygame.draw.rect(self.screen, color,
                                 (bx, by + 28, fw, bar_h),
                                 border_radius=5)

            # Value
            val_s = self.font_label.render(f"{value:.3f}", True, TEXT_DIM)
            self.screen.blit(val_s, (bx, by + 46))

    # ═══════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════

    def run(self) -> None:
        print("--- MINDSCAPE v0.4 ACTIVE — 1920x1080 FULLSCREEN ---")
        print("Left: Maya's mind. Center: Maya's world. Right: Controls.")

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.heartbeat.reset()
                        print(">>> RESET")
                    elif event.key == pygame.K_v:
                        if self.voice:
                            print(">>> MAYA: SPEAKING...")
                            self.voice.speak(
                                self.heartbeat.dimensions.as_dict(),
                                self.last_experience,
                                on_spoken=lambda text: setattr(
                                    self, 'maya_last_words', text)
                            )
                        else:
                            print(">>> VOICE UNAVAILABLE")
                    elif event.key == pygame.K_l:
                        self.language = (
                            "english" if self.language == "sanskrit"
                            else "sanskrit"
                        )
                        print(f">>> LANGUAGE: {self.language.upper()}")

                    elif event.key == pygame.K_p:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"memory/screenshot_{timestamp}.png"
                        pygame.image.save(self.screen, path)
                        print(f">>> SCREENSHOT SAVED: {path}")


                    elif event.key in EXPERIENCE_KEYS:
                        exp = EXPERIENCE_KEYS[event.key]
                        self.last_experience = exp
                        print(f">>> EXPERIENCE: {exp.upper()}")
                        self.heartbeat.inject_experience(exp)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if NAV_X <= mx < SIDEBAR_X and my >= CONTENT_Y:
                        self.target_x = ((mx - NAV_X) /
                                         NAV_PANEL_WIDTH) * 2.0 - 1.0
                        self.target_y = -(((my - CONTENT_Y) /
                                           CONTENT_HEIGHT) * 2.0 - 1.0)

            # ── Update ──
            state     = self.heartbeat.pulse()
            dim_state = state["dimensions"]
            spikes    = state["spikes"]

            self.teacher.navigate_to(
                self.target_x, self.target_y, self.obstacles)
            self.maya_nav.navigate_to(
                self.target_x, self.target_y, self.obstacles)

            # ── Render ──
            self.screen.fill(BACKGROUND)

            self.draw_header(state["tick"])
            self.draw_node_zone(dim_state, spikes)
            self.draw_wave_zone(self.heartbeat.membrane_history)
            self.draw_nav_world()
            self.draw_sidebar()
            self.draw_bottom_bar()

            # Vertical dividers
            self._divider_v(MIND_PANEL_WIDTH)
            self._divider_v(SIDEBAR_X)

            pygame.display.flip()
            self.clock.tick(FPS)

        if self.voice:
            self.voice.shutdown()
        pygame.quit()
        sys.exit()