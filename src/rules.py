from __future__ import annotations

from typing import Any

OPTIMAL_BANDS = {
    "nutrition": (40.0, 65.0),
    "rest": (35.0, 60.0),
    "exercise": (30.0, 55.0),
    "social": (30.0, 60.0),
    "contribution": (20.0, 50.0),
    "morality": (35.0, 70.0),
    "risk_load": (5.0, 30.0),
    "reproduction_load": (5.0, 25.0),
}

THRESHOLDS = {
    "starving": 10.0,
    "weak_nutrition": 25.0,
    "low_energy": 15.0,
    "death_life_force": 0.0,
    "death_health": 0.0,
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def balance_band_score(
    value: float,
    low: float,
    high: float,
    peak: float = 10.0,
    penalty: float = 0.5,
) -> float:
    if low <= value <= high:
        return peak
    if value < low:
        return max(0.0, peak - (low - value) * penalty)
    return max(0.0, peak - (value - high) * penalty)


def ensure_agent_fields(agent: Any) -> None:
    defaults = {
        "generation": 1,
        "parents": [],
        "alive": True,
        "cause_of_death": None,
        "life_force": 50.0,
        "health": 50.0,
        "energy": 50.0,
        "nutrition": 50.0,
        "rest": 50.0,
        "exercise": 30.0,
        "social": 40.0,
        "contribution": 20.0,
        "morality": 50.0,
        "risk_load": 10.0,
        "reproduction_load": 0.0,
        "age_ticks": 0,
        "max_age_ticks": 220,
        "life_stage": "juvenile",
        "speed": 0.6,
        "agility": 0.6,
        "traits": {
            "kindness": 0.5,
            "discipline": 0.5,
            "caution": 0.5,
            "ambition": 0.5,
            "sociability": 0.5,
            "resilience": 0.5,
            "fertility": 0.5,
            "learning_rate": 0.5,
            "metabolism": 0.5,
        },
    }

    for key, value in defaults.items():
        if not hasattr(agent, key):
            setattr(agent, key, value)


def update_life_stage(agent: Any) -> None:
    a = agent.age_ticks
    if a <= 15:
        agent.life_stage = "infant"
    elif a <= 40:
        agent.life_stage = "juvenile"
    elif a <= 90:
        agent.life_stage = "young_adult"
    elif a <= 140:
        agent.life_stage = "adult"
    elif a <= 185:
        agent.life_stage = "mature"
    else:
        agent.life_stage = "elder"


def nutrition_modifier(agent: Any) -> float:
    if agent.nutrition >= 40:
        return 1.0
    if agent.nutrition >= 25:
        return 0.78
    if agent.nutrition >= 10:
        return 0.50
    return 0.24


def energy_modifier(agent: Any) -> float:
    if agent.energy >= 50:
        return 1.0
    if agent.energy >= 30:
        return 0.78
    if agent.energy >= 15:
        return 0.55
    return 0.30


def age_curve_multiplier(agent: Any) -> float:
    a = agent.age_ticks
    max_age = agent.max_age_ticks
    midpoint = max_age * 0.48

    if a <= midpoint:
        return 0.56 + 0.44 * (a / midpoint)

    decline_ratio = (a - midpoint) / (max_age - midpoint)
    return 1.0 - 0.48 * decline_ratio


def update_physical_profile(agent: Any) -> None:
    base_curve = age_curve_multiplier(agent)
    n_mod = nutrition_modifier(agent)
    e_mod = energy_modifier(agent)

    agent.speed = max(0.22, base_curve * n_mod * e_mod)
    agent.agility = max(0.22, base_curve * (0.7 * n_mod + 0.3 * e_mod))


def clamp_agent_state(agent: Any) -> None:
    agent.life_force = clamp(agent.life_force)
    agent.health = clamp(agent.health)
    agent.energy = clamp(agent.energy)
    agent.nutrition = clamp(agent.nutrition)
    agent.rest = clamp(agent.rest)
    agent.exercise = clamp(agent.exercise)
    agent.social = clamp(agent.social)
    agent.contribution = clamp(agent.contribution)
    agent.morality = clamp(agent.morality)
    agent.risk_load = clamp(agent.risk_load)
    agent.reproduction_load = clamp(agent.reproduction_load)


def apply_passive_decay(agent: Any) -> None:
    metabolism = agent.traits["metabolism"]

    agent.nutrition -= 1.7 + 1.2 * metabolism
    agent.energy -= 1.2
    agent.rest -= 0.85
    agent.social -= 0.28
    agent.exercise -= 0.10
    agent.contribution -= 0.12
    agent.reproduction_load = max(0.0, agent.reproduction_load - 0.65)
    agent.risk_load = max(0.0, agent.risk_load - 0.35)

    if agent.nutrition < THRESHOLDS["starving"]:
        agent.health -= 1.8
        agent.life_force -= 1.5
    elif agent.nutrition < THRESHOLDS["weak_nutrition"]:
        agent.health -= 0.7

    if agent.energy < THRESHOLDS["low_energy"]:
        agent.health -= 0.7
        agent.life_force -= 0.55

    if agent.exercise > 70:
        agent.health -= 0.55
        agent.energy -= 0.85

    if agent.rest > 75:
        agent.exercise -= 0.35
        agent.contribution -= 0.18

    if agent.social < 15:
        agent.life_force -= 0.45

    if agent.social > 80:
        agent.energy -= 0.35
        agent.rest -= 0.22

    if agent.risk_load > 70:
        agent.health -= 0.9
        agent.life_force -= 0.75

    clamp_agent_state(agent)


def compute_balance_score(agent: Any) -> float:
    nutrition_score = balance_band_score(agent.nutrition, *OPTIMAL_BANDS["nutrition"])
    rest_score = balance_band_score(agent.rest, *OPTIMAL_BANDS["rest"])
    exercise_score = balance_band_score(agent.exercise, *OPTIMAL_BANDS["exercise"])
    social_score = balance_band_score(agent.social, *OPTIMAL_BANDS["social"])
    contribution_score = balance_band_score(agent.contribution, *OPTIMAL_BANDS["contribution"])
    morality_score = balance_band_score(agent.morality, *OPTIMAL_BANDS["morality"])
    risk_score = balance_band_score(agent.risk_load, *OPTIMAL_BANDS["risk_load"])
    reproduction_score = balance_band_score(
        agent.reproduction_load,
        *OPTIMAL_BANDS["reproduction_load"],
    )

    return (
        0.18 * nutrition_score
        + 0.15 * rest_score
        + 0.12 * exercise_score
        + 0.10 * social_score
        + 0.10 * contribution_score
        + 0.10 * morality_score
        + 0.10 * risk_score
        + 0.05 * reproduction_score
        + 0.10 * (agent.health / 10.0)
    )


def update_life_force(agent: Any) -> None:
    balance_score = compute_balance_score(agent)
    life_force_delta = balance_score - 6.2
    agent.life_force += life_force_delta
    clamp_agent_state(agent)


def check_death(agent: Any) -> None:
    if not agent.alive:
        return

    if agent.life_force <= THRESHOLDS["death_life_force"]:
        agent.alive = False
        agent.cause_of_death = "life_force_collapse"
        return

    if agent.health <= THRESHOLDS["death_health"]:
        agent.alive = False
        agent.cause_of_death = "health_collapse"
        return

    if agent.age_ticks >= agent.max_age_ticks:
        agent.alive = False
        agent.cause_of_death = "old_age"
        return

    if agent.nutrition <= 0 and agent.energy <= 4:
        agent.alive = False
        agent.cause_of_death = "starvation"


def tick_agent_state(agent: Any) -> None:
    ensure_agent_fields(agent)

    if not agent.alive:
        return

    agent.age_ticks += 1
    update_life_stage(agent)
    update_physical_profile(agent)
    apply_passive_decay(agent)
    update_life_force(agent)
    check_death(agent)
