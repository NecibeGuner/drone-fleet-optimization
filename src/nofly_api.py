from shapely.geometry import Polygon
from random import choice
from datetime import datetime

# noflyzone.py dosyanız varsa bu importu kullanabilirsiniz, yoksa silinebilir
# from noflyzone import NoFlyZone 

def get_dynamic_nofly_zones(current_time: str, weather: str = None):
    """
    Saat ve hava durumuna göre aktif ve pasif no-fly bölgelerini döndürür.
    Dönüş değeri doğrudan Shapely Polygon objeleridir.
    """
    def is_time_in_range(now_str: str, start_str: str, end_str: str) -> bool:
        now_dt = datetime.strptime(now_str, "%H:%M")
        start_dt = datetime.strptime(start_str, "%H:%M")
        end_dt = datetime.strptime(end_str, "%H:%M")
        
        # Gece yarısı geçişlerini doğru ele almak için
        if start_dt <= end_dt:
            return start_dt <= now_dt <= end_dt
        else: # Örneğin, 22:00 - 06:00 gibi gece yarısını geçen aralıklar
            return now_dt >= start_dt or now_dt <= end_dt

    # Zaman bazlı statik no-fly bölgeleri
    all_zones_data = [
        {"id": 1, "start": "08:00", "end": "12:00", "coords": [(10, 10), (20, 10), (20, 20), (10, 20)]},
        {"id": 2, "start": "14:00", "end": "18:00", "coords": [(40, 40), (50, 40), (50, 50), (40, 50)]},
        {"id": 3, "start": "00:00", "end": "23:59", "coords": [(60, 10), (65, 10), (65, 20), (60, 20)]}
    ]

    # Hava durumu bazlı dinamik no-fly bölgeleri
    weather_zones = [
        {"id": 4, "start": "00:00", "end": "23:59", "weather": ["storm", "windy"], "coords": [(70, 70), (80, 70), (80, 80), (70, 80)]},
        {"id": 5, "start": "06:00", "end": "22:00", "weather": ["foggy", "rainy"], "coords": [(30, 60), (40, 60), (40, 70), (30, 70)]}
    ]

    active_polygons = []
    passive_polygons = []

    # Zaman bazlı bölgeleri kontrol et
    for z in all_zones_data:
        polygon = Polygon(z["coords"])
        if is_time_in_range(current_time, z["start"], z["end"]):
            active_polygons.append(polygon)
        else:
            passive_polygons.append(polygon)

    # Hava durumu bazlı bölgeleri kontrol et
    if weather:
        for wz in weather_zones:
            polygon = Polygon(wz["coords"])
            # Hava durumu listede varsa ve zaman aralığındaysa aktif yap
            if is_time_in_range(current_time, wz["start"], wz["end"]) and weather.lower() in [w.lower() for w in wz["weather"]]:
                active_polygons.append(polygon)
            else:
                passive_polygons.append(polygon)

    return active_polygons, passive_polygons

def get_random_weather():
    """
    Rastgele bir hava durumu döndürür.
    'extreme' seçeneği eklendi.
    """
    return choice(["clear", "windy", "storm", "foggy", "rainy", "extreme"])