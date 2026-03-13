from __future__ import annotations
from dataclasses import dataclass

@dataclass
class EmotionState:
    name: str
    intensity: float  # 0.0 .. 1.0

    def __str__(self) -> str:
        return f"{self.name}:{self.intensity:.1f}"

def compute_emotion(energy: int, mood: float, recent_event: str | None) -> EmotionState:
    """
    A tiny heuristic emotion model.
    - energy: 0..15 (we cap in Simulite)
    - mood: roughly -5..+5
    - recent_event: "eat", "blocked", "nap", "social_pos", "social_neg", None
    """
    # Base emotion from mood/energy
    if energy <= 3:
        base = ("tired", 0.7)
    elif mood <= -2:
        base = ("grumpy", 0.6)
    elif mood >= 2:
        base = ("happy", 0.6)
    else:
        base = ("neutral", 0.4)

    # Modify by recent events
    if recent_event == "eat":
        return EmotionState("content", min(1.0, base[1] + 0.2))
    if recent_event == "blocked":
        return EmotionState("annoyed", min(1.0, base[1] + 0.2))
    if recent_event == "nap":
        return EmotionState("rested", min(1.0, base[1] + 0.1))
    if recent_event == "social_pos":
        return EmotionState("cheerful", min(1.0, base[1] + 0.2))
    if recent_event == "social_neg":
        return EmotionState("prickly", min(1.0, base[1] + 0.2))

    return EmotionState(*base)
