from datetime import datetime
from shapely.geometry import Polygon

class NoFlyZone:
    def __init__(self, id, coordinates, active_time):
        self.id = id
        self.coordinates = coordinates
        self.active_time = active_time
        self.polygon = Polygon(coordinates)  # çizim için kolaylık

    def is_active(self, current_time_str):
        """Zaman formatı: 'HH:MM'"""
        now = datetime.strptime(current_time_str, "%H:%M")
        start, end = [datetime.strptime(t, "%H:%M") for t in self.active_time]
        return start <= now <= end
