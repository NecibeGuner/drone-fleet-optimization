import json
import time
import random
from datetime import datetime, timedelta
from shapely.geometry import Polygon, Point # Point de eklendi
from drone import Drone # Drone sınıfınızın doğru import edildiğinden emin olun
from delivery import Delivery # Delivery sınıfınızın doğru import edildiğinden emin olun
from nofly_api import get_dynamic_nofly_zones # sahte API desteği için
from noflyzone import NoFlyZone # NoFlyZone sınıfınızın doğru import edildiğinden emin olun

# generate_drones ve generate_deliveries fonksiyonları, Drone ve Delivery sınıflarına bağlıdır.
# Bu sınıfların drone.py ve delivery.py dosyalarında tanımlı olduğunu varsayıyorum.

def generate_drones(n, graph_size=100):
    """
    Belirtilen sayıda drone oluşturur.
    """
    return [
        Drone(
            id=i,
            max_weight=random.uniform(3.0, 7.0), # Daha geniş ağırlık aralığı
            battery=random.uniform(10000.0, 20000.0), # Daha gerçekçi batarya değerleri (mAh)
            battery_level=1.0, # Başlangıçta tam dolu
            speed=random.uniform(10.0, 25.0), # Daha geniş hız aralığı (m/s)
            start_pos=(random.randint(0, graph_size // 3), random.randint(0, graph_size // 3)) # Başlangıçlar daha küçük bir alanda
        )
        for i in range(n)
    ]

def generate_deliveries(n, graph_size=100, current_time_dt=None):
    """
    Belirtilen sayıda teslimat oluşturur.
    Teslimatların zaman pencereleri, mevcut zamana göre ayarlanır.
    """
    deliveries = []
    
    # current_time_dt None gelirse, şu anki zamanı kullan
    if current_time_dt is None: # << BU KONTROL ÖNEMLİ
        current_time_dt = datetime.now()

    current_minutes_from_midnight = current_time_dt.hour * 60 + current_time_dt.minute + current_time_dt.second / 60

    for i in range(n):
        x = random.uniform(0, graph_size)
        y = random.uniform(0, graph_size)
        
        weight = round(random.uniform(0.5, 4.0), 2) # Daha gerçekçi ağırlıklar
        priority = random.randint(1, 5)

        # Zaman penceresi başlangıcı: mevcut zamandan 0 ila 30 dakika sonra
        window_start_offset = random.randint(0, 30)
        window_start_minutes = current_minutes_from_midnight + window_start_offset
        
        # Zaman penceresi bitişi: başlangıçtan 30 ila 90 dakika sonra
        window_duration = random.randint(30, 90)
        window_end_minutes = window_start_minutes + window_duration

        # Zaman pencerelerinin 24 saati (1440 dakika) aşmamasını sağlamak için mod alma
        # Bu, gece yarısı geçişlerini de doğru şekilde ele alır.
        # Örneğin, 1430'dan 1460'a giden bir pencere, (1430, 20) olur.
        time_window_start_mod = round(window_start_minutes % 1440)
        time_window_end_mod = round(window_end_minutes % 1440)

        # Eğer bitiş başlangıçtan küçükse (gece yarısı geçişi), bitişe 1440 ekle
        if time_window_end_mod < time_window_start_mod:
            time_window_end_mod += 1440 # Bu, CSP'deki is_time_in_range mantığına uygun olur

        time_window = (time_window_start_mod, time_window_end_mod)
        
        is_urgent = random.random() < 0.3 # %30 olasılıkla acil

        deliveries.append(Delivery(
            id=i,
            x=x,
            y=y,
            weight=weight,
            priority=priority,
            time_window=time_window,
            is_urgent=is_urgent
        ))
    return deliveries

def generate_noflyzones(n, dynamic=False, graph_size=100):
    """
    Belirtilen sayıda statik no-fly bölgesi oluşturur.
    Dinamik bölgeler için nofly_api kullanılır.
    """
    zones = []
    for i in range(n):
        # No-fly bölgeleri için daha geniş ve rastgele konumlar
        x1 = random.randint(graph_size // 4, graph_size * 3 // 4)
        y1 = random.randint(graph_size // 4, graph_size * 3 // 4)
        x2 = x1 + random.randint(5, 20) # Daha geniş no-fly bölgeleri
        y2 = y1 + random.randint(5, 20)

        # NoFlyZone sınıfınızın varlığını ve Polygon objesi döndürdüğünü varsayıyorum
        # Eğer NoFlyZone sınıfınız yoksa veya farklı çalışıyorsa, bu kısmı düzeltmeniz gerekebilir.
        # Örneğin, doğrudan Polygon objesi oluşturabilirsiniz:
        # polygon = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
        # zones.append(polygon)

        # Eğer NoFlyZone sınıfı kullanılıyorsa ve .polygon özelliği varsa:
        zone = NoFlyZone(
            id=i,
            coordinates=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
            active_time=("00:00", "23:59") # Statik bölgeler her zaman aktif
        )
        zones.append(zone.polygon) # NoFlyZone objesinin Polygon özelliğini alıyoruz
    return zones


def load_data(scenario=1, json_path=None, current_time_dt=None, num_drones=None, num_deliveries=None, graph_size=100):
    """
    Senaryoya veya JSON dosyasına göre drone, teslimat ve no-fly bölgesi verilerini yükler.
    """
    drones = []
    deliveries = []
    nofly_zones = []

    # current_time_dt None gelirse, şimdiye ayarla.
    # Bu kontrol, generate_deliveries ve get_dynamic_nofly_zones tarafından da yapılsa da,
    # load_data'nın da bu bilgiye sahip olması tutarlılık açısından iyi.
    if current_time_dt is None: # << BU KONTROL ÇOK ÖNEMLİ
        current_time_dt = datetime.now()


    if json_path:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        drones = [Drone(**d) for d in data["drones"]]
        deliveries = [Delivery(**d) for d in data["deliveries"]]

        # JSON'dan no-fly bölgelerini Shapely Polygon objeleri olarak yükle
        for z_data in data.get("nofly_zones", []):
            coords = z_data.get("coordinates")
            if coords:
                polygon = Polygon(coords)
                nofly_zones.append(polygon)

        print(f"✅ JSON'dan yüklenen no-fly bölgesi sayısı: {len(nofly_zones)}")

    elif scenario == 1:
        # num_drones ve num_deliveries load_data'ya geçirilirse onları kullan, yoksa varsayılanı
        drones = generate_drones(num_drones if num_drones is not None else 5, graph_size=graph_size)
        deliveries = generate_deliveries(num_deliveries if num_deliveries is not None else 20, graph_size=graph_size, current_time_dt=current_time_dt)
        nofly_zones = generate_noflyzones(2, dynamic=False, graph_size=graph_size)

    elif scenario == 2:
        drones = generate_drones(num_drones if num_drones is not None else 10, graph_size=graph_size)
        deliveries = generate_deliveries(num_deliveries if num_deliveries is not None else 50, graph_size=graph_size, current_time_dt=current_time_dt)
        
        # Dinamik no-fly bölgeleri için nofly_api'yi kullan
        # nofly_api'den dönen değer zaten Shapely Polygon objeleri listesidir.
        # current_time_dt'den string'e çevirerek gönderiyoruz.
        active_zones_list, _ = get_dynamic_nofly_zones(current_time_dt.strftime("%H:%M"))
        
        # Sadece 5 bölge olmasını istiyorsanız, burada bir kesme yapabilirsiniz
        # Veya nofly_api.py'deki get_dynamic_nofly_zones'u ayarlayarak tam 5 bölge dönmesini sağlayabilirsiniz.
        # Şimdilik, nofly_api'nin döndürdüğü kadarını alıyoruz.
        nofly_zones = active_zones_list 
        
        # Eğer nofly_api'den 5'ten az bölge geliyorsa, generate_noflyzones ile tamamlayabilirsiniz.
        # Ancak bu, dinamikliği bozabilir. En iyisi nofly_api.py'deki tanımı 5 bölgeye çıkarmaktır.
        # Örneğin:
        # if len(nofly_zones) < 5:
        #     nofly_zones.extend(generate_noflyzones(5 - len(nofly_zones), dynamic=False))

    else:
        raise ValueError("Geçersiz senaryo. 1, 2 veya bir JSON dosya yolu belirtmelisin.")

    return drones, deliveries, nofly_zones