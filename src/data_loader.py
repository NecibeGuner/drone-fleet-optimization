import json
import os
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone

def load_data(file_name="veri.json"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'data', file_name)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # ... (dronelar, teslimatlar, no-fly zone objeleri üret)


    # Drone objelerini oluştur
    drones = [
        Drone(
            id=d["id"],
            max_weight=d["max_weight"],
            battery=d["battery"],
            battery_level=d.get("battery_level", 1.0),  # Default değer: %100
            speed=d["speed"],
            start_pos=tuple(d["start_pos"])
        )
        for d in data['drones']
    ]

    # Delivery objelerini oluştur
    deliveries = [
        Delivery(
            id=dlv["id"],
            pos=tuple(dlv["pos"]),
            weight=dlv["weight"],
            priority=dlv["priority"],
            time_window=tuple(dlv["time_window"])
        )
        for dlv in data['deliveries']
    ]

    # No-fly zone objelerini oluştur
    nofly_zones = [
        NoFlyZone(
            id=z["id"],
            coordinates=[tuple(coord) for coord in z["coordinates"]],
            active_time=tuple(z["active_time"])
        )
        for z in data['no_fly_zones']
    ]

    return drones, deliveries, nofly_zones
