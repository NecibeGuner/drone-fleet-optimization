import random
import copy
import math
import matplotlib.pyplot as plt
from modules.astar import astar  # A* fonksiyonu

def create_individual(num_drones, deliveries):
    """Her drone’a rastgele, eşit sayıda teslimat ID’si assign eder."""
    individual = [[] for _ in range(num_drones)]
    delivery_ids = [d.id for d in deliveries]
    random.shuffle(delivery_ids)
    for i, did in enumerate(delivery_ids):
        individual[i % num_drones].append(did)
    return individual

def nearest_node(pos, positions):
    """Verilen (x,y) pozisyonuna en yakın graph düğümünü bulur."""
    x, y = pos
    return min(positions.keys(),
               key=lambda n: math.hypot(positions[n][0] - x,
                                        positions[n][1] - y))

def fitness(individual, drones, graph, positions,
            battery_consumption_rate, deliveries, nofly_zones):
    """
    Fitness = 50*T - 0.1*E - 1000*V
      T = toplam başarılı teslimat adedi
      E = toplam harcanan enerji
      V = ihlâl edilen kısıt sayısı
    """
    drones_copy = [copy.deepcopy(d) for d in drones]
    deliveries_dict = {d.id: d for d in deliveries}

    total_deliveries = 0
    total_energy = 0.0
    violation_count = 0

    for di, route in enumerate(individual):
        drone = drones_copy[di]
        current = nearest_node(drone.start_pos, positions)

        for did in route:
            if did not in deliveries_dict:
                violation_count += 1
                continue

            delivery = deliveries_dict[did]

            if delivery.weight > drone.max_weight:
                violation_count += 1
                continue

            path, _, dist = astar(
                graph, current, did, positions,
                drone.speed, noflyzones=nofly_zones
            )
            if not path:
                violation_count += 1
                continue

            energy = dist * battery_consumption_rate
            if drone.battery < energy:
                violation_count += 1
                continue

            drone.battery -= energy
            total_energy += energy
            total_deliveries += 1
            current = did

    return (50 * total_deliveries) -( 0.1 * total_energy) - (1000 * violation_count)

def crossover(p1, p2):
    """Single‐point: bir drone index’inde tüm rotayı swap et."""
    c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
    idx = random.randrange(len(p1))
    c1[idx], c2[idx] = c2[idx], c1[idx]
    return c1, c2

def mutate(ind, rate=0.1):
    """Her drone’daki rota listesinde swap mutasyon."""
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
    """Mesafeyi okunabilir biçimde döndürür."""
    return f"{distance:.2f} m"

def genetic_algorithm(drones, deliveries, graph, positions,
                      nofly_zones, battery_consumption_rate,
                      population_size= 1000, generations=10):  
    pop = [create_individual(len(drones), deliveries)
           for _ in range(population_size)]
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

        ranked = [ind for _, ind in sorted(
            zip(scores, pop), key=lambda x: x[0], reverse=True)]
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
