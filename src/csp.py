from datetime import datetime

def time_in_window(current_time, time_window):
    """ 
    current_time ve time_window ('HH:MM' string) ile kontrol eder.
    """
    start = datetime.strptime(time_window[0], "%H:%M").time()
    end = datetime.strptime(time_window[1], "%H:%M").time()

    return start <= current_time <= end


def is_in_no_fly_zone(pos, no_fly_zones):
    """
    pos: (x, y)
    no_fly_zones: liste, her biri {"coordinates": [(x1,y1), (x2,y2), ...]} (poligon)
    
    Basit kutu içinde kontrol yapar (bounding box)
    """
    x, y = pos
    for zone in no_fly_zones:
        xs = [c[0] for c in zone["coordinates"]]
        ys = [c[1] for c in zone["coordinates"]]
        if min(xs) <= x <= max(xs) and min(ys) <= y <= max(ys):
            return True
    return False


def is_valid_path(drone, delivery_list, no_fly_zones, route=None, start_time_str="08:00", speed=10):
    """
    - drone: Drone objesi
    - delivery_list: Delivery objeleri listesi
    - no_fly_zones: no fly zone verisi (liste)
    - route: [(x,y), ...] listesi (astar'dan gelen rota)
    - start_time_str: drone'nun kalkış saati string olarak 'HH:MM'
    - speed: birim zamanda (örneğin 1 dakika) kat edilen mesafe

    Kontroller:
    1) Kapasite aşımı
    2) Zaman penceresi uyumu
    3) No-fly zone ihlali
    """

    # 1) Kapasite kontrolü
    total_weight = sum(d.weight for d in delivery_list)
    if total_weight > drone.max_weight:
        print("Kapasite aşıldı!")
        return False

    # 2) Zaman penceresi kontrolü
    # Basit zaman simülasyonu: start_time + rota boyunca mesafeye göre süre hesapla
    current_time = datetime.strptime(start_time_str, "%H:%M")

    def distance(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

    # route içindeki teslimat pozisyonlarına göre zaman kontrolü
    if route is None:
        print("Rota yok, zaman kontrolü yapılamıyor.")
        return False

    # İlk pozisyon drone'nun başlangıç pozisyonu, sonra teslimat noktaları
    for i in range(1, len(route)):
        travel_dist = distance(route[i-1], route[i])
        travel_time_minutes = travel_dist / speed * 60  # speed: birim/saat ise bunu ayarla
        current_time = current_time + timedelta(minutes=travel_time_minutes)

        # Eğer rota üzerindeki nokta teslimat noktası ise (kontrol et)
        for d in delivery_list:
            if route[i] == d.pos:
                # teslimatın zaman penceresine uyuyor mu?
                if not time_in_window(current_time.time(), d.time_window):
                    print(f"Teslimat {d.id} zaman penceresi dışı! Zaman: {current_time.time()} Pencere: {d.time_window}")
                    return False

    # 3) No-fly zone kontrolü (rota üzerindeki her pozisyonu kontrol et)
    for pos in route:
        if is_in_no_fly_zone(pos, no_fly_zones):
            print(f"No-fly zone ihlali pozisyon: {pos}")
            return False

    return True
