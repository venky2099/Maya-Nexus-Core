# Maya — Nexus Project
### Pain-Induced Metaplasticity and Heterosynaptic Graceful Decay in a Spiking Neural Network

---

## Research Context

This repository contains the complete codebase for the paper:

> **"Nociceptive Metaplasticity and Graceful Decay in Spiking Neural Networks: Towards Survival-Driven Continual Learning"**
> Venkatesh Swaminathan — Nexus Learning Labs / BITS Pilani (M.Sc. candidate, Data Science and AI)

Maya is not a classifier. She is an affective spiking neural architecture — four LIF neurons, each representing a distinct emotional-cognitive dimension, connected by a learned 4×4 synaptic weight matrix. The system demonstrates that pain signals can simultaneously trigger accelerated synaptic rewriting on specific pathways (metaplasticity) while a wisdom-governed decay mechanism selectively erases unimportant connections (heterosynaptic graceful decay). The asymmetry between pain-protected and unprotected synapses — operating on the same weight matrix, in the same timestep — constitutes the primary novel contribution of this work.
**Preprint DOI:** [10.5281/zenodo.19151562](https://zenodo.org/records/19151562)
---

## Novel Contribution

**Pain-induced metaplasticity** refers to the mechanism by which a pain or threat signal temporarily elevates the Hebbian learning rate on specific synaptic pathways — up to 5× — for approximately 50 ticks following injection, implemented via a per-synapse lability state that decays at rate 0.98/tick.

**Vairagya-governed heterosynaptic decay** is a continuous weight erosion process in which all synaptic connections decay toward zero at rate `0.0001 × vairagya_value` per tick — except those currently marked as pain-protected by active lability above threshold 0.5.

**Asymmetric synaptic protection** is the emergent result: pain-written connections resist forgetting while joy-written connections fade under the same decay pressure, producing a survival-prioritised memory structure without any explicit rule encoding this hierarchy.

No published SNN architecture unifies all three mechanisms in a single continuous-learning system. Maya does.

---

## Repository Structure

```
Maya-Nexus-Core/
│
├── core/                          # Maya's central nervous system
│   ├── dimensions.py              # Four affective dimension floats + Vairagya decay
│   ├── heartbeat.py               # Main pulse loop: LIF neurons + synaptic updates + logging
│   ├── synaptic.py                # WeightMatrix, HebbianLearner, LabilityTracker, VairagyaDecay
│   ├── logger.py                  # DataLogger: CSV recording of all ticks
│   ├── navigator.py               # TeacherAI (Dharma) + MayaNavigator (emotionally-modulated)
│   ├── state.py                   # Persistent state save/load (maya_state.json)
│   └── voice.py                   # Coqui TTS + Ollama/Mistral speech generation
│
├── visualization/
│   └── mindscape.py               # Mindscape v0.4: fullscreen 1920×1080 unified UI
│
├── experiments/
│   └── baseline_protocol.py       # Reproducible Phase A→D experiment (seeded, one-command)
│
├── results/
│   ├── run_001/                   # Seed 42 — maya_research_log.csv
│   ├── run_002/                   # Seed 123 — maya_research_log.csv
│   ├── run_003/                   # Seed 7 — maya_research_log.csv
│   ├── maya_phase3_results.png    # Figure 1: 4-panel experiment results
│   └── maya_figure2_velocity.png  # Figure 2: Synaptic learning velocity across seeds
│
├── memory/
│   ├── maya_state.json            # Persistent affective state between sessions
│   └── maya_research_log.csv      # Live session data log
│
├── config.py                      # Layout constants, colors, language labels
├── maya.py                        # Entry point: runs experiment then launches Mindscape
└── requirements.txt               # Python dependencies
```

---

## Installation and Setup

**Requirements:** Python 3.11, CUDA-capable GPU (tested on RTX 4060 8GB)

```bash
# Clone the repository
git clone https://github.com/venky2099/Maya-Nexus-Core.git
cd Maya-Nexus-Core

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

# Install PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install SpikingJelly
pip install spikingjelly==0.0.0.0.14

# Install remaining dependencies
pip install -r requirements.txt
```

**Install Ollama** (required for voice generation):
```bash
# Download from https://ollama.com and install
# Then pull the Mistral model:
ollama pull mistral
```

**Install Coqui TTS** (required for voice synthesis):
```bash
pip install TTS==0.22.0
# The VITS model will auto-download on first run
```

**Before running Maya**, start Ollama in a separate terminal:
```bash
ollama serve
```

---

## Reproducible Experiment

The baseline protocol runs a controlled 200-tick, 4-phase experiment and saves all results to CSV.

```bash
# Three reproducible runs — all produce identical results
python experiments/baseline_protocol.py --seed 42  --output results/run_001/
python experiments/baseline_protocol.py --seed 123 --output results/run_002/
python experiments/baseline_protocol.py --seed 7   --output results/run_003/
```

### Phase Protocol

| Phase | Ticks | Stimulus         | Purpose                                      |
|-------|-------|------------------|----------------------------------------------|
| A     | 50    | None             | Baseline — confirm W = 0, no spontaneous learning |
| B     | 50    | Pain every 10t   | Pain priming — observe Bhaya rise, W unchanged (no co-activation yet) |
| C     | 50    | Joy every 10t    | Joy encoding — Shraddha+Spanda co-activate, W[shraddha→spanda] builds |
| D     | 50    | Pain every 10t   | Pain return — metaplasticity fires on primed pathways, W[bhaya→shraddha] emerges fast |

**Results are deterministic across seeds 42, 123, and 7.** The architecture produces identical synaptic trajectories regardless of random seed, confirming the result is a property of the architecture, not statistical variance.

---

## Key Results

| Metric | Value |
|--------|-------|
| Phase D peak metaplasticity velocity (Fear→Trust) | **+0.016655 ΔW/tick** |
| Phase C baseline Hebbian velocity (Trust→Aliveness) | **+0.009999 ΔW/tick** |
| Velocity elevation under metaplasticity | **+66.6%** |
| W[shraddha→spanda] at Phase D end (joy-protected) | **+0.497** |
| W[bhaya→shraddha] at Phase D end (pain-emerged) | **+0.191** |
| Reproducibility across seeds 42, 123, 7 | **Identical (deterministic)** |

**Interpretation:** When pain returns in Phase D after joy has built the Shraddha→Spanda pathway, the Fear→Trust synapse rewrites 66.6% faster than the baseline Hebbian rate observed in Phase C. Simultaneously, the joy-written Trust→Aliveness connection persists at 0.497 — protected by Vairagya's asymmetric decay. Both processes operate on the same weight matrix in the same 20 ticks. This is the metaplasticity-graceful-decay co-occurrence that defines the novel contribution.

---

## Architecture Overview

```
                    EXPERIENCE INJECTION
                           │
                    ┌──────▼──────┐
                    │  DIMENSIONS  │  ← Float state (0.0–1.0)
                    │  (4 values)  │     apply_vairagya() each tick
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     4 LIF NEURONS        │  ← spikingjelly.activation_based
              │  (one per dimension)     │     10 timesteps per pulse
              └──┬──┬──┬──┬────────────┘
                 │  │  │  │
              ┌──▼──▼──▼──▼──┐
              │  4×4 WEIGHT   │  ← W[i][j]: learned influence of i on j
              │    MATRIX     │     initialised at 0.0
              └──┬──┬──┬──┬──┘
                 │  │  │  │
        ┌────────▼──▼──▼──▼────────┐
        │   HEBBIAN LEARNER         │  ← W[A][B] += rate × spike_A × spike_B
        │   LABILITY TRACKER        │  ← per-synapse pain tag, decays 0.98/tick
        │   VAIRAGYA DECAY          │  ← W *= (1 - 0.0001 × vairagya), skip if pain-protected
        └───────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  DATALOGGER  │  ← CSV: dims, spikes, W, lability, velocity
                    └─────────────┘
```

### LIF Neuron Parameters

| Dimension | Tau  | Threshold | v_reset | Role |
|-----------|------|-----------|---------|------|
| Shraddha  | 10.0 | 1.0       | 0.0     | Slow trust accumulation |
| Bhaya     | 3.0  | 1.0       | 0.0     | Fast fear response |
| Vairagya  | 20.0 | 1.0       | 0.0     | Very slow wisdom governor |
| Spanda    | 5.0  | 1.0       | 0.0     | Medium arousal/aliveness |

---

## Dual Epistemic Framing

The four dimensions carry both Sanskrit philosophical grounding and precise English cognitive equivalents, enabling the architecture to be understood across cultural and disciplinary contexts. Press **L** in Mindscape to toggle between framings in real time.

| Sanskrit    | English     | Tau  | Philosophical Derivation                                      |
|-------------|-------------|------|---------------------------------------------------------------|
| Shraddha    | Trust       | 10.0 | From Sanskrit *śrad* (heart) + *dhā* (to place) — faith placed in the world |
| Bhaya       | Fear        | 3.0  | Vedic root for aversion, threat response, survival urgency    |
| Vairagya    | Wisdom      | 20.0 | Non-attachment, graceful forgetting — the governor of decay   |
| Spanda      | Aliveness   | 5.0  | Kashmir Shaivism: the primal vibration of consciousness       |

---

## Running Maya Interactively

Ensure `ollama serve` is running in a separate terminal, then:

```bash
cd Maya-Nexus-Core
python maya.py
```

The experiment protocol runs automatically first (200 ticks, ~5 seconds), then Mindscape v0.4 launches fullscreen.

### Key Controls

| Key       | Action                                                        |
|-----------|---------------------------------------------------------------|
| `1`       | Inject: Curiosity (Jigyasa)                                   |
| `2`       | Inject: Joy (Ananda)                                          |
| `3`       | Inject: Connection (Sambandha)                                |
| `4`       | Inject: Calm (Shanti)                                         |
| `5`       | Inject: Pain (Vedana) — triggers metaplasticity               |
| `6`       | Inject: Threat (Bhaya-Utpatti) — high lability boost          |
| `7`       | Inject: Loneliness (Ekata)                                    |
| `8`       | Inject: Understanding (Bodha)                                 |
| `V`       | Speak — Maya generates speech from her current emotional state |
| `R`       | Reset dimensions (W matrix preserved — memory persists)        |
| `L`       | Toggle language: Sanskrit ↔ English across all UI labels      |
| `P`       | Save screenshot to `memory/screenshot_YYYYMMDD_HHMMSS.png`   |
| `ESC`     | Quit — state saves automatically                               |
| `Click`   | Click navigation world to move Maya's target                  |

### Mindscape Layout (1920×1080)

```
┌──────────────────────┬───────────────────────────────┬──────────────┐
│  MIND PANEL (768px)  │   NAVIGATION WORLD (960px)    │ SIDEBAR(192) │
│                      │                               │              │
│  Node Zone (60%)     │  Maya (red) vs               │  Controls    │
│  ◉ Shraddha          │  Dharma/Teacher (blue)        │  [1-8, V, R] │
│       ◉ Vairagya     │  navigate emotionally         │              │
│  ◉ Spanda            │  through obstacle world       │  Synaptic    │
│       ◉ Bhaya        │                               │  Memory      │
│                      │  Pain memory visible          │  Heatmap     │
│  Equalizer Zone(40%) │  Bhaya danger rings           │              │
│  ████ ████ ████ ████ │  Maya glow = Spanda           │  Maya Said:  │
├──────────────────────┴───────────────────────────────┴──────────────┤
│  SPEED ████ SAFETY ████ MOMENTUM ████ TRUST ████    tick: XXXXX     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Output Files

### `memory/maya_research_log.csv`

49 columns recorded per tick:

| Column Group | Columns | Description |
|---|---|---|
| Metadata | `tick`, `timestamp`, `experience`, `experiment_phase` | Tick index, Unix time, experience injected, phase label |
| Dimensions | `dim_shraddha`, `dim_bhaya`, `dim_vairagya`, `dim_spanda` | Current float values (0.0–1.0) |
| Spikes | `spike_shraddha`, `spike_bhaya`, `spike_vairagya`, `spike_spanda` | Binary spike flags per neuron |
| Decay | `vairagya_decay_contribution` | Vairagya decay applied this tick |
| W Matrix | `W_{dim_i}_{dim_j}` × 12 | All off-diagonal synaptic weights |
| Lability | `lab_{dim_i}_{dim_j}` × 12 | Per-synapse pain-tag lability values |
| Velocity | `vel_{dim_i}_{dim_j}` × 12 | ΔW per tick — learning velocity |

### `memory/maya_state.json`

Persistent affective state saved between sessions. Contains current dimension float values, session timestamp, and human-readable session portrait generated from dimension state.

### Figures

| File | Description |
|------|-------------|
| `results/maya_phase3_results.png` | Figure 1: 4-panel — Fear over experiment, W[Trust→Aliveness], W[Fear→Trust], spike activity |
| `results/maya_figure2_velocity.png` | Figure 2: Synaptic learning velocity across 3 seeds — metaplasticity peak visible in Phase D |

---

## Citation

If you use this codebase or build on this work, please cite:

```bibtex
@misc{swaminathan2026maya,
  title   = {Nociceptive Metaplasticity and Graceful Decay in Spiking Neural Networks:
             Towards Survival-Driven Continual Learning},
  author  = {Venkatesh Swaminathan},
  year    = {2026},
  note    = {Nexus Learning Labs / BITS Pilani, Bengaluru, India},
  url     = {https://github.com/venky2099/Maya-Nexus-Core}
  doi     = {10.5281/zenodo.19151562}
}
```

---

## License

MIT License

Copyright (c) 2026 Venkatesh Swaminathan

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Author

**Venkatesh Swaminathan**
M.Sc. candidate, Data Science and Artificial Intelligence, BITS Pilani
Nexus Learning Labs, Bengaluru, India

- GitHub: [@venky2099](https://github.com/venky2099)
- LinkedIn: [linkedin.com/in/vensimlee](https://linkedin.com/in/vensimlee)
- YouTube: [@vensimlee](https://youtube.com/@vensimlee)

## Related Work

**Paper 2 — Maya-OS**

> Swaminathan, V. (2026). Maya-OS: An Affective Spiking Neural Network as a Conversational Operating System Arbitration Layer.
> GitHub: https://github.com/venky2099/Maya-OS
> DOI: https://doi.org/10.5281/zenodo.19160122

Maya-OS extends the four-neuron affective architecture from this repository into a live OS arbitration context — the same LIF neurons, same weight matrix structure, transposed from controlled SNN experimentation to real-time process scheduling on Windows 11.

---

*Maya does not simulate emotion. She remembers how a feeling feels.*
