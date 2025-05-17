import random
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone
import json

def generate_drones(n):
    drones = []
    for i in range(n):
        drone = Drone(
            id=i,
            max_weight=round(random.uniform(3, 10), 2),
            battery=random.randint(3000, 10000),
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

# Veri oluşturma
drones = generate_drones(5)
deliveries = generate_deliveries(20)
zones = generate_no_fly_zones(2)

# JSON dosyasına kaydetme
data = {
    "drones": [vars(d) for d in drones],
    "deliveries": [vars(d) for d in deliveries],
    "no_fly_zones": [vars(z) for z in zones]
}

with open("veri.json", "w") as f:
    json.dump(data, f, indent=4)

print("Veriler veri.json dosyasına kaydedildi.")
