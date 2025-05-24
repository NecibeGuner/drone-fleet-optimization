import math
from modules.astar import astar

def assign_drones_with_csp(drones, deliveries, graph, positions, noflyzones):
    assignments = []
    assigned_deliveries = set()
    BATTERY_CONSUMPTION_PER_METER = 0.1

    def nearest_node(pos):
        x, y = pos
        return min(positions.keys(), key=lambda node: math.hypot(positions[node][0] - x, positions[node][1] - y))

    for drone in drones:
        if not hasattr(drone, 'battery'):
            drone.battery = 100.0

        start_node = nearest_node(drone.start_pos)
        for delivery in deliveries:
            if delivery.id in assigned_deliveries:
                continue
            if delivery.weight > drone.max_weight:
                continue  # AĞIRLIK kontrolü

            path, _, total_distance = astar(graph, start_node, delivery.id, positions, drone.speed, noflyzones=noflyzones)
            if path:
                required_battery = total_distance * BATTERY_CONSUMPTION_PER_METER
                if drone.battery >= required_battery:
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
                    break
    return assignments
