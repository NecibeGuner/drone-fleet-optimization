# drone.py
class Drone:
    def __init__(self, id, start_pos, max_weight, battery, battery_level, speed):
        self.id = id
        self.start_pos = start_pos # (x, y) tuple
        self.max_weight = max_weight
        self.battery = battery # mAh cinsinden toplam batarya kapasitesi
        self.current_mah = battery # Anlık batarya seviyesi, başlangıçta tam dolu
        self.battery_level = battery_level # Yüzde cinsinden (0.0 - 1.0)
        self.speed = speed # m/s
        self.assigned_deliveries = [] # Atanan teslimatların listesi

    def __repr__(self):
        return f"Drone(ID:{self.id}, Pos:{self.start_pos}, Bat:{self.current_mah:.1f}/{self.battery:.1f}, Spd:{self.speed:.1f}, W:{self.max_weight:.1f})"