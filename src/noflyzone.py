# noflyzone.py

class NoFlyZone:
    def __init__(self, id, coordinates, active_time):
        self.id = id
        self.coordinates = coordinates
        self.active_time = active_time

    def __repr__(self):
        return f"NoFlyZone(id={self.id}, coordinates={self.coordinates}, active_time={self.active_time})"
