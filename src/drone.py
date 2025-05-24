class Drone:
    def __init__(self, id, max_weight, battery, battery_level, speed, start_pos):
        self.id = id
        self.max_weight = max_weight      # float (kg)
        self.battery = battery            # int (mAh)
        self.battery_level = battery_level  # float (0.0 - 1.0)
        self.speed = speed                # float (m/s)
        self.start_pos = start_pos        # (x, y) tuple

    def __repr__(self):
        return f"Drone({self.id}, {self.max_weight}kg, {self.battery}mAh, {self.battery_level*100:.0f}%, {self.speed}m/s, {self.start_pos})"
