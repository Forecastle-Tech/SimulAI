from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any

from simulai.agents.simulite import Simulite
from simulai.agents.traits import Traits


class World:
    def __init__(self, grid) -> None:
        self.grid = grid
        self.agents: list[Any] = []

        self.food: set[tuple[int, int]] = set()
        self.chips: dict[tuple[int, int], str] = {}

        self.food_zones: list[tuple[int, int]] = []
        self._last_log: str = ""

        self.tick_count: int = 0
        self.metrics_history: list[dict[str, float | int]] = []
        self.deaths_by_cause: dict[str, int] = {}

        self.next_child_id: int = 1
        self.max_population: int = 24
        self.max_generation_limit: int = 6

    def add_agent(self, agent) -> None:
        self.agents.append(agent)

    def living_agents(self) -> list[Any]:
        return [a for a in self.agents if getattr(a, "alive", True)]

    def dead_agents(self) -> list[Any]:
        return [a for a in self.agents if not getattr(a, "alive", True)]

    def get_zone(self, x: int, y: int) -> str:
        return self.grid.get_zone(x, y)

    def zone_lookup(self) -> dict[str, list[tuple[int, int]]]:
        return {
            "forest": self.grid.cells_in_zone("forest"),
            "plains": self.grid.cells_in_zone("plains"),
            "village": self.grid.cells_in_zone("village"),
            "drylands": self.grid.cells_in_zone("drylands"),
        }

    def sprinkle_food(self, count: int = 5) -> None:
        added = 0
        weighted_zone_choices = ["forest"] * 5 + ["plains"] * 3 + ["village"] * 2 + ["drylands"] * 1

        for _ in range(count):
            zone_name = random.choice(weighted_zone_choices)
            pos = self.grid.random_cell_in_zone(zone_name)

            if pos is None:
                x = random.randint(0, self.grid.width - 1)
                y = random.randint(0, self.grid.height - 1)
                pos = (x, y)

            if pos in self.chips:
                continue

            if pos not in self.food:
                added += 1
            self.food.add(pos)

        self._last_log = f"Sprinkled food: +{added}"

    def sprinkle_chips(self, count: int = 3) -> None:
        zone_chip_weights = {
            "forest": (["health"] * 4 + ["exercise"] * 3 + ["good_deed"] * 1 + ["bad"] * 1),
            "plains": (
                ["good_deed"] * 2
                + ["health"] * 2
                + ["exercise"] * 2
                + ["reproduction"] * 1
                + ["bad"] * 1
            ),
            "village": (["good_deed"] * 5 + ["health"] * 2 + ["exercise"] * 1 + ["bad"] * 1),
            "drylands": (["bad"] * 5 + ["reproduction"] * 2 + ["exercise"] * 1 + ["health"] * 1),
        }

        added = 0
        zone_names = ["forest", "plains", "village", "drylands"]

        for _ in range(count):
            zone_name = random.choice(zone_names)
            pos = self.grid.random_cell_in_zone(zone_name)

            if pos is None:
                continue

            if pos in self.food or pos in self.chips:
                continue

            chip_type = random.choice(zone_chip_weights[zone_name])
            self.chips[pos] = chip_type
            added += 1

        if added > 0:
            self._last_log = f"Spawned chips: +{added}"

    def _apply_zone_effects(self, agent) -> None:
        zone = self.get_zone(agent.x, agent.y)

        if zone == "forest":
            agent.energy = min(100.0, agent.energy + 0.3)

        elif zone == "village":
            agent.social = min(100.0, agent.social + 0.6)
            agent.rest = min(100.0, agent.rest + 0.4)
            agent.life_force = min(100.0, agent.life_force + 0.2)

        elif zone == "drylands":
            agent.energy = max(0.0, agent.energy - 0.4)
            agent.risk_load = min(100.0, agent.risk_load + 0.5)

    def _feed_agent_if_on_food(self, agent) -> None:
        pos = (agent.x, agent.y)
        if pos in self.food and getattr(agent, "alive", True):
            self.food.remove(pos)

            zone = self.get_zone(agent.x, agent.y)

            nutrition_gain = 24.0
            energy_gain = 6.0
            life_force_gain = 3.0
            health_gain = 1.5

            if zone == "forest":
                nutrition_gain += 4.0
                energy_gain += 1.0
            elif zone == "drylands":
                nutrition_gain -= 4.0
                life_force_gain -= 0.5

            agent.nutrition = min(100.0, agent.nutrition + nutrition_gain)
            agent.energy = min(100.0, agent.energy + energy_gain)
            agent.life_force = min(100.0, agent.life_force + life_force_gain)
            agent.health = min(100.0, agent.health + health_gain)

            self._last_log = f"{agent.name} found food in {zone}"

    def _apply_chip_effect(self, agent, chip_type: str) -> None:
        if chip_type == "good_deed":
            agent.contribution = min(100.0, agent.contribution + 8.0)
            agent.morality = min(100.0, agent.morality + 6.0)
            agent.social = min(100.0, agent.social + 4.0)
            agent.life_force = min(100.0, agent.life_force + 3.0)

        elif chip_type == "health":
            agent.health = min(100.0, agent.health + 8.0)
            agent.energy = min(100.0, agent.energy + 3.0)
            agent.life_force = min(100.0, agent.life_force + 2.0)

        elif chip_type == "exercise":
            if agent.nutrition > 10 and agent.energy > 15:
                agent.exercise = min(100.0, agent.exercise + 6.0)
                agent.health = min(100.0, agent.health + 3.0)
                agent.energy = max(0.0, agent.energy - 1.0)
                agent.life_force = min(100.0, agent.life_force + 1.5)
            else:
                agent.energy = max(0.0, agent.energy - 1.0)
                agent.life_force = max(0.0, agent.life_force - 0.5)

        elif chip_type == "reproduction":
            agent.reproduction_load = max(0.0, agent.reproduction_load - 8.0)
            agent.life_force = min(100.0, agent.life_force + 2.0)
            agent.health = min(100.0, agent.health + 1.0)
            agent.reproduction_boost = min(3.0, agent.reproduction_boost + 1.0)

        elif chip_type == "bad":
            agent.health = max(0.0, agent.health - 6.0)
            agent.life_force = max(0.0, agent.life_force - 4.0)
            agent.risk_load = min(100.0, agent.risk_load + 8.0)
            agent.morality = max(0.0, agent.morality - 2.0)

        agent.clamp_state()

    def _collect_chip_if_on_tile(self, agent) -> None:
        pos = (agent.x, agent.y)
        if pos not in self.chips or not getattr(agent, "alive", True):
            return

        chip_type = self.chips.pop(pos)

        before_life = agent.life_force
        before_health = agent.health
        before_energy = agent.energy
        before_nutrition = agent.nutrition

        self._apply_chip_effect(agent, chip_type)

        reward = (
            (agent.life_force - before_life) * 0.8
            + (agent.health - before_health) * 0.6
            + (agent.energy - before_energy) * 0.2
            + (agent.nutrition - before_nutrition) * 0.3
        )

        agent.update_chip_memory(chip_type, reward)
        self._last_log = f"{agent.name} collected {chip_type}"

    def _nearby_agents(self, agent: Simulite, max_distance: float = 1.5) -> list[Simulite]:
        nearby: list[Simulite] = []
        for other in self.living_agents():
            if other is agent:
                continue
            if agent.distance_to(other) <= max_distance:
                nearby.append(other)
        return nearby

    def _attempt_help(self, helper: Simulite) -> None:
        if not helper.alive:
            return

        if helper.last_action != "help":
            return

        if (
            helper.energy < 55
            or helper.nutrition < 55
            or helper.life_force < 65
            or helper.health < 55
        ):
            return

        nearby = self._nearby_agents(helper)
        if not nearby:
            return

        needy = [
            other
            for other in nearby
            if (
                other.life_force < 35
                or other.health < 30
                or other.energy < 18
                or other.nutrition < 18
            )
        ]
        if not needy:
            return

        target = min(
            needy,
            key=lambda a: a.life_force + a.health + a.energy + a.nutrition,
        )

        transfer_energy = min(2.0, max(0.0, helper.energy - 40.0))
        transfer_nutrition = min(2.0, max(0.0, helper.nutrition - 40.0))
        transfer_life = 0.8 if helper.life_force > 70 else 0.3

        if transfer_energy <= 0 and transfer_nutrition <= 0:
            return

        helper.energy = max(0.0, helper.energy - transfer_energy)
        helper.nutrition = max(0.0, helper.nutrition - transfer_nutrition)
        helper.life_force = max(0.0, helper.life_force - transfer_life * 0.25)

        target.energy = min(100.0, target.energy + transfer_energy)
        target.nutrition = min(100.0, target.nutrition + transfer_nutrition)
        target.life_force = min(100.0, target.life_force + transfer_life)
        target.health = min(100.0, target.health + 1.0)

        helper.contribution = min(100.0, helper.contribution + 1.5)
        helper.morality = min(100.0, helper.morality + 1.0)
        helper.social = min(100.0, helper.social + 0.5)
        helper.life_force = min(100.0, helper.life_force + 0.4)

        helper.clamp_state()
        target.clamp_state()

        reward = 3.0 + 0.4 * transfer_energy + 0.4 * transfer_nutrition + transfer_life
        helper.update_action_memory("help", reward)
        helper.update_chip_memory("good_deed", reward * 0.5)

        self._last_log = f"{helper.name} helped {target.name}"

    def _record_new_deaths(self, previous_dead_names: set[str]) -> None:
        for agent in self.dead_agents():
            if agent.name not in previous_dead_names and agent.cause_of_death:
                self.deaths_by_cause[agent.cause_of_death] = (
                    self.deaths_by_cause.get(agent.cause_of_death, 0) + 1
                )
                self._last_log = f"{agent.name} died: {agent.cause_of_death}"

    def _record_metrics(self) -> None:
        living = self.living_agents()

        if not living:
            self.metrics_history.append(
                {
                    "tick": self.tick_count,
                    "population": 0,
                    "avg_life_force": 0.0,
                    "avg_health": 0.0,
                    "avg_energy": 0.0,
                    "avg_nutrition": 0.0,
                    "avg_rest": 0.0,
                    "avg_exercise": 0.0,
                    "avg_social": 0.0,
                    "avg_speed": 0.0,
                    "avg_agility": 0.0,
                    "avg_generation": 0.0,
                    "deaths_total": len(self.dead_agents()),
                }
            )
            return

        def avg(values: list[float]) -> float:
            return sum(values) / len(values)

        self.metrics_history.append(
            {
                "tick": self.tick_count,
                "population": len(living),
                "avg_life_force": avg([a.life_force for a in living]),
                "avg_health": avg([a.health for a in living]),
                "avg_energy": avg([a.energy for a in living]),
                "avg_nutrition": avg([a.nutrition for a in living]),
                "avg_rest": avg([a.rest for a in living]),
                "avg_exercise": avg([a.exercise for a in living]),
                "avg_social": avg([a.social for a in living]),
                "avg_speed": avg([a.speed for a in living]),
                "avg_agility": avg([a.agility for a in living]),
                "avg_generation": avg([float(a.generation) for a in living]),
                "deaths_total": len(self.dead_agents()),
            }
        )

    def _history(self, key: str, limit: int = 50) -> list[float]:
        values = [float(row.get(key, 0.0)) for row in self.metrics_history[-limit:]]
        return values if values else [0.0]

    def _compute_trend(self) -> str:
        if len(self.metrics_history) < 2:
            return "stable"

        last = self.metrics_history[-1]
        prev = self.metrics_history[-2]

        population_delta = float(last.get("population", 0.0)) - float(prev.get("population", 0.0))
        life_force_delta = float(last.get("avg_life_force", 0.0)) - float(
            prev.get("avg_life_force", 0.0)
        )

        if population_delta > 0 or life_force_delta > 0.5:
            return "rising"
        if population_delta < 0 or life_force_delta < -0.5:
            return "declining"
        return "stable"

    def _adjacent_cells(self, x: int, y: int) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx = x + dx
            ny = y + dy
            if self.grid.in_bounds(nx, ny):
                cells.append((nx, ny))
        return cells

    def _find_child_spawn(self, parent: Simulite) -> tuple[int, int] | None:
        nearby = self._adjacent_cells(parent.x, parent.y)
        nearby = [pos for pos in nearby if pos not in self.food and pos not in self.chips]

        if nearby:
            return random.choice(nearby)

        return self.grid.random_empty_cell()

    def _mutate_trait(self, value: float, spread: float = 0.6) -> float:
        return max(0.0, min(10.0, value + random.uniform(-spread, spread)))

    def _inherit_traits(self, parent: Simulite) -> Traits:
        t = parent.traits
        return Traits(
            curiosity=self._mutate_trait(t.curiosity),
            sociability=self._mutate_trait(t.sociability),
            discipline=self._mutate_trait(t.discipline),
            resilience=self._mutate_trait(t.resilience),
            metabolism=self._mutate_trait(t.metabolism),
            kindness=self._mutate_trait(t.kindness),
            caution=self._mutate_trait(t.caution),
        )

    def _lineage_score(self, parent: Simulite) -> float:
        memory_strength = (
            max(0.0, parent.action_memory.get("forage", 0.0))
            + max(0.0, parent.zone_memory.get("forest", 0.0))
            + max(0.0, parent.zone_memory.get("village", 0.0))
            + max(0.0, parent.chip_memory.get("health", 0.0))
            + max(0.0, parent.chip_memory.get("good_deed", 0.0))
        )

        return (
            0.20 * parent.life_force
            + 0.18 * parent.health
            + 0.14 * parent.nutrition
            + 0.10 * parent.energy
            + 0.08 * parent.rest
            + 0.08 * parent.morality
            + 0.08 * parent.contribution
            + 0.05 * parent.social
            + 0.05 * (memory_strength * 10.0)
            + 0.04 * max(0, 4 - parent.births)
        ) / 100.0

    def _generation_pressure(self, generation: int) -> float:
        if generation <= 2:
            return 0.0
        if generation == 3:
            return 0.03
        if generation == 4:
            return 0.06
        if generation == 5:
            return 0.10
        return 0.14

    def _lineage_fatigue(self, parent: Simulite) -> float:
        fatigue = 0.0

        if parent.births >= 3:
            fatigue += 0.03 * (parent.births - 2)

        if parent.life_force < 55:
            fatigue += 0.05
        if parent.health < 50:
            fatigue += 0.05
        if parent.nutrition < 45:
            fatigue += 0.04
        if parent.reproduction_load > 22:
            fatigue += 0.05

        return min(0.22, fatigue)

    def _legacy_advantage(self, parent: Simulite) -> float:
        score = self._lineage_score(parent)

        if score >= 0.72:
            return 0.08
        if score >= 0.62:
            return 0.05
        if score >= 0.54:
            return 0.02
        return 0.0

    def _inherit_action_memory(self, parent: Simulite, support: float) -> dict[str, float]:
        inherit_factor = min(0.78, 0.32 + 0.56 * support)
        child_memory: dict[str, float] = {}

        for action, value in parent.action_memory.items():
            inherited = value * inherit_factor

            if action == "forage":
                inherited += 0.12 * support
            elif action in {"rest", "help"}:
                inherited += 0.05 * support
            elif action in {"contribute", "socialize"} and parent.contribution > 70:
                inherited *= 0.92

            inherited += random.uniform(-0.08, 0.08)
            child_memory[action] = max(-5.0, min(5.0, inherited))

        return child_memory

    def _inherit_zone_memory(self, parent: Simulite, support: float) -> dict[str, float]:
        inherit_factor = min(0.74, 0.30 + 0.50 * support)
        child_memory: dict[str, float] = {}

        for zone, value in parent.zone_memory.items():
            inherited = value * inherit_factor

            if zone == "forest" and parent.nutrition > 45:
                inherited += 0.08 * support
            if zone == "village" and parent.social > 40:
                inherited += 0.05 * support

            inherited += random.uniform(-0.06, 0.06)
            child_memory[zone] = max(-5.0, min(5.0, inherited))

        return child_memory

    def _inherit_chip_memory(self, parent: Simulite, support: float) -> dict[str, float]:
        inherit_factor = min(0.68, 0.24 + 0.48 * support)
        child_memory: dict[str, float] = {}

        for chip, value in parent.chip_memory.items():
            inherited = value * inherit_factor

            if chip == "bad":
                inherited *= 0.70
            if chip == "health" and parent.health > 50:
                inherited += 0.04 * support
            if chip == "good_deed" and parent.contribution > 55:
                inherited += 0.03 * support

            inherited += random.uniform(-0.05, 0.05)
            child_memory[chip] = max(-5.0, min(5.0, inherited))

        return child_memory

    def _create_offspring(self, parent: Simulite) -> Simulite | None:
        if len(self.living_agents()) >= self.max_population:
            return None

        if parent.generation >= self.max_generation_limit:
            return None

        spawn = self._find_child_spawn(parent)
        if spawn is None:
            return None

        child_name = f"C{self.next_child_id}"
        self.next_child_id += 1

        support = self._lineage_score(parent)
        pressure = self._generation_pressure(parent.generation + 1)
        fatigue = self._lineage_fatigue(parent)
        legacy = self._legacy_advantage(parent)

        effective_support = max(0.18, min(0.95, support + legacy - pressure - fatigue))
        hardship = max(0.0, 0.55 - effective_support)

        child = Simulite(
            name=child_name,
            x=spawn[0],
            y=spawn[1],
            traits=self._inherit_traits(parent),
            generation=parent.generation + 1,
            life_force=max(18.0, 30.0 + 30.0 * effective_support - 8.0 * hardship),
            health=max(18.0, 27.0 + 28.0 * effective_support - 7.0 * hardship),
            energy=max(20.0, 30.0 + 22.0 * effective_support - 5.0 * hardship),
            nutrition=max(18.0, 22.0 + 25.0 * effective_support - 7.0 * hardship),
            rest=36.0 + 9.0 * effective_support,
            exercise=17.0 + 7.0 * effective_support,
            social=26.0 + 11.0 * effective_support,
            contribution=7.0 + 7.0 * effective_support,
            morality=35.0 + 11.0 * effective_support,
            risk_load=max(4.0, 11.0 - 4.5 * effective_support + 3.0 * hardship + pressure * 20.0),
            reproduction_load=0.0,
            reproduction_boost=max(0.0, min(1.0, parent.reproduction_boost * 0.30)),
        )

        child.action_memory = self._inherit_action_memory(parent, effective_support)
        child.zone_memory = self._inherit_zone_memory(parent, effective_support)
        child.chip_memory = self._inherit_chip_memory(parent, effective_support)

        child.action_memory["forage"] = max(child.action_memory.get("forage", 0.0), 0.18)
        child.zone_memory["forest"] = max(child.zone_memory.get("forest", 0.0), 0.12)
        child.chip_memory["bad"] = min(child.chip_memory.get("bad", 0.0), -0.12)

        return child

    def _can_reproduce(self, agent: Simulite) -> bool:
        if not agent.alive:
            return False

        if len(self.living_agents()) >= self.max_population:
            return False

        if agent.generation >= self.max_generation_limit:
            return False

        if agent.life_stage not in {"young_adult", "adult", "mature"}:
            return False

        if agent.life_force < 65:
            return False
        if agent.health < 55:
            return False
        if agent.energy < 50:
            return False
        if agent.nutrition < 50:
            return False
        if agent.risk_load > 40:
            return False
        if agent.reproduction_load > 20:
            return False

        return True

    def _offspring_count_for_parent(self, parent: Simulite) -> int:
        count = 1
        boost = float(getattr(parent, "reproduction_boost", 0.0))

        elite_parent = (
            parent.life_force > 82
            and parent.health > 78
            and parent.energy > 74
            and parent.nutrition > 74
            and parent.morality > 55
        )

        if boost >= 1.0 and elite_parent:
            if boost >= 2.0 and random.random() < 0.20:
                count = 3
            elif random.random() < 0.40:
                count = 2

        return count

    def _attempt_reproduction(self) -> None:
        births_this_tick: list[Simulite] = []

        for agent in list(self.living_agents()):
            if not self._can_reproduce(agent):
                continue

            fertility_bonus = agent.traits.resilience * 0.003
            chip_bonus = float(getattr(agent, "reproduction_boost", 0.0)) * 0.01
            memory_bonus = max(0.0, agent.action_memory.get("forage", 0.0)) * 0.002

            generation_penalty = self._generation_pressure(agent.generation) * 0.08
            birth_chance = 0.018 + fertility_bonus + chip_bonus + memory_bonus - generation_penalty

            if random.random() >= max(0.003, birth_chance):
                continue

            offspring_target = self._offspring_count_for_parent(agent)
            made = 0

            for _ in range(offspring_target):
                child = self._create_offspring(agent)
                if child is None:
                    break
                births_this_tick.append(child)
                made += 1

            if made == 0:
                continue

            generation_cost = 1.0 + self._generation_pressure(agent.generation) * 10.0

            energy_cost = 10.0 + 4.0 * (made - 1) + generation_cost
            nutrition_cost = 8.0 + 4.0 * (made - 1) + generation_cost * 0.8
            health_cost = 5.0 + 2.5 * (made - 1) + generation_cost * 0.6
            life_force_cost = 4.0 + 2.0 * (made - 1) + generation_cost * 0.5

            agent.energy = max(0.0, agent.energy - energy_cost)
            agent.nutrition = max(0.0, agent.nutrition - nutrition_cost)
            agent.health = max(0.0, agent.health - health_cost)
            agent.life_force = max(0.0, agent.life_force - life_force_cost)
            agent.reproduction_load = min(100.0, agent.reproduction_load + 18.0 + 6.0 * (made - 1))
            agent.births += made

            agent.reproduction_boost = max(0.0, agent.reproduction_boost - made)

            if made == 1:
                self._last_log = f"{agent.name} reproduced -> 1 child"
            elif made == 2:
                self._last_log = f"{agent.name} reproduced -> twins"
            else:
                self._last_log = f"{agent.name} reproduced -> triplets"

        for child in births_this_tick:
            self.add_agent(child)

    def _counts_by_generation(self, agents: list[Any]) -> dict[int, int]:
        counts: dict[int, int] = {}
        for agent in agents:
            gen = int(getattr(agent, "generation", 1))
            counts[gen] = counts.get(gen, 0) + 1
        return counts

    def _births_by_generation(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for agent in self.agents:
            gen = int(getattr(agent, "generation", 1))
            births = int(getattr(agent, "births", 0))
            counts[gen] = counts.get(gen, 0) + births
        return counts

    def _ages_of_dead(self) -> list[int]:
        return [int(getattr(a, "age_ticks", 0)) for a in self.dead_agents()]

    def _longest_lived_agents(self, top_n: int = 5) -> list[Simulite]:
        return sorted(
            self.agents,
            key=lambda a: int(getattr(a, "age_ticks", 0)),
            reverse=True,
        )[:top_n]

    def get_dashboard_stats(self) -> dict[str, int | float | str | list[float]]:
        living = self.living_agents()
        dead = self.dead_agents()

        def avg_attr(attr: str) -> float:
            if not living:
                return 0.0
            return sum(float(getattr(a, attr, 0.0)) for a in living) / len(living)

        max_generation = 0
        if self.agents:
            max_generation = max(int(getattr(a, "generation", 1)) for a in self.agents)

        total_births = sum(int(getattr(a, "births", 0)) for a in self.agents)

        return {
            "tick": self.tick_count,
            "ticks": self.tick_count,
            "population": len(living),
            "alive": len(living),
            "dead": len(dead),
            "food_count": len(self.food),
            "food": len(self.food),
            "chip_count": len(self.chips),
            "avg_life_force": round(avg_attr("life_force"), 2),
            "avg_health": round(avg_attr("health"), 2),
            "avg_energy": round(avg_attr("energy"), 2),
            "avg_nutrition": round(avg_attr("nutrition"), 2),
            "avg_rest": round(avg_attr("rest"), 2),
            "avg_exercise": round(avg_attr("exercise"), 2),
            "avg_social": round(avg_attr("social"), 2),
            "avg_speed": round(avg_attr("speed"), 2),
            "avg_agility": round(avg_attr("agility"), 2),
            "births": total_births,
            "deaths": len(dead),
            "max_generation": max_generation,
            "generation_limit": self.max_generation_limit,
            "trend": self._compute_trend(),
            "population_history": self._history("population"),
            "life_force_history": self._history("avg_life_force"),
            "health_history": self._history("avg_health"),
            "energy_history": self._history("avg_energy"),
            "nutrition_history": self._history("avg_nutrition"),
            "rest_history": self._history("avg_rest"),
            "exercise_history": self._history("avg_exercise"),
            "social_history": self._history("avg_social"),
            "speed_history": self._history("avg_speed"),
            "agility_history": self._history("avg_agility"),
            "generation_history": self._history("avg_generation"),
            "deaths_history": self._history("deaths_total"),
        }

    def summary(self) -> str:
        living = self.living_agents()
        dead = self.dead_agents()

        zone_counts: dict[str, int] = {}
        for agent in living:
            zone = self.get_zone(agent.x, agent.y)
            zone_counts[zone] = zone_counts.get(zone, 0) + 1

        total_births = sum(int(getattr(a, "births", 0)) for a in self.agents)
        max_generation = max(
            (int(getattr(a, "generation", 1)) for a in self.agents),
            default=1,
        )

        living_by_generation = self._counts_by_generation(living)
        dead_by_generation = self._counts_by_generation(dead)
        births_by_generation = self._births_by_generation()

        dead_ages = self._ages_of_dead()
        avg_age_at_death = sum(dead_ages) / len(dead_ages) if dead_ages else 0.0

        longest_lived = self._longest_lived_agents()

        lines = [
            "=== Simulation Metrics Summary ===",
            f"Rows: {len(self.metrics_history)}",
            f"Ticks recorded: 1 to {self.tick_count}",
            f"Final population: {len(living)}",
            f"Total births: {total_births}",
            f"Max generation: {max_generation}",
            f"Generation limit: {self.max_generation_limit}",
            f"Total deaths: {len(dead)}",
            f"Average age at death: {avg_age_at_death:.2f}",
            f"Food on grid: {len(self.food)}",
            f"Chips on grid: {len(self.chips)}",
        ]

        if living:
            lines.extend(
                [
                    f"Average Life Force: {sum(a.life_force for a in living) / len(living):.2f}",
                    f"Average Health: {sum(a.health for a in living) / len(living):.2f}",
                    f"Average Energy: {sum(a.energy for a in living) / len(living):.2f}",
                    f"Average Nutrition: {sum(a.nutrition for a in living) / len(living):.2f}",
                    f"Average Rest: {sum(a.rest for a in living) / len(living):.2f}",
                    f"Average Exercise: {sum(a.exercise for a in living) / len(living):.2f}",
                    f"Average Social: {sum(a.social for a in living) / len(living):.2f}",
                    f"Average Speed: {sum(a.speed for a in living) / len(living):.2f}",
                    f"Average Agility: {sum(a.agility for a in living) / len(living):.2f}",
                ]
            )

        if living_by_generation:
            lines.append("Living by generation:")
            for gen, count in sorted(living_by_generation.items()):
                lines.append(f"  - Gen {gen}: {count}")

        if dead_by_generation:
            lines.append("Dead by generation:")
            for gen, count in sorted(dead_by_generation.items()):
                lines.append(f"  - Gen {gen}: {count}")

        if births_by_generation:
            lines.append("Births by parent generation:")
            for gen, count in sorted(births_by_generation.items()):
                lines.append(f"  - Gen {gen}: {count}")

        if zone_counts:
            lines.append("Living agents by zone:")
            for zone_name, count in sorted(zone_counts.items()):
                lines.append(f"  - {zone_name}: {count}")

        if longest_lived:
            lines.append("Longest-lived agents:")
            for agent in longest_lived[:5]:
                lines.append(
                    f"  - {agent.name}: age {int(getattr(agent, 'age_ticks', 0))}, "
                    f"Gen {int(getattr(agent, 'generation', 1))}, "
                    f"{'alive' if getattr(agent, 'alive', False) else 'dead'}"
                )

        if self.deaths_by_cause:
            lines.append("Deaths by cause:")
            for cause, count in sorted(self.deaths_by_cause.items()):
                lines.append(f"  - {cause}: {count}")

        return "\n".join(lines)

    def save_metrics(self, path: str | Path = "outputs/simulation_metrics.csv") -> None:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.metrics_history:
            return

        fieldnames = list(self.metrics_history[0].keys())
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics_history)

    def step(self) -> None:
        self.tick_count += 1
        previous_dead_names = {a.name for a in self.dead_agents()}

        self._last_log = f"Tick {self.tick_count}"

        if self.tick_count % 3 == 0:
            self.sprinkle_food(count=3)

        if self.tick_count % 5 == 0:
            self.sprinkle_chips(count=3)

        zone_lookup = self.zone_lookup()

        for agent in self.living_agents():
            old_pos = (agent.x, agent.y)

            current_zone = self.get_zone(agent.x, agent.y)
            agent.step(current_zone=current_zone)

            agent.move_random(
                self.grid.width,
                self.grid.height,
                self.food,
                zone_lookup,
                self.chips,
            )

            self._apply_zone_effects(agent)
            self._feed_agent_if_on_food(agent)
            self._collect_chip_if_on_tile(agent)

            new_pos = (agent.x, agent.y)
            if old_pos != new_pos:
                zone = self.get_zone(agent.x, agent.y)
                self._last_log = f"{agent.name} moved to {new_pos} ({zone})"

        for agent in self.living_agents():
            self._attempt_help(agent)

        self._attempt_reproduction()
        self._record_new_deaths(previous_dead_names)
        self._record_metrics()
        self.save_metrics()
