# --- [ MAYA CORE: CONFIG v0.4 ] ---
# 1920x1080 fullscreen. No guesswork. Every pixel accounted for.

# Window
W_WIDTH:  int = 1920
W_HEIGHT: int = 1080
FPS:      int = 60

# Layout — horizontal panels
MIND_PANEL_WIDTH:  int = 768   # 40% of 1920
NAV_PANEL_WIDTH:   int = 960   # 50% of 1920
SIDEBAR_WIDTH:     int = 192   # 10% of 1920

# Layout — vertical zones
HEADER_HEIGHT:     int = 40
BOTTOM_BAR_HEIGHT: int = 60
CONTENT_HEIGHT:    int = W_HEIGHT - HEADER_HEIGHT - BOTTOM_BAR_HEIGHT  # 980px

NODE_ZONE_HEIGHT:  int = int(CONTENT_HEIGHT * 0.60)   # 588px
WAVE_ZONE_HEIGHT:  int = CONTENT_HEIGHT - NODE_ZONE_HEIGHT              # 392px

# Derived Y positions
HEADER_Y:          int = 0
CONTENT_Y:         int = HEADER_HEIGHT                                   # 40
NODE_ZONE_Y:       int = CONTENT_Y                                       # 40
WAVE_ZONE_Y:       int = CONTENT_Y + NODE_ZONE_HEIGHT                   # 628
BOTTOM_BAR_Y:      int = W_HEIGHT - BOTTOM_BAR_HEIGHT                   # 1020

# Derived X positions
MIND_X:            int = 0
NAV_X:             int = MIND_PANEL_WIDTH                                # 768
SIDEBAR_X:         int = MIND_PANEL_WIDTH + NAV_PANEL_WIDTH              # 1728

# Colors — backgrounds
BACKGROUND         = (8,   8,  12)
HEADER_BG          = (12,  12,  18)
PANEL_COLOR        = (14,  14,  20)
PANEL_COLOR_ALT    = (11,  11,  16)
SIDEBAR_BG         = (10,  10,  15)
BOTTOM_BAR_COLOR   = (12,  12,  18)

# Colors — UI chrome
GRID_COLOR         = (18,  18,  26)
DIVIDER_COLOR      = (45,  45,  65)
SECTION_LABEL_COL  = (55,  55,  75)
TEXT_DIM           = (100, 100, 120)
TEXT_BRIGHT        = (180, 180, 200)

# Colors — dimensions
DIMENSION_COLORS = {
    "Shraddha": (100, 200, 255),
    "Bhaya":    (255,  80,  80),
    "Vairagya": (180, 130, 255),
    "Spanda":   (255, 220,  80),
}

# Colors — navigation
TARGET_COLOR       = (0,   255,  80)
TEACHER_COLOR      = (60,  160, 255)
MAYA_COLOR         = (255,  80,  80)
OBSTACLE_COLOR     = (50,   50,  60)
OBSTACLE_RING      = (80,   80, 100)
FOOTSTEP_TEACHER   = (30,   90, 160)
FOOTSTEP_MAYA      = (140,  30,  30)
PAIN_MEMORY_COLOR  = (255, 130,   0)

# --- [ LANGUAGE DUALITY ] ---
# Press L in Mindscape to toggle between Sanskrit and English
# Sanskrit = soul of the project
# English = accessible to all researchers

LABELS = {
    "sanskrit": {
        "trust":        "Shraddha",
        "fear":         "Bhaya",
        "wisdom":       "Vairagya",
        "aliveness":    "Spanda",
        "constellation":"Neural Constellation",
        "activity":     "Membrane Activity",
        "world":        "Maya's World",
        "controls":     "Controls",
        "spoke":        "Maya Said",
        "language_tag": "Lang: Sanskrit  [L]",
        "reset":        "Reset",
        "speak":        "Speak",
        "quit":         "Quit",
        "experiences": {
            "curiosity":     "Curiosity  (Jigyasa)",
            "joy":           "Joy  (Ananda)",
            "connection":    "Connection  (Sambandha)",
            "calm":          "Calm  (Shanti)",
            "pain":          "Pain  (Vedana)",
            "threat":        "Threat  (Bhaya-Utpatti)",
            "loneliness":    "Loneliness  (Ekata)",
            "understanding": "Understanding  (Bodha)",
        }
    },
    "english": {
        "trust":        "Trust",
        "fear":         "Fear",
        "wisdom":       "Wisdom",
        "aliveness":    "Aliveness",
        "constellation":"Neural Constellation",
        "activity":     "Neural Activity",
        "world":        "Navigation World",
        "controls":     "Controls",
        "spoke":        "Maya Said",
        "language_tag": "Lang: English  [L]",
        "reset":        "Reset",
        "speak":        "Speak",
        "quit":         "Quit",
        "experiences": {
            "curiosity":     "Curiosity",
            "joy":           "Joy",
            "connection":    "Connection",
            "calm":          "Calm",
            "pain":          "Pain",
            "threat":        "Threat",
            "loneliness":    "Loneliness",
            "understanding": "Understanding",
        }
    }
}