import random
import json
from datetime import datetime
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone

def parse_time_window(start_str, end_str):
    return (
        datetime.strptime(start_str, "%H:%M").time(),
        datetime.strptime(end_str, "%H:%M").time()
    )

def time_to_string(t):
    return t.strftime("%H:%M")

def generate_drones(n):
    drones = []
    for i in range(n):
        battery_capacity = random.randint(4000, 10000)  # mAh
        battery_level = round(random.uniform(0.3, 1.0), 2)  # %30 ile %100 arası şarj
        drone = Drone(
            id=i,
            max_weight=round(random.uniform(3.0, 10.0), 2),
            battery=battery_capacity,
            battery_level=battery_level,
            speed=round(random.uniform(5.0, 15.0), 2),
            start_pos=(random.randint(0, 100), random.randint(0, 100))
        )
        drones.append(drone)
    return drones

def generate_deliveries(n):
    deliveries = []
    for i in range(n):
        time_window = parse_time_window("09:00", "12:00")
        delivery = Delivery(
            id=i,
            pos=(random.randint(0, 100), random.randint(0, 100)),
            weight=round(random.uniform(0.5, 5.0), 2),
            priority=random.randint(1, 5),
            time_window=time_window
        )
        deliveries.append(delivery)
    return deliveries

def generate_no_fly_zones(n):
    zones = []
    for i in range(n):
        coords = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(4)]
        active_time = parse_time_window("09:30", "11:00")
        zone = NoFlyZone(
            id=i,
            coordinates=coords,
            active_time=active_time
        )
        zones.append(zone)
    return zones

def main():
    drones = generate_drones(5)
    deliveries = generate_deliveries(20)
    zones = generate_no_fly_zones(2)

    data = {
        "drones": [d.__dict__ for d in drones],
        "deliveries": [
            {
                **d.__dict__,
                "time_window": [time_to_string(d.time_window[0]), time_to_string(d.time_window[1])]
            }
            for d in deliveries
        ],
        "no_fly_zones": [
            {
                **z.__dict__,
                "active_time": [time_to_string(z.active_time[0]), time_to_string(z.active_time[1])]
            }
            for z in zones
        ]
    }

    with open("veri.json", "w") as f:
        json.dump(data, f, indent=4)

    print("veri.json dosyası başarıyla oluşturuldu.")

if __name__ == "__main__":
    main()
