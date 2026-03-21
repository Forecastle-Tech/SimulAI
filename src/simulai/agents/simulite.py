from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from simulai.agents.traits import Traits


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


@dataclass
class Simulite:
    name: str
    x: int
    y: int
    traits: Traits = field(default_factory=Traits)

    alive: bool = True
    cause_of_death: str | None = None

    generation: int = 1
    age_ticks: int = 0
    max_age_ticks: int = 220
    life_stage: str = "juvenile"

    life_force: float = 50.0
    health: float = 50.0
    energy: float = 50.0
    nutrition: float = 50.0
    rest: float = 50.0
    exercise: float = 30.0
    social: float = 40.0
    contribution: float = 20.0
    morality: float = 50.0
    risk_load: float = 10.0
    reproduction_load: float = 0.0

    speed: float = 0.6
    agility: float = 0.6

    births: int = 0
    generation_depth: int = 1

    last_action: str = "idle"
    move_mode: str = "wander"
    target_zone: str | None = None
    target_chip: str | None = None

    action_memory: dict[str, float] = field(
        default_factory=lambda: {
            "forage": 0.0,
            "rest": 0.0,
            "exercise": 0.0,
            "socialize": 0.0,
            "contribute": 0.0,
            "help": 0.0,
            "idle": 0.0,
        }
    )
    action_counts: dict[str, int] = field(
        default_factory=lambda: {
            "forage": 0,
            "rest": 0,
            "exercise": 0,
            "socialize": 0,
            "contribute": 0,
            "help": 0,
            "idle": 0,
        }
    )

    zone_memory: dict[str, float] = field(
        default_factory=lambda: {
            "forest": 0.0,
            "plains": 0.0,
            "village": 0.0,
            "drylands": 0.0,
        }
    )
    zone_visit_counts: dict[str, int] = field(
        default_factory=lambda: {
            "forest": 0,
            "plains": 0,
            "village": 0,
            "drylands": 0,
        }
    )

    chip_memory: dict[str, float] = field(
        default_factory=lambda: {
            "good_deed": 0.0,
            "health": 0.0,
            "exercise": 0.0,
            "reproduction": 0.0,
            "bad": 0.0,
        }
    )

    reproduction_boost: float = 0.0

    def __post_init__(self) -> None:
        self.traits.clamp()
        self.generation_depth = self.generation
        self.clamp_state()

    def clamp_state(self) -> None:
        self.life_force = clamp(self.life_force)
        self.health = clamp(self.health)
        self.energy = clamp(self.energy)
        self.nutrition = clamp(self.nutrition)
        self.rest = clamp(self.rest)
        self.exercise = clamp(self.exercise)
        self.social = clamp(self.social)
        self.contribution = clamp(self.contribution)
        self.morality = clamp(self.morality)
        self.risk_load = clamp(self.risk_load)
        self.reproduction_load = clamp(self.reproduction_load)
        self.reproduction_boost = clamp(self.reproduction_boost, 0.0, 3.0)

    def update_life_stage(self) -> None:
        a = self.age_ticks
        if a <= 15:
            self.life_stage = "infant"
        elif a <= 40:
            self.life_stage = "juvenile"
        elif a <= 90:
            self.life_stage = "young_adult"
        elif a <= 140:
            self.life_stage = "adult"
        elif a <= 185:
            self.life_stage = "mature"
        else:
            self.life_stage = "elder"

    def nutrition_modifier(self) -> float:
        if self.nutrition >= 40:
            return 1.0
        if self.nutrition >= 25:
            return 0.75
        if self.nutrition >= 10:
            return 0.45
        return 0.20

    def energy_modifier(self) -> float:
        if self.energy >= 50:
            return 1.0
        if self.energy >= 30:
            return 0.75
        if self.energy >= 15:
            return 0.50
        return 0.25

    def age_curve_multiplier(self) -> float:
        midpoint = self.max_age_ticks * 0.45
        if self.age_ticks <= midpoint:
            return 0.5 + 0.5 * (self.age_ticks / midpoint)

        decline_ratio = (self.age_ticks - midpoint) / (self.max_age_ticks - midpoint)
        return 1.0 - 0.55 * decline_ratio

    def update_physical_profile(self) -> None:
        base_curve = self.age_curve_multiplier()
        n_mod = self.nutrition_modifier()
        e_mod = self.energy_modifier()

        self.speed = max(0.2, base_curve * n_mod * e_mod)
        self.agility = max(0.2, base_curve * (0.7 * n_mod + 0.3 * e_mod))

    def compute_balance_score(self) -> float:
        nutrition_score = balance_band_score(self.nutrition, 40.0, 65.0)
        rest_score = balance_band_score(self.rest, 35.0, 60.0)
        exercise_score = balance_band_score(self.exercise, 30.0, 55.0)
        social_score = balance_band_score(self.social, 30.0, 60.0)
        contribution_score = balance_band_score(self.contribution, 20.0, 50.0)
        morality_score = balance_band_score(self.morality, 35.0, 70.0)
        risk_score = balance_band_score(self.risk_load, 5.0, 30.0)
        reproduction_score = balance_band_score(self.reproduction_load, 5.0, 25.0)

        return (
            0.18 * nutrition_score
            + 0.15 * rest_score
            + 0.12 * exercise_score
            + 0.10 * social_score
            + 0.10 * contribution_score
            + 0.10 * morality_score
            + 0.10 * risk_score
            + 0.05 * reproduction_score
            + 0.10 * (self.health / 10.0)
        )

    def apply_passive_decay(self) -> None:
        metabolism_factor = self.traits.metabolism / 10.0

        self.nutrition -= 1.4 + 1.0 * metabolism_factor
        self.energy -= 1.0
        self.rest -= 0.7
        self.social -= 0.3
        self.exercise -= 0.10
        self.contribution -= 0.12
        self.reproduction_load = max(0.0, self.reproduction_load - 0.5)
        self.risk_load = max(0.0, self.risk_load - 0.3)
        self.reproduction_boost = max(0.0, self.reproduction_boost - 0.02)

        if self.nutrition < 10:
            self.health -= 2.5
            self.life_force -= 2.0
        elif self.nutrition < 25:
            self.health -= 1.0

        if self.energy < 15:
            self.health -= 1.0
            self.life_force -= 0.8

        if self.social < 15:
            self.life_force -= 0.8

        if self.risk_load > 70:
            self.health -= 1.2
            self.life_force -= 1.0

        self.clamp_state()

    def apply_overaccumulation_penalties(self) -> None:
        penalty = 0.0

        if self.exercise > 78:
            excess = self.exercise - 78
            self.energy -= 0.04 * excess
            self.health -= 0.02 * excess
            penalty += 0.02 * excess

        if self.social > 85:
            excess = self.social - 85
            self.energy -= 0.03 * excess
            self.rest -= 0.02 * excess
            penalty += 0.02 * excess

        if self.contribution > 82:
            excess = self.contribution - 82
            self.energy -= 0.03 * excess
            self.nutrition -= 0.02 * excess
            penalty += 0.025 * excess

        if self.rest > 88:
            excess = self.rest - 88
            self.exercise -= 0.03 * excess
            penalty += 0.02 * excess

        if self.reproduction_load > 42:
            excess = self.reproduction_load - 42
            self.health -= 0.04 * excess
            self.energy -= 0.03 * excess
            penalty += 0.03 * excess

        if self.reproduction_boost > 2.3:
            excess = self.reproduction_boost - 2.3
            self.risk_load += 0.30 * excess
            penalty += 0.20 * excess

        if self.nutrition > 88:
            excess = self.nutrition - 88
            self.energy -= 0.015 * excess
            penalty += 0.01 * excess

        if penalty > 0:
            self.life_force -= penalty

        self.clamp_state()

    def update_life_force(self) -> None:
        balance_score = self.compute_balance_score()
        life_force_delta = balance_score - 6.5
        self.life_force += life_force_delta
        self.clamp_state()

    def check_death(self) -> None:
        if not self.alive:
            return

        if self.life_force <= 0:
            self.alive = False
            self.cause_of_death = "life_force_collapse"
            return

        if self.health <= 0:
            self.alive = False
            self.cause_of_death = "health_collapse"
            return

        if self.age_ticks >= self.max_age_ticks:
            self.alive = False
            self.cause_of_death = "old_age"
            return

        if self.nutrition <= 0 and self.energy <= 5:
            self.alive = False
            self.cause_of_death = "starvation"
            return

    def _memory_bonus(self, action: str) -> float:
        return self.action_memory.get(action, 0.0) * 2.0

    def _zone_bonus(self, zone_name: str) -> float:
        return self.zone_memory.get(zone_name, 0.0) * 1.5

    def _chip_bonus(self, chip_type: str) -> float:
        return self.chip_memory.get(chip_type, 0.0) * 1.5

    def _score_forage(self) -> float:
        score = 0.0
        if self.nutrition < 45:
            score += (45 - self.nutrition) * 1.6
        if self.energy < 25:
            score += 2.0
        score += self.traits.curiosity * 0.5
        score += self._memory_bonus("forage")
        return score

    def _score_rest(self) -> float:
        score = 0.0
        if self.rest < 35:
            score += (35 - self.rest) * 1.4
        if self.energy < 35:
            score += (35 - self.energy) * 1.0
        if self.rest > 70:
            score -= 8.0
        score += self._memory_bonus("rest")
        return score

    def _score_exercise(self) -> float:
        if self.nutrition <= 10 or self.energy <= 15:
            return -999.0

        score = 0.0
        if self.exercise < 35:
            score += (35 - self.exercise) * 1.0
        if self.exercise > 60:
            score -= (self.exercise - 60) * 1.2
        if self.energy < 25:
            score -= 8.0
        score += self.traits.discipline * 0.5
        score += self._memory_bonus("exercise")
        return score

    def _score_socialize(self) -> float:
        score = 0.0
        if self.social < 35:
            score += (35 - self.social) * 1.0
        if self.social > 72:
            score -= (self.social - 72) * 0.8
        score += self.traits.sociability * 0.7
        score += self._memory_bonus("socialize")
        return score

    def _score_contribute(self) -> float:
        score = 0.0
        if self.contribution < 25:
            score += (25 - self.contribution) * 0.8
        if self.contribution > 68:
            score -= (self.contribution - 68) * 0.8
        if self.energy < 25:
            score -= 6.0
        if self.nutrition < 20:
            score -= 10.0
        score += self.traits.kindness * 0.6
        score += self._memory_bonus("contribute")
        return score

    def _score_help(self) -> float:
        score = -4.0

        if (
            self.life_stage in {"adult", "mature"}
            and self.energy > 60
            and self.nutrition > 60
            and self.life_force > 70
            and self.health > 60
            and self.contribution < 72
        ):
            score += 4.0

        if self.contribution < 25:
            score += 1.0

        if self.morality < 50:
            score += 0.8

        score += self.traits.kindness * 0.35
        score += self.traits.sociability * 0.15
        score += self._memory_bonus("help") * 0.4

        if self.energy < 50 or self.nutrition < 50 or self.life_force < 60:
            score -= 8.0

        return score

    def _score_idle(self) -> float:
        score = 1.0 + self._memory_bonus("idle")
        if self.energy < 20:
            score += 1.5
        if self.rest < 20:
            score += 1.5
        return score

    def choose_action(self) -> str:
        action_scores = {
            "forage": self._score_forage(),
            "rest": self._score_rest(),
            "exercise": self._score_exercise(),
            "socialize": self._score_socialize(),
            "contribute": self._score_contribute(),
            "help": self._score_help(),
            "idle": self._score_idle(),
        }
        return max(action_scores, key=action_scores.get)

    def choose_target_zone(self) -> str | None:
        zone_scores = {
            "forest": 0.0,
            "plains": 1.0,
            "village": 0.0,
            "drylands": -1.0,
        }

        if self.nutrition < 40:
            zone_scores["forest"] += (40 - self.nutrition) * 0.8

        if self.social < 35:
            zone_scores["village"] += (35 - self.social) * 0.7

        if self.rest < 35 or self.energy < 30:
            zone_scores["village"] += 4.0

        if self.risk_load > 35 or self.energy < 20 or self.health < 30:
            zone_scores["drylands"] -= 8.0

        if self.nutrition > 60 and self.social > 55 and self.rest > 50:
            zone_scores["plains"] += 2.0

        for zone_name in zone_scores:
            zone_scores[zone_name] += self._zone_bonus(zone_name)

        best_zone = max(zone_scores, key=zone_scores.get)
        if zone_scores[best_zone] <= 0.5:
            return None
        return best_zone

    def choose_target_chip(self) -> str | None:
        chip_scores = {
            "health": 0.0,
            "good_deed": 0.0,
            "exercise": 0.0,
            "reproduction": 0.0,
            "bad": -10.0,
        }

        if self.health < 45:
            chip_scores["health"] += (45 - self.health) * 0.5

        if self.exercise < 35 and self.nutrition > 15 and self.energy > 20:
            chip_scores["exercise"] += (35 - self.exercise) * 0.5

        if self.social < 30 or self.contribution < 15 or self.morality < 35:
            chip_scores["good_deed"] += 3.5

        if (
            self.life_stage in {"young_adult", "adult", "mature"}
            and self.life_force > 70
            and self.health > 60
            and self.energy > 55
            and self.nutrition > 55
            and self.reproduction_load < 18
        ):
            chip_scores["reproduction"] += 2.5

        if self.contribution > 72:
            chip_scores["good_deed"] -= 2.0

        if self.exercise > 62:
            chip_scores["exercise"] -= 2.0

        chip_scores["health"] += self._chip_bonus("health")
        chip_scores["good_deed"] += self._chip_bonus("good_deed")
        chip_scores["exercise"] += self._chip_bonus("exercise")
        chip_scores["reproduction"] += self._chip_bonus("reproduction")
        chip_scores["bad"] += self._chip_bonus("bad")

        best_chip = max(chip_scores, key=chip_scores.get)
        if chip_scores[best_chip] <= 1.0:
            return None
        return best_chip

    def perform_action(self, action: str) -> None:
        if not self.alive:
            return

        self.last_action = action
        self.target_zone = self.choose_target_zone()
        self.target_chip = self.choose_target_chip()

        survival_critical = (
            self.nutrition < 35 or self.energy < 25 or self.life_force < 45 or self.health < 40
        )

        if action == "forage":
            self.energy -= 0.6
            self.rest -= 0.3
            self.risk_load += 0.4
            self.nutrition += 3.5
            self.life_force += 0.6
            self.move_mode = "seek_food"

            if not survival_critical:
                if self.target_chip in {"health", "exercise", "good_deed", "reproduction"}:
                    self.move_mode = "seek_chip"
                elif self.target_zone == "forest":
                    self.move_mode = "seek_zone"

        elif action == "rest":
            self.rest += 6.0
            self.energy += 5.0
            self.risk_load -= 0.8
            self.exercise -= 0.2
            self.life_force += 0.2
            self.move_mode = "stay"

            if not survival_critical and self.target_zone == "village" and self.rest < 50:
                self.move_mode = "seek_zone"

        elif action == "exercise":
            if self.nutrition <= 10 or self.energy <= 15:
                self.health -= 1.0
                self.energy -= 1.0
                self.life_force -= 0.8
            else:
                self.exercise += 3.0
                self.health += 1.2
                self.energy -= 1.8
                self.rest -= 1.0
                self.risk_load += 0.3
                self.life_force += 0.2
            self.move_mode = "wander"

            if not survival_critical and self.target_chip == "exercise":
                self.move_mode = "seek_chip"

        elif action == "socialize":
            self.social += 3.5
            self.energy -= 0.9
            self.rest -= 0.4
            self.life_force += 0.2
            self.move_mode = "wander"

            if not survival_critical:
                if self.target_chip == "good_deed":
                    self.move_mode = "seek_chip"
                elif self.target_zone == "village":
                    self.move_mode = "seek_zone"

        elif action == "contribute":
            self.contribution += 2.4
            self.morality += 1.2
            self.energy -= 1.3
            self.rest -= 0.4
            self.life_force += 0.3
            if self.energy < 20 or self.nutrition < 20:
                self.life_force -= 0.6
            self.move_mode = "wander"

            if not survival_critical:
                if self.target_chip == "good_deed":
                    self.move_mode = "seek_chip"
                elif self.target_zone == "village":
                    self.move_mode = "seek_zone"

        elif action == "help":
            self.energy -= 0.8
            self.nutrition -= 0.4
            self.rest -= 0.2
            self.contribution += 1.8
            self.morality += 1.0
            self.social += 0.7
            self.life_force += 0.2
            self.move_mode = "wander"

            if self.target_zone == "village" and not survival_critical:
                self.move_mode = "seek_zone"

        elif action == "idle":
            self.rest += 1.0
            self.energy += 0.5
            self.move_mode = "stay"

        self.action_counts[action] += 1
        self.clamp_state()

    def update_action_memory(self, action: str, reward: float) -> None:
        learning_rate = 0.08 + (self.traits.discipline / 100.0) + (self.traits.resilience / 200.0)
        old_value = self.action_memory.get(action, 0.0)
        new_value = old_value + learning_rate * (reward - old_value)
        self.action_memory[action] = max(-5.0, min(5.0, new_value))

    def update_zone_memory(self, zone_name: str, reward: float) -> None:
        if zone_name not in self.zone_memory:
            self.zone_memory[zone_name] = 0.0
            self.zone_visit_counts[zone_name] = 0

        learning_rate = 0.05 + (self.traits.curiosity / 150.0)
        old_value = self.zone_memory.get(zone_name, 0.0)
        new_value = old_value + learning_rate * (reward - old_value)
        self.zone_memory[zone_name] = max(-5.0, min(5.0, new_value))
        self.zone_visit_counts[zone_name] += 1

    def update_chip_memory(self, chip_type: str, reward: float) -> None:
        if chip_type not in self.chip_memory:
            self.chip_memory[chip_type] = 0.0

        learning_rate = 0.05 + (self.traits.curiosity / 180.0)
        old_value = self.chip_memory.get(chip_type, 0.0)
        new_value = old_value + learning_rate * (reward - old_value)
        self.chip_memory[chip_type] = max(-5.0, min(5.0, new_value))

    def step(self, current_zone: str | None = None) -> None:
        if not self.alive:
            return

        before_life = self.life_force
        before_health = self.health
        before_energy = self.energy
        before_nutrition = self.nutrition

        self.age_ticks += 1
        self.update_life_stage()
        self.update_physical_profile()
        self.apply_passive_decay()

        action = self.choose_action()
        self.perform_action(action)

        self.apply_overaccumulation_penalties()
        self.update_life_force()
        self.check_death()

        reward = (
            (self.life_force - before_life) * 0.8
            + (self.health - before_health) * 0.6
            + (self.energy - before_energy) * 0.2
            + (self.nutrition - before_nutrition) * 0.3
        )

        if not self.alive:
            reward -= 5.0

        self.update_action_memory(action, reward)

        if current_zone is not None:
            self.update_zone_memory(current_zone, reward)

    def distance_to(self, other: "Simulite") -> float:
        return math.dist((self.x, self.y), (other.x, other.y))

    def _move_toward(self, target_x: int, target_y: int, width: int, height: int) -> None:
        dx = 0
        dy = 0

        if target_x > self.x:
            dx = 1
        elif target_x < self.x:
            dx = -1

        if target_y > self.y:
            dy = 1
        elif target_y < self.y:
            dy = -1

        if abs(target_x - self.x) >= abs(target_y - self.y):
            self.x = max(0, min(width - 1, self.x + dx))
        else:
            self.y = max(0, min(height - 1, self.y + dy))

    def _move_toward_zone(
        self,
        zone_name: str,
        width: int,
        height: int,
        zone_lookup: dict[str, list[tuple[int, int]]] | None,
    ) -> bool:
        if not zone_lookup:
            return False

        cells = zone_lookup.get(zone_name, [])
        if not cells:
            return False

        nearest = min(
            cells,
            key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y),
        )
        self._move_toward(nearest[0], nearest[1], width, height)
        return True

    def _move_toward_chip(
        self,
        chip_positions: dict[tuple[int, int], str] | None,
        width: int,
        height: int,
    ) -> bool:
        if not chip_positions or not self.target_chip:
            return False

        candidates = [
            pos for pos, chip_type in chip_positions.items() if chip_type == self.target_chip
        ]
        if not candidates:
            return False

        nearest = min(
            candidates,
            key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y),
        )
        self._move_toward(nearest[0], nearest[1], width, height)
        return True

    def move_random(
        self,
        width: int,
        height: int,
        food_positions: set[tuple[int, int]] | None = None,
        zone_lookup: dict[str, list[tuple[int, int]]] | None = None,
        chip_positions: dict[tuple[int, int], str] | None = None,
    ) -> None:
        if not self.alive:
            return

        move_chance = min(0.95, max(0.15, self.speed))
        if random.random() > move_chance:
            return

        if self.energy < 10 or self.nutrition < 8:
            if random.random() < 0.7:
                return

        food_positions = food_positions or set()

        if self.move_mode == "stay":
            return

        if self.move_mode == "seek_chip":
            moved = self._move_toward_chip(chip_positions, width, height)
            if moved:
                return

        if self.move_mode == "seek_food" and food_positions:
            nearest = min(
                food_positions,
                key=lambda pos: abs(pos[0] - self.x) + abs(pos[1] - self.y),
            )
            self._move_toward(nearest[0], nearest[1], width, height)
            return

        if self.move_mode == "seek_zone" and self.target_zone:
            moved = self._move_toward_zone(self.target_zone, width, height, zone_lookup)
            if moved:
                return

        options = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        if self.energy < 15 or self.nutrition < 10:
            options.extend([(0, 0), (0, 0)])

        dx, dy = random.choice(options)
        self.x = max(0, min(width - 1, self.x + dx))
        self.y = max(0, min(height - 1, self.y + dy))
