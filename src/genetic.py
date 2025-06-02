import random
import copy
import math
import matplotlib.pyplot as plt
from modules.astar import astar
from shapely.geometry import LineString
from datetime import datetime

def create_individual(num_drones, deliveries):
    individual = [[] for _ in range(num_drones)]
    delivery_ids = [d.id for d in deliveries]
    random.shuffle(delivery_ids)
    for i, did in enumerate(delivery_ids):
        individual[i % num_drones].append(did)
    return individual

def nearest_node(pos, positions):
    x, y = pos
    return min(positions.keys(), key=lambda n: math.hypot(positions[n][0] - x, positions[n][1] - y))

def violates_nofly_zone(path, positions, nofly_zones):
    if len(path) < 2:
        return False
    try:
        for i in range(len(path) - 1):
            segment = LineString([positions[path[i]], positions[path[i + 1]]])
            if any(segment.intersects(zone) for zone in nofly_zones):
                return True
        return False
    except Exception:
        return True

def violates_time_window(current_time, delivery):
    if hasattr(delivery, 'time_window'):
        earliest, latest = delivery.time_window
        try:
            earliest_minutes = int(datetime.strptime(earliest, "%H:%M").hour) * 60 + int(datetime.strptime(earliest, "%H:%M").minute)
            latest_minutes = int(datetime.strptime(latest, "%H:%M").hour) * 60 + int(datetime.strptime(latest, "%H:%M").minute)
            current_minutes = int(current_time * 60)
            return not (earliest_minutes <= current_minutes <= latest_minutes)
        except Exception:
            return False
    return False

def fitness(individual, drones, graph, positions,
            battery_consumption_rate, deliveries, nofly_zones):
    drones_copy = [copy.deepcopy(d) for d in drones]
    deliveries_dict = {d.id: d for d in deliveries}

    total_deliveries = 0
    total_energy = 0.0
    violation_count = 0

    for di, route in enumerate(individual):
        drone = drones_copy[di]
        current = nearest_node(drone.start_pos, positions)
        current_time = 0

        for did in route:
            if did not in deliveries_dict:
                violation_count += 1
                continue

            delivery = deliveries_dict[did]

            if delivery.weight > drone.max_weight:
                violation_count += 1
                continue

            path, _, dist = astar(graph, current, did, positions, drone.speed, noflyzones=nofly_zones)
            if not path:
                violation_count += 1
                continue

            if violates_nofly_zone(path, positions, nofly_zones):
                violation_count += 1
                continue

            energy = dist * battery_consumption_rate
            if drone.battery < energy:
                violation_count += 1
                continue

            if violates_time_window(current_time, delivery):
                violation_count += 1
                continue

            drone.battery -= energy
            total_energy += energy
            total_deliveries += 1
            current = did
            current_time += dist / drone.speed

    return (50 * total_deliveries) - (0.1 * total_energy) - (1000 * violation_count)

def crossover(p1, p2):
    c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
    idx = random.randrange(len(p1))
    c1[idx], c2[idx] = c2[idx], c1[idx]

    def remove_duplicates(individual):
        seen = set()
        all_ids = [did for route in individual for did in route]
        unique_ids = []
        for did in all_ids:
            if did not in seen:
                seen.add(did)
                unique_ids.append(did)
        cleaned = [[] for _ in range(len(individual))]
        for i, did in enumerate(unique_ids):
            cleaned[i % len(cleaned)].append(did)
        return cleaned

    return remove_duplicates(c1), remove_duplicates(c2)

def mutate(ind, rate=0.1):
    for route in ind:
        if random.random() < rate and len(route) > 1:
            i, j = random.sample(range(len(route)), 2)
            route[i], route[j] = route[j], route[i]

def plot_fitness_evolution(best_list):
    plt.figure(figsize=(10, 5))
    plt.plot(best_list, marker='o', linestyle='-')
    plt.title("Best Fitness per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def format_dist(distance):
    return f"{distance:.2f} m"

def genetic_algorithm(drones, deliveries, graph, positions,
                      nofly_zones, battery_consumption_rate,
                      population_size=1000, generations=25):
    pop = [create_individual(len(drones), deliveries) for _ in range(population_size)]
    best_history = []

    for gen in range(generations):
        scores = [
            fitness(ind, drones, graph, positions,
                    battery_consumption_rate,
                    deliveries, nofly_zones)
            for ind in pop
        ]
        best = max(scores)
        best_history.append(best)
        print(f"Gen {gen}: Best fitness = {best:.2f}")

        ranked = [ind for _, ind in sorted(zip(scores, pop), key=lambda x: x[0], reverse=True)]
        selected = ranked[:population_size // 2]

        next_pop = []
        while len(next_pop) < population_size:
            p1, p2 = random.sample(selected, 2)
            c1, c2 = crossover(p1, p2)
            mutate(c1)
            mutate(c2)
            next_pop.extend([c1, c2])
        pop = next_pop[:population_size]

    final_scores = [
        fitness(ind, drones, graph, positions,
                battery_consumption_rate,
                deliveries, nofly_zones)
        for ind in pop
    ]
    best_idx = final_scores.index(max(final_scores))
    plot_fitness_evolution(best_history)
    return pop[best_idx]