# delivery.py

class Delivery:
    def __init__(self, id, pos, weight, priority, time_window):
        self.id = id
        self.pos = pos
        self.weight = weight
        self.priority = priority
        self.time_window = time_window

    def __repr__(self):
        return f"Delivery(id={self.id}, pos={self.pos}, weight={self.weight}, priority={self.priority}, time_window={self.time_window})"
