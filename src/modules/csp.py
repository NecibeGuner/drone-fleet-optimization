import math
from modules.astar import astar

def assign_drones_one_delivery_each(drones, deliveries, graph, positions, noflyzones):
    assignments = []
    assigned_deliveries = set()
    BATTERY_CONSUMPTION_PER_METER = 0.1

    def nearest_node(pos):
        x, y = pos
        return min(positions.keys(), key=lambda node: math.hypot(positions[node][0] - x, positions[node][1] - y))

    for drone in drones:
        if not hasattr(drone, 'battery'):
            drone.battery = 100.0

    for delivery in deliveries:
        assigned = False
        for drone in drones:
            if delivery.id in assigned_deliveries:
                break  # Zaten atanmış

            if delivery.weight > drone.max_weight:
                continue  # Drone ağırlık sınırını aşar

            start_node = nearest_node(drone.start_pos)
            path, _, total_distance = astar(graph, start_node, delivery.id, positions, drone.speed, noflyzones=noflyzones)
            if not path:
                continue  # No-fly zone ihlali olabilir ya da yol yok

            required_battery = total_distance * BATTERY_CONSUMPTION_PER_METER
            if drone.battery < required_battery:
                continue  # Batarya yetmez

            # Atama yapılabilir
            drone.battery -= required_battery
            time = round(total_distance / drone.speed, 2)
            assignments.append({
                'drone_id': drone.id,
                'delivery_id': delivery.id,
                'path': path,
                'distance': total_distance,
                'time': time,
                'battery_left': drone.battery
            })
            assigned_deliveries.add(delivery.id)
            assigned = True
            break  # Drone sadece 1 paket taşıyabilir, sıradaki drone'ya geç

        if not assigned:
            print(f"Delivery {delivery.id} could not be assigned to any drone.")

    return assignments
