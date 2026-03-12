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
