import json
import os
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone

def load_data():
    # veri.json dosyasının yolunu belirt (src/data/veri.json)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'data', 'veri.json')

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Drone objelerini oluştur
    drones = [Drone(**d) for d in data['drones']]

    # Delivery objelerini oluştur
    deliveries = [Delivery(**d) for d in data['deliveries']]

    # NoFlyZone objelerini oluştur
    nofly_zones = [NoFlyZone(**z) for z in data['no_fly_zones']]

    return drones, deliveries, nofly_zones
