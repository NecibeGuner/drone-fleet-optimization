import random
import copy
import math
import matplotlib.pyplot as plt
from modules.astar import astar

def create_individual(num_drones, deliveries):
    """Rastgele bir çözüm üretir: her drone’a rastgele teslimat atar."""
    individual = [[] for _ in range(num_drones)]
    delivery_ids = [d.id for d in deliveries]
    random.shuffle(delivery_ids)
    for i, delivery_id in enumerate(delivery_ids):
        individual[i % num_drones].append(delivery_id)
    return individual

def nearest_node(pos, positions):
    x, y = pos
    return min(positions.keys(), key=lambda node: math.hypot(positions[node][0] - x, positions[node][1] - y))

def fitness(individual, drones, deliveries, graph, positions, battery_consumption_rate):
    total_deliveries = 0
    total_energy = 0
    penalty = 0

    for drone_idx, delivery_ids in enumerate(individual):
        drone = drones[drone_idx]
        battery = 100.0
        current_node = nearest_node(drone.start_pos, positions)

        for delivery_id in delivery_ids:
            delivery = next((d for d in deliveries if d.id == delivery_id), None)
            if not delivery or delivery.weight > drone.max_weight:
                penalty += 500
                continue

            path, _, distance = astar(graph, current_node, delivery.id, positions, drone.speed)
            if not path:
                penalty += 1000
                continue

            energy_needed = distance * battery_consumption_rate
            if battery < energy_needed:
                penalty += 500
                continue

            battery -= energy_needed
            total_energy += energy_needed
            total_deliveries += 1
            current_node = delivery.id

    # Fitness = başarı - ceza - enerji
    a, b, c = 10, 5, 20
    return a * total_deliveries - b * total_energy - c * penalty

def crossover(parent1, parent2):
    """Basit tek noktalı crossover: bir drone’un görevlerini değiştirir."""
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    idx = random.randint(0, len(parent1) - 1)
    child1[idx], child2[idx] = child2[idx], child1[idx]
    return child1, child2

def mutate(individual, mutation_rate=0.1):
    """Tesadüfi iki teslimatı yer değiştirir."""
    for drone_deliveries in individual:
        if random.random() < mutation_rate and len(drone_deliveries) > 1:
            i, j = random.sample(range(len(drone_deliveries)), 2)
            drone_deliveries[i], drone_deliveries[j] = drone_deliveries[j], drone_deliveries[i]

def plot_fitness_evolution(best_fitness_list):
    plt.figure(figsize=(10, 5))
    plt.plot(best_fitness_list, marker='o', linestyle='-', color='blue')
    plt.title("Best Fitness per Generation")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def genetic_algorithm(
    drones, deliveries, graph, positions, nofly_zones,
    battery_consumption_rate, population_size=20, generations=50
):
    population = [create_individual(len(drones), deliveries) for _ in range(population_size)]
    best_fitness_list = []

    for gen in range(generations):
        fitness_scores = [fitness(ind, drones, deliveries, graph, positions, battery_consumption_rate) for ind in population]
        best_fitness = max(fitness_scores)
        best_fitness_list.append(best_fitness)
        print(f"Generation {gen}: Best fitness = {best_fitness}")

        # En iyilerin yarısını seç
        selected = [
            ind for _, ind in sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)[:population_size // 2]
        ]

        # Çocuk üretimi
        children = []
        while len(children) < population_size:
            p1, p2 = random.sample(selected, 2)
            c1, c2 = crossover(p1, p2)
            mutate(c1)
            mutate(c2)
            children.extend([c1, c2] if len(children) + 2 <= population_size else [c1])
        population = children

    # En iyi çözümü döndür
    fitness_scores = [fitness(ind, drones, deliveries, graph, positions, battery_consumption_rate) for ind in population]
    best_index = fitness_scores.index(max(fitness_scores))
    plot_fitness_evolution(best_fitness_list)
    return population[best_index]
