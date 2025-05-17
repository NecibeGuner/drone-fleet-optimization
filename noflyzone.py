class NoFlyZone:
    def __init__(self, id, coordinates, active_time):
        self.id = id
        self.coordinates = coordinates    # [(x1,y1), (x2,y2), ...]
        self.active_time = active_time    # ("09:30", "11:00")

    def __repr__(self):
        return f"NoFlyZone({self.id}, coords={self.coordinates}, time={self.active_time})"