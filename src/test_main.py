# test_main.py

import json
from drone import Drone
from delivery import Delivery
from astar import find_path
from csp import is_valid_path

# Veriyi yükle
with open("veri.json", "r") as f:
    data = json.load(f)

drones = [Drone(**d) for d in data["drones"]]
deliveries = [Delivery(**d) for d in data["deliveries"]]
no_fly_zones = data["no_fly_zones"]

# Örnek drone ve delivery
drone = drones[0]
delivery_list = deliveries[:5]

# CSP kontrol
if is_valid_path(drone, delivery_list, no_fly_zones):
    route = find_path(drone, delivery_list, no_fly_zones)
    print("Uygun rota:", route)
else:
    print("Bu teslimat listesi drone için uygun değil.")
