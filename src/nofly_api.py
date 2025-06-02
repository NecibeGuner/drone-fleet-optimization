from shapely.geometry import Polygon
from random import choice
from datetime import datetime
from noflyzone import NoFlyZone  # varsa bu importu kullan

from shapely.geometry import Polygon
from datetime import datetime
from noflyzone import NoFlyZone

def get_dynamic_nofly_zones(current_time: str, weather: str = None):
    """
    Dinamik No-Fly bölgelerini saat ve hava durumuna göre döner.
    """

    def is_time_in_range(now: str, start: str, end: str) -> bool:
        now_dt = datetime.strptime(now, "%H:%M")
        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")
        return start_dt <= now_dt <= end_dt

    all_zones_data = [
        {"id": 1, "start": "08:00", "end": "12:00", "coords": [(10, 10), (20, 10), (20, 20), (10, 20)]},
        {"id": 2, "start": "14:00", "end": "18:00", "coords": [(40, 40), (50, 40), (50, 50), (40, 50)]},
        {"id": 3, "start": "00:00", "end": "23:59", "coords": [(60, 10), (65, 10), (65, 20), (60, 20)]}
    ]

    weather_zones = [
        {"id": 4, "start": "00:00", "end": "23:59", "weather": ["storm", "windy"], "coords": [(70, 70), (80, 70), (80, 80), (70, 80)]},
        {"id": 5, "start": "06:00", "end": "22:00", "weather": ["foggy", "rainy"], "coords": [(30, 60), (40, 60), (40, 70), (30, 70)]}
    ]

    active_zones = []

    for zone in all_zones_data:
        if is_time_in_range(current_time, zone["start"], zone["end"]):
            polygon = Polygon(zone["coords"])
            active_zones.append(polygon)

    if weather:
        for wz in weather_zones:
            if is_time_in_range(current_time, wz["start"], wz["end"]) and weather in wz["weather"]:
                polygon = Polygon(wz["coords"])
                active_zones.append(polygon)

    return active_zones  # sadece Polygon listesi dönüyoruz



def get_random_weather():
    """
    Hava durumu rastgele döndürülür.
    """
    return choice(["clear", "windy", "storm", "foggy", "rainy"])
