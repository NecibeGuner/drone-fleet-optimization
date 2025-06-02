import json
import time
import random
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone
from nofly_api import get_dynamic_nofly_zones  # sahte API desteği için
from shapely.geometry import Polygon

def generate_drones(n):
    return [
        Drone(
            id=i,
            max_weight=5.0,
            battery=100.0,
            battery_level=1.0,
            speed=10.0,
            start_pos=(random.randint(0, 30), random.randint(0, 30))
        )
        for i in range(n)
    ]

def generate_deliveries(n):
    return [
        Delivery(
            id=i,
            pos=(random.randint(40, 100), random.randint(40, 100)),
            weight=round(random.uniform(1.0, 4.0), 2),
            priority=random.randint(1, 5),
            time_window=("09:00", "11:00")
        )
        for i in range(n)
    ]
from shapely.geometry import Polygon

def generate_noflyzones(n, dynamic=False):
    zones = []
    for i in range(n):
        x1, y1 = random.randint(20, 60), random.randint(20, 60)
        x2, y2 = x1 + random.randint(5, 15), y1 + random.randint(5, 15)

        if dynamic:
            start_hour = random.randint(8, 10)
            end_hour = start_hour + random.randint(1, 3)
            start_min = random.choice([0, 15, 30, 45])
            end_min = (start_min + 30) % 60
            active_time = (f"{start_hour:02d}:{start_min:02d}", f"{end_hour:02d}:{end_min:02d}")
        else:
            active_time = ("00:00", "23:59")

        zone = NoFlyZone(
            id=i,
            coordinates=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
            active_time=active_time
        )
        zones.append(zone.polygon)  # 🔁 Sadece polygon'u alıyoruz
    return zones



def load_data(scenario=1, json_path=None):
    if json_path:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        drones = [Drone(**d) for d in data["drones"]]
        deliveries = [Delivery(**d) for d in data["deliveries"]]

        nofly_zones = []
        for z in data.get("nofly_zones", []):
            coords = z.get("coordinates")
            if coords:
                polygon = Polygon(coords)
                nofly_zones.append(polygon)

        print(f"✅ JSON'dan yüklenen no-fly bölgesi sayısı: {len(nofly_zones)}")  # DEBUG için

        return drones, deliveries, nofly_zones

    if scenario == 1:
        drones = generate_drones(5)
        deliveries = generate_deliveries(20)
        nofly_zones = generate_noflyzones(2, dynamic=False)

    elif scenario == 2:
        drones = generate_drones(10)
        deliveries = generate_deliveries(50)
        current_time = time.strftime("%H:%M")
        nofly_zones = get_dynamic_nofly_zones(current_time)

    else:
        raise ValueError("Geçersiz senaryo. 1, 2 veya bir JSON dosya yolu belirtmelisin.")

    return drones, deliveries, nofly_zones


