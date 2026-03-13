# SimulAI
**Where Your Digital Creatures Develop Attitude.**

SimulAI is a tiny artificial world where **Simulites**—your digital creatures—wander, learn, and develop personality.
Built to be fun, hackable, and easy to extend.

---

## ✨ Features (v0.0.1)
- Minimal grid world with time steps
- **Simulites** with energy + mood
- Simple wandering behavior with “attitude” logs
- Text-mode ASCII renderer
- CLI: `simulai demo`

- **Food resources** (F on the grid) restore energy when eaten
- **Traits** (curiosity, sociability) affect wandering & interactions
- **Simple social interactions** when Simulites meet

## 🚀 Run locally
```bash
# clone and install
git clone https://github.com/YOUR_USERNAME/SimulAI
cd SimulAI
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# run the demo
simulai demo --steps 30 --size 10

# or without installing a console script (fallback)
python -m simulai.cli demo --steps 30 --size 10

## 💾 Save / Load

Save a simulated world to JSON (or YAML with PyYAML installed):

```bash
# Save after 20 ticks on a 12x12 grid
simulai save --file world.json --size 12 --steps 20
# YAML requires: pip install pyyaml
simulai save --file world.yaml --size 12 --steps 20
