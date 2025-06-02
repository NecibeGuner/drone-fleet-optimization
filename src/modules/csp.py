from datetime import datetime
import math
import time
from shapely.geometry import LineString, Point
from modules.astar import astar # astar modülünüzü import ettiğinizden emin olun

def assign_drones_one_delivery_each(drones, deliveries, graph, positions, noflyzones, current_time=None, scenario=1):
    start_time = time.time()
    assignments = []
    assigned_deliveries = set()
    reasons = []  # Atanamayan teslimatların nedenlerini tutacağız

    # ÖNEMLİ DÜZELTME: Batarya tüketim oranını astar_main.py ile senkronize ediyoruz.
    # astar_main.py'de 0.008 olarak tanımlandığı için burada da aynı değeri kullanıyoruz.
    BATTERY_CONSUMPTION_PER_METER = 0.008 

    def nearest_node(pos):
        """
        Verilen pozisyona en yakın düğümü bulur.
        """
        x, y = pos
        return min(positions.keys(), key=lambda node: math.hypot(positions[node][0] - x, positions[node][1] - y))

    def time_str_to_minutes(tstr):
        """
        Saat stringini (HH:MM) dakikaya çevirir.
        """
        if isinstance(tstr, int):
            return tstr
        if isinstance(tstr, str) and ':' in tstr:
            try:
                h, m = int(tstr.split(':')[0]), int(tstr.split(':')[1])
                return h * 60 + m
            except ValueError:
                return 0 # Hatalı format durumunda 0 döndür
        return 0 # Diğer durumlar için 0 döndür

    def current_time_to_minutes(ct):
        """
        Mevcut zamanı (string veya datetime objesi) dakikaya çevirir.
        """
        if isinstance(ct, (int, float)):
            return ct
        elif isinstance(ct, datetime):
            return ct.hour * 60 + ct.minute + ct.second / 60
        elif isinstance(ct, str) and ':' in ct:
            return time_str_to_minutes(ct)
        return 0 # Geçersiz format için 0 döndür

    # Teslimatları önceliğe göre sırala (yüksek öncelikli olanlar önce)
    sorted_deliveries = sorted(deliveries, key=lambda d: -getattr(d, 'priority', 1))

    # Droneların batarya özelliğinin olduğundan emin ol, yoksa varsayılan değer ata
    # Not: astar_main.py'de drone.current_mah = drone.battery yapıldığı için,
    # burada drone.battery'nin doğru olduğundan emin olmak yeterlidir.
    for drone in drones:
        if not hasattr(drone, 'battery'):
            drone.battery = 10000.0 # Varsayılan batarya değeri (daha gerçekçi bir başlangıç)
        if not hasattr(drone, 'current_mah'): # current_mah'ı da başlangıç bataryasına eşitle
            drone.current_mah = drone.battery


    # Her bir teslimat için atama yapmayı dene
    print(f"CSP: Başlangıç. {len(deliveries)} teslimat ve {len(drones)} drone mevcut.")
    for delivery in sorted_deliveries:
        print(f"\nCSP: Teslimat {delivery.id} deneniyor (Konum: {delivery.x:.2f},{delivery.y:.2f}, Ağırlık: {delivery.weight:.2f}kg)...")
        
        if delivery.id in assigned_deliveries:
            print(f"CSP: Teslimat {delivery.id} zaten atanmış, geçiliyor.")
            continue

        # Teslimat noktasının no-fly bölgesi içinde olup olmadığını kontrol et
        if any(Point(delivery.x, delivery.y).within(z) for z in noflyzones):
            reasons.append((delivery.id, "Teslimat noktası no-fly bölgesinde."))
            print(f"CSP: Teslimat {delivery.id} no-fly bölgesinde. Atanamadı.")
            continue

        assigned = False
        delivery_specific_reasons = [] 

        for drone in drones:
            # Drone'un zaten atanmış olup olmadığını kontrol et (tekli teslimat ataması için)
            # Bu CSP'nin "her drone'a bir teslimat" kuralını uygular.
            if any(a['drone_id'] == drone.id for a in assignments):
                print(f"    CSP: Drone {drone.id} zaten bir teslimata atanmış, geçiliyor.")
                continue

            print(f"    CSP: Drone {drone.id} ile Teslimat {delivery.id} deneniyor (Drone Konum: {drone.start_pos[0]:.2f},{drone.start_pos[1]:.2f}, Batarya: {drone.current_mah:.2f} mAh, Max Ağırlık: {drone.max_weight:.2f}kg)...")
            
            # Ağırlık kısıtı kontrolü
            if delivery.weight > drone.max_weight:
                reason = f"Drone {drone.id}: Ağırlık sınırı aşıldı ({delivery.weight:.2f}kg > {drone.max_weight:.2f}kg)."
                delivery_specific_reasons.append(reason)
                print(f"        {reason}")
                continue

            # Drone'un başlangıç düğümünü bul
            start_node = nearest_node(drone.start_pos)

            # A* ile yol bulma
            path, _, total_distance = astar(
                graph,
                start_node,
                delivery.id, # Teslimatın ID'si hedef düğüm ID'si olarak kullanılıyor
                positions,
                drone.speed,
                noflyzones=noflyzones,
                current_time=current_time,
                scenario=scenario
            )

            # Yol bulunamadıysa veya geçersizse
            if path is None or len(path) < 2:
                reason = f"Drone {drone.id}: Yol bulunamadı (Başlangıç {start_node}, Hedef teslimat ID'si {delivery.id})."
                delivery_specific_reasons.append(reason)
                print(f"        {reason}")
                continue

            # Yolun no-fly bölgeleriyle kesişip kesişmediğini kontrol et
            line = LineString([positions[n] for n in path])
            # Bounding box kontrolü ile performansı artırıyoruz
            filtered_zones = [z for z in noflyzones if line.bounds[0] <= z.bounds[2]
                                                     and line.bounds[2] >= z.bounds[0]
                                                     and line.bounds[1] <= z.bounds[3]
                                                     and line.bounds[3] >= z.bounds[1]]
            if any(line.intersects(z) for z in filtered_zones):
                reason = f"Drone {drone.id}: Yol no-fly zone ({len(filtered_zones)} bölge) ile kesişiyor."
                delivery_specific_reasons.append(reason)
                print(f"        {reason}")
                continue

            # Batarya kısıtı kontrolü
            required_battery = total_distance * BATTERY_CONSUMPTION_PER_METER
            if drone.current_mah < required_battery:
                reason = f"Drone {drone.id}: Yetersiz batarya (Gerekli: {required_battery:.2f} mAh, Mevcut: {drone.current_mah:.2f} mAh)."
                delivery_specific_reasons.append(reason)
                print(f"        {reason}")
                continue

            # Zaman penceresi kısıtı kontrolü (eğer teslimatta zaman penceresi varsa)
            travel_time_minutes = (total_distance / drone.speed) / 60 # Saniyeyi dakikaya çevir
            arrival_time_minutes = current_time_to_minutes(current_time) + travel_time_minutes

            if hasattr(delivery, 'time_window') and delivery.time_window:
                window_start, window_end = delivery.time_window
                start_minutes = time_str_to_minutes(window_start)
                end_minutes = time_str_to_minutes(window_end)
                
                # Varış zamanının zaman penceresi içinde olup olmadığını kontrol et
                if not (start_minutes <= arrival_time_minutes <= end_minutes):
                    reason = f"Drone {drone.id}: Zaman penceresine uymuyor (Varış: {round(arrival_time_minutes,2)} dk, Pencere: {start_minutes}-{end_minutes} dk)."
                    delivery_specific_reasons.append(reason)
                    print(f"        {reason}")
                    continue

            # Tüm kısıtlar geçerliyse, atama başarılı
            drone.current_mah -= required_battery # Drone'un bataryasını güncelle
            assignments.append({
                'drone_id': drone.id,
                'delivery_id': delivery.id,
                'path': path, # Yol bilgisi burada tutuluyor
                'distance': total_distance,
                'time': round(travel_time_minutes * 60, 2), # Süreyi saniye olarak kaydet
                'battery_left': round(drone.current_mah, 2) # Kalan batarya bilgisi
            })
            assigned_deliveries.add(delivery.id) # Teslimatı atanmış olarak işaretle
            assigned = True
            print(f"    CSP: !!! Teslimat {delivery.id} -> Drone {drone.id} BAŞARIYLA atandı.")
            break # Bu teslimat atandığı için diğer droneları kontrol etmeye gerek yok

        # Eğer bu teslimat hiçbir drone tarafından atanamadıysa, nedenlerini kaydet
        if not assigned:
            final_reason_for_delivery = "; ".join(delivery_specific_reasons)
            if not final_reason_for_delivery:
                final_reason_for_delivery = "Hiçbir drone bu teslimatı atayamadı (tüm drone denemeleri başarısız veya kısıtlar tetiklenmedi)."
            reasons.append((delivery.id, final_reason_for_delivery))
            print(f"CSP: Teslimat {delivery.id} ATANAMADI. Neden: {final_reason_for_delivery}")

    duration = time.time() - start_time
    print(f"CSP: Algoritma bitti. Toplam atanan: {len(assignments)}")
    return assignments, duration, len(assignments), reasons