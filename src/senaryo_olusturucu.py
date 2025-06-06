import random
import json
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone

def generate_drones(n):
    drones = []
    for i in range(n):
        drone = Drone(
            id=i,
            max_weight=round(random.uniform(3.0, 10.0), 2),
            battery=round(random.uniform(4000, 10000), 2),
            battery_level=round(random.uniform(0.3, 1.0), 2),
            speed=round(random.uniform(5.0, 15.0), 2),
            start_pos=(random.randint(0, 100), random.randint(0, 100))
        )
        drones.append(drone)
    return drones

def generate_deliveries(n):
    deliveries = []
    for i in range(n):
        delivery = Delivery(
            id=i,
            pos=(random.randint(0, 100), random.randint(0, 100)),
            weight=round(random.uniform(0.5, 5.0), 2),
            priority=random.randint(1, 5),
            time_window=("09:00", "12:00")
        )
        deliveries.append(delivery)
    return deliveries

def generate_no_fly_zones(n):
    zones = []
    for i in range(n):
        coords = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(4)]
        zone = NoFlyZone(
            id=i,
            coordinates=coords,
            active_time=("09:30", "11:00")
        )
        zones.append(zone)
    return zones

def generate_scenario(drone_count, delivery_count, zone_count, output_name):
    drones = generate_drones(drone_count)
    deliveries = generate_deliveries(delivery_count)
    zones = generate_no_fly_zones(zone_count)

    data = {
        "drones": [d.__dict__ for d in drones],
        "deliveries": [d.__dict__ for d in deliveries],
        "no_fly_zones": [z.__dict__ for z in zones]
    }

    # Aynı klasöre kaydedecek, klasör yolunu kaldırdım
    with open(f"{output_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"✅ {output_name}.json başarıyla oluşturuldu.")

if __name__ == "__main__":
    generate_scenario(5, 20, 2, "senaryo1")
    generate_scenario(10, 50, 5, "senaryo2")
