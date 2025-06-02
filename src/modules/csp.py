from datetime import datetime
import math
import time
from modules.astar import astar

def convert_to_minutes(value):
    if isinstance(value, int):
        return value
    elif isinstance(value, str):
        try:
            dt = datetime.strptime(value, "%H:%M")
            return dt.hour * 60 + dt.minute
        except ValueError:
            return 0
    return 0

def assign_drones_one_delivery_each(drones, deliveries, graph, positions, noflyzones, current_time=None, scenario=1):
    start_time = time.time()
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
                break

            if delivery.weight > drone.max_weight:
                continue

            start_node = nearest_node(drone.start_pos)

            path, _, total_distance = astar(
                graph,
                start_node,
                delivery.id,
                positions,
                drone.speed,
                noflyzones=noflyzones,
                current_time=current_time,
                scenario=scenario
            )

            if not path:
                continue

            required_battery = total_distance * BATTERY_CONSUMPTION_PER_METER
            if drone.battery < required_battery:
                continue

            travel_time = round(total_distance / drone.speed, 2)

            if delivery.time_window:
                window_start, window_end = delivery.time_window

                # arrival_time hesapla (dakika cinsinden)
                arrival_time = current_time + travel_time if current_time is not None else travel_time

                # Saat biçiminde gelirse dakikaya çevir
                start_minutes = convert_to_minutes(window_start)
                end_minutes = convert_to_minutes(window_end)

                if not (start_minutes <= arrival_time <= end_minutes):
                    continue

            drone.battery -= required_battery
            assignments.append({
                'drone_id': drone.id,
                'delivery_id': delivery.id,
                'path': path,
                'distance': total_distance,
                'time': travel_time,
                'battery_left': round(drone.battery, 2)
            })
            assigned_deliveries.add(delivery.id)
            assigned = True
            break

    duration = time.time() - start_time
    return assignments, duration, len(assignments)