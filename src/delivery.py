class Delivery:
    def __init__(self, id, pos, weight, priority, time_window):
        self.id = id
        self.pos = pos                  # (x, y)
        self.weight = weight            # float (kg)
        self.priority = priority        # int (1-5)
        self.time_window = time_window  # ("09:00", "10:00")

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]
    
    def __repr__(self):
        return f"Delivery({self.id}, {self.pos}, {self.weight}kg, priority={self.priority}, window={self.time_window})"
