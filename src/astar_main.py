import os
import copy
import time
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Polygon, LineString, Point
from matplotlib.patches import Polygon as MplPoly
import matplotlib.cm as cm
from datetime import datetime
import math

# Kendi modülleriniz (These need to exist in your project structure)
from data_loader import load_data
from modules.graph_builder import GraphBuilder
from modules.astar import astar
from genetic import genetic_algorithm, nearest_node, format_dist
from modules.csp import assign_drones_one_delivery_each
from nofly_api import get_dynamic_nofly_zones, get_random_weather 

def get_next_weather_change(current_time_str):
    """
    Belirli bir saatten sonraki bir sonraki hava değişim zamanını döndürür.
    """
    now = datetime.strptime(current_time_str, "%H:%M")
    change_times = ["00:00", "06:00", "12:00", "18:00"]
    for t in change_times:
        change_dt = datetime.strptime(t, "%H:%M")
        if change_dt > now:
            return t
    return "00:00" # Eğer tüm değişimler geçmişse, bir sonraki günün 00:00'ı

def is_delivery_urgent(delivery):
    """
    Teslimatın acil olup olmadığını kontrol eder.
    """
    # Teslimat aciliyet kontrolü: priority >= 4 ise ya da mesafe 15 birimden kısa ise acil
    urgent = False
    if hasattr(delivery, 'priority') and delivery.priority is not None:
        if delivery.priority >= 4:
            urgent = True
    
    if hasattr(delivery, 'distance_to_base') and delivery.distance_to_base is not None:
        if delivery.distance_to_base <= 15:
            urgent = True

    print(f"📦 Teslimat {delivery.id}: Öncelik = {getattr(delivery, 'priority', 'N/A')}, ", end="")
    if hasattr(delivery, 'distance_to_base') and delivery.distance_to_base is not None:
        print(f"Mesafe = {delivery.distance_to_base:.2f}, ", end="")
    print(f"Acil = {'EVET' if urgent else 'HAYIR'}")
    return urgent

def main():
    parser = argparse.ArgumentParser(description="Drone Teslimat Simülasyonu")
    parser.add_argument('--scenario', type=str, default='2',
                        help='Senaryo ID\'si (1 veya 2) veya JSON dosya yolu (örn: data/veri.json)')
    args = parser.parse_args()

    current_time = time.strftime("%H:%M")
    scenario_id = None
    weather = None
    BATTERY_CONSUMPTION_RATE = 0.008

    deliveries_list = []
    deliveries_dict = {}
    polygons = [] # Shapely Polygon objeleri için boş liste

    # Veri yükleme
    if args.scenario.isdigit():
        scenario_id = int(args.scenario)
        # load_data'dan dönen nofly_zones_from_loader_orig_objects zaten Shapely Polygon objeleri listesi olmalı
        drones, deliveries_list_from_loader, nofly_zones_from_loader_orig_objects = load_data(scenario=scenario_id)
        
        deliveries_dict = {d.id: d for d in deliveries_list_from_loader}
        deliveries_list = deliveries_list_from_loader

        scenario_name = f"senaryo{scenario_id}"

        if scenario_id == 2:
            weather = get_random_weather()
            # nofly_api'den dönen active_zones_coords_list zaten Shapely Polygon objeleri listesidir
            active_zones_coords_list, _ = get_dynamic_nofly_zones(current_time, weather)
            polygons = active_zones_coords_list if active_zones_coords_list else [] # Düzeltildi, zaten Polygon objeleri
            
            next_change = get_next_weather_change(current_time)
            print(f"🕒 Saat: {current_time} | Hava: {weather.upper()} | Değişim: {next_change}")
            
            # Kötü hava koşullarına göre teslimat filtrelemesi
            if weather.lower() in ['storm', 'foggy', 'extreme', 'rainy']: # 'rainy' de eklendi
                print(f"⛈ Kötü hava ( {weather.upper()} ). Sadece acil teslimatlar işlenecek.")
                deliveries_list = [d for d in deliveries_list if is_delivery_urgent(d)]
                deliveries_dict = {d.id: d for d in deliveries_list}
                if not deliveries_list:
                    print("❌ Hava nedeniyle tüm teslimatlar iptal edildi. Program sonlandırılıyor.")
                    return
            
        else: # Senaryo 1 veya belirtilen diğer sayısal senaryolar
            # load_data'dan dönen nofly_zones_from_loader_orig_objects zaten Shapely Polygon objeleri listesidir
            polygons = nofly_zones_from_loader_orig_objects if nofly_zones_from_loader_orig_objects else [] # Düzeltildi, zaten Polygon objeleri
    else: # JSON dosya yolu belirtilmişse
        json_path = args.scenario
        # load_data'dan dönen nofly_zones_from_loader_orig_objects zaten Shapely Polygon objeleri listesidir
        drones, deliveries_list_from_loader, nofly_zones_from_loader_orig_objects = load_data(json_path=json_path)
        deliveries_dict = {d.id: d for d in deliveries_list_from_loader}
        deliveries_list = deliveries_list_from_loader
        
        polygons = nofly_zones_from_loader_orig_objects if nofly_zones_from_loader_orig_objects else [] # Düzeltildi, zaten Polygon objeleri

        scenario_name = os.path.splitext(os.path.basename(json_path))[0]
        scenario_id = "JSON_File" # Senaryo ID'si yerine dosya adını kullan
        weather = "normal" # JSON dosyaları için varsayılan hava durumu

    # Eğer hiç drone veya teslimat yoksa erken çıkış yap
    if not drones:
        print("❌ Hiç drone yüklenemedi. Program sonlandırılıyor.")
        return
    if not deliveries_list:
        print("❌ Hiç teslimat yüklenemedi (veya filtreleme sonrası kalmadı). Program sonlandırılıyor.")
        return

    # GraphBuilder, teslimat listesi ve no-fly bölgeleri ile ağı oluşturur
    G = GraphBuilder(deliveries_list, polygons).build() 
    positions = {n: (d['x'], d['y']) for n, d in G.nodes(data=True)}
    
    V = len(G.nodes)
    E = len(G.edges)

    print(f"Toplam {V} düğüm ve {E} kenar oluşturuldu.")

    # Genetik Algoritma parametreleri (bu değerleri buradan değiştirebilirsiniz)
    population_size = 50
    generations = 15
    
    # fitness_operations değeri daha doğru hesaplanmalı, örneğin her atama denemesi
    fitness_operations = len(drones) * (len(deliveries_list) // len(drones)) if len(drones) > 0 else 0

    print("2) Genetik algoritma ile teslimatlar drone'lara atanıyor...")
    start_ga = time.time()
    best_assign = genetic_algorithm(
        drones=drones,
        deliveries=deliveries_list, 
        graph=G,
        positions=positions,
        nofly_zones=polygons, # No-fly bölgeleri GA'ya gönderiliyor
        battery_consumption_rate=BATTERY_CONSUMPTION_RATE,
        current_time=0,
        population_size=population_size,
        generations=generations
    )
    end_ga = time.time()
    ga_time = end_ga - start_ga

    print("Genetik algoritma tamamlandı. En iyi atama hazır.")

    print("\n3) GA sonucu A* ve Kısıt Kontrolü ile rotalar hesaplanıyor ve atamalar yapılıyor...")
    start_astar_ga_validation = time.time() # A* validation for GA starts here
    assignments_ga_paths = []
    reasons_ga = []
    assigned_deliveries_ga = set()

    sim_drones_ga = [copy.deepcopy(d) for d in drones]
    for di, route in enumerate(best_assign):
        if di >= len(sim_drones_ga):
            continue
        drone_ga = sim_drones_ga[di]
        drone_ga.current_mah = drone_ga.battery # Her drone için başlangıç bataryasını sıfırla

        current_node_ga = nearest_node(drone_ga.start_pos, positions)

        for did in route:
            delivery_obj_ga = deliveries_dict.get(did)

            if not delivery_obj_ga:
                reasons_ga.append((did, "Teslimat objesi bulunamadı (geçersiz ID veya filtrelenmiş)"))
                continue
            if delivery_obj_ga.id in assigned_deliveries_ga:
                reasons_ga.append((did, "Zaten GA tarafından atanmış"))
                continue
            if delivery_obj_ga.weight > drone_ga.max_weight:
                reasons_ga.append((did, f"Ağırlık sınırı aşıldı ({delivery_obj_ga.weight}kg > {drone_ga.max_weight}kg)"))
                continue
            
            # Teslimat noktasının no-fly zone içinde olup olmadığını kontrol et
            if any(Point(delivery_obj_ga.x, delivery_obj_ga.y).within(p) for p in polygons):
                reasons_ga.append((did, "Teslimat noktası no-fly zone içinde"))
                continue

            # A* hesaplaması her segment için yapılır
            path_ga, astar_cost_ga, total_distance_ga = astar(G, current_node_ga, delivery_obj_ga.id, positions, drone_ga.speed, noflyzones=polygons, current_time=current_time, scenario=scenario_id)

            if not path_ga:
                reasons_ga.append((did, "Yol bulunamadı (no-fly zone veya bağlantısızlık olabilir)"))
                continue
            
            # Düzeltme: LineString oluşturmadan önce yolun yeterli sayıda düğüm içerdiğini kontrol et
            if len(path_ga) < 2:
                reasons_ga.append((did, "Yol çok kısa (başlangıç ve bitiş noktası aynı olabilir veya geçersiz)"))
                continue

            # Oluşan yolun no-fly zone ile kesişip kesişmediğini kontrol et
            path_line_ga = LineString([positions[n] for n in path_ga])
            if any(path_line_ga.intersects(p) for p in polygons):
                reasons_ga.append((did, "No-fly zone ihlali tespit edildi (GA yolu)"))
                continue

            needed_battery_mah_ga = total_distance_ga * BATTERY_CONSUMPTION_RATE
            if drone_ga.current_mah < needed_battery_mah_ga:
                reasons_ga.append((did, f"Batarya yetersiz (Kalan: {drone_ga.current_mah:.1f} mAh, Gerekli: {needed_battery_mah_ga:.1f} mAh)"))
                continue

            drone_ga.current_mah -= needed_battery_mah_ga
            time_taken_seconds_ga = round(total_distance_ga / drone_ga.speed, 2)

            assignments_ga_paths.append({
                'drone_id': drone_ga.id,
                'delivery_id': delivery_obj_ga.id,
                'path': path_ga, # astar already returns full path
                'distance': total_distance_ga,
                'time': time_taken_seconds_ga,
                'battery_left': drone_ga.current_mah,
                'algo': 'GA' 
            })
            assigned_deliveries_ga.add(delivery_obj_ga.id)
            current_node_ga = delivery_obj_ga.id # Bir sonraki teslimat için başlangıç noktası

    end_astar_ga_validation = time.time()
    astar_time_ga = end_astar_ga_validation - start_astar_ga_validation
    print(f"\nToplam {len(assignments_ga_paths)} GA-A* ataması başarıyla yapıldı.")

    print("\n4) CSP algoritması ile tekli teslimat atamaları yapılıyor...")
    start_csp_solving = time.time() # CSP solving time

    # Initialize variables for CSP (ensure these are initialized before use)
    csp_full_assignments = []
    assigned_deliveries_csp = set()
    reasons_csp = []

    csp_assignments_raw, csp_solving_time, _, _ = assign_drones_one_delivery_each(
        drones=copy.deepcopy(drones),
        deliveries=deliveries_list, # Corrected: Use deliveries_list
        graph=G,
        positions=positions,
        noflyzones=polygons, # Corrected: Use polygons (which is your polygons list)
        current_time = 0,
        scenario=scenario_id
    )
    end_csp_solving = time.time()
    csp_solving_time = end_csp_solving - start_csp_solving # This is the actual solving time, not total time

    start_astar_csp_validation = time.time() # A* validation for CSP starts here
    csp_drones = [copy.deepcopy(d) for d in drones]
    for a in csp_assignments_raw:
        drone = next((d for d in csp_drones if d.id == a['drone_id']), None)
        delivery = next((d for d in deliveries_list if d.id == a['delivery_id']), None) # Corrected: Use deliveries_list
        
        if not drone or not delivery:
            reasons_csp.append((a['delivery_id'], "Teslimat veya drone objesi bulunamadı"))
            continue
        if delivery.weight > drone.max_weight:
            reasons_csp.append((delivery.id, f"Ağırlık sınırı aşıldı ({delivery.weight}kg > {drone.max_weight}kg)"))
            continue
        if any(Point(delivery.x, delivery.y).within(p) for p in polygons):
            reasons_csp.append((delivery.id, "Teslimat noktası no-fly zone içinde"))
            continue

        start_node = nearest_node(drone.start_pos, positions)
        path, _, dist = astar(G, start_node, delivery.id, positions, drone.speed, noflyzones=polygons, current_time=current_time, scenario=scenario_id)
        
        if not path:
            reasons_csp.append((delivery.id, "Yol bulunamadı (no-fly zone veya bağlantısızlık olabilir)"))
            continue
        
        # Düzeltme: LineString oluşturmadan önce yolun yeterli sayıda düğüm içerdiğini kontrol et
        if len(path) < 2: # Path must have at least two nodes (start and end)
            reasons_csp.append((delivery.id, "Geçersiz yol uzunluğu (başlangıç ve bitiş noktası aynı olabilir)"))
            continue

        if any(LineString([positions[n] for n in path]).intersects(p) for p in polygons):
            reasons_csp.append((delivery.id, "No-fly zone ihlali tespit edildi (CSP yolu)"))
            continue

        needed_battery = dist * BATTERY_CONSUMPTION_RATE # Corrected: Use BATTERY_CONSUMPTION_RATE
        if drone.current_mah < needed_battery: # Use current_mah for consistency
            reasons_csp.append((delivery.id, f"Batarya yetersiz (Kalan: {drone.current_mah:.1f} mAh, Gerekli: {needed_battery:.1f} mAh)"))
            continue
        
        drone.current_mah -= needed_battery # Update drone's battery
        t = round(dist / drone.speed, 2)
        
        csp_full_assignments.append({
            'drone_id': drone.id,
            'delivery_id': delivery.id,
            'path': path, # astar already returns full path
            'distance': dist,
            'time': t,
            'battery_left': drone.current_mah, # Use current_mah for consistency
            'algo': 'CSP'
        })
        assigned_deliveries_csp.add(delivery.id)

    end_astar_csp_validation = time.time()
    astar_time_csp_validation = end_astar_csp_validation - start_astar_csp_validation
    csp_time_total = csp_solving_time + astar_time_csp_validation # CSP toplam süresi (çözüm + A* validasyon)

    print(f"\nToplam {len(csp_full_assignments)} CSP-A* ataması başarıyla yapıldı.")

    # Performans Metrikleri Hesaplamaları
    total_deliveries_count = len(deliveries_list)
    
    successful_deliveries_ga = len(assignments_ga_paths)
    total_energy_ga = sum(a['distance'] * BATTERY_CONSUMPTION_RATE for a in assignments_ga_paths)
    average_energy_ga = total_energy_ga / successful_deliveries_ga if successful_deliveries_ga > 0 else 0
    
    successful_deliveries_csp = len(csp_full_assignments)
    total_energy_csp = sum(a['distance'] * BATTERY_CONSUMPTION_RATE for a in csp_full_assignments)
    average_energy_csp = total_energy_csp / successful_deliveries_csp if successful_deliveries_csp > 0 else 0

    # Kombine başarılı teslimatlar (Hem GA hem de CSP'nin atadıklarının birleşimi)
    successful_deliveries_combined = len(assigned_deliveries_ga.union(assigned_deliveries_csp))
    success_rate_combined = (successful_deliveries_combined / total_deliveries_count) * 100 if total_deliveries_count > 0 else 0
    
    # Kombine ortalama ve toplam enerji
    # Aynı teslimatın iki kez enerjisini saymamak için birleştirilmiş bir liste oluştur
    all_assigned_energies = [a['distance'] * BATTERY_CONSUMPTION_RATE for a in assignments_ga_paths]
    for a_csp in csp_full_assignments:
        if a_csp['delivery_id'] not in assigned_deliveries_ga: # GA tarafından atanmadıysa CSP'ninkini ekle
            all_assigned_energies.append(a_csp['distance'] * BATTERY_CONSUMPTION_RATE)

    total_energy_combined = sum(all_assigned_energies)
    average_energy_combined = total_energy_combined / successful_deliveries_combined if successful_deliveries_combined > 0 else 0

    total_runtime = ga_time + astar_time_ga + csp_time_total

    # Zaman karmaşıklığı hesaplamaları için
    ga_ops_count = population_size * generations * fitness_operations
    astar_ops_count_ga = successful_deliveries_ga * (E + V * math.log(V)) if V > 0 else 0 
    astar_ops_count_csp = successful_deliveries_csp * (E + V * math.log(V)) if V > 0 else 0 
    csp_ops_count = len(csp_assignments_raw) # CSP'nin bulduğu başlangıç atama sayısı (veya çözüm arayışındaki operasyonlar)

    # Gerçekten atanamayan teslimatları belirle (hem GA hem de CSP tarafından atanmayanlar)
    all_assigned_ids_union = assigned_deliveries_ga.union(assigned_deliveries_csp)
    truly_unassigned_deliveries = [d for d in deliveries_list if d.id not in all_assigned_ids_union]

    # Atanamayan teslimatlar için sadeleştirilmiş nedenleri topla
    truly_unassigned_reasons_simplified = {}
    for delivery in truly_unassigned_deliveries:
        reason_text = "Uygun drone bulunamadı veya rota imkansız" # Varsayılan genel neden
        
        # GA nedenlerine bak (eğer GA'da belirli bir neden varsa onu kullan)
        ga_reason_tuple = next(((r_did, r_reason) for r_did, r_reason in reasons_ga if r_did == delivery.id), None)
        if ga_reason_tuple:
            if "Ağırlık sınırı aşıldı" in ga_reason_tuple[1]:
                reason_text = "Ağırlık sınırı aşıldı"
            elif "Batarya yetersiz" in ga_reason_tuple[1]:
                reason_text = "Batarya yetersiz"
            elif "Yol bulunamadı" in ga_reason_tuple[1] or "no-fly zone ihlali" in ga_reason_tuple[1]:
                reason_text = "Yol bulunamadı (no-fly zone veya bağlantısızlık)"
            elif "no-fly zone içinde" in ga_reason_tuple[1]:
                    reason_text = "Teslimat noktası no-fly zone içinde"
        
        # CSP nedenlerine bak (eğer CSP'de daha spesifik bir neden varsa onu kullan)
        csp_reason_tuple = next(((r_did, r_reason) for r_did, r_reason in reasons_csp if r_did == delivery.id), None)
        if csp_reason_tuple:
            if "Ağırlık sınırı aşıldı" in csp_reason_tuple[1]:
                reason_text = "Ağırlık sınırı aşıldı"
            elif "Batarya yetersiz" in csp_reason_tuple[1]:
                reason_text = "Batarya yetersiz"
            elif "Yol bulunamadı" in csp_reason_tuple[1] or "no-fly zone ihlali" in csp_reason_tuple[1]:
                reason_text = "Yol bulunamadı (no-fly zone veya bağlantısızlık)"
            elif "no-fly zone içinde" in csp_reason_tuple[1]:
                    reason_text = "Teslimat noktası no-fly zone içinde"

        truly_unassigned_reasons_simplified[delivery.id] = reason_text


    # 5) Tek bir rapor dosyasına kaydet
    current_datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    rapor_yolu = os.path.join(os.path.dirname(__file__), f'performance_log{scenario_name}_{current_datetime_str}.txt')
    with open(rapor_yolu, 'w', encoding='utf-8') as log:
        log.write(f"📘 SENARYO: {scenario_name}\n")
        log.write(f"🕒 Saat: {current_time} | Hava Durumu: {weather.upper() if weather else 'N/A'}\n")
        log.write(f"🚁 Drone Sayısı: {len(drones)} | 📦 Teslimat Sayısı: {total_deliveries_count} | ⛔ No-Fly Bölge: {len(polygons)}\n\n")

        log.write(f"✅ Başarılı Teslimatlar: {successful_deliveries_combined} / {total_deliveries_count} (%{success_rate_combined:.2f})\n")
        log.write(f"🔋 Ortalama Enerji Tüketimi: {average_energy_combined:.2f} mAh | Toplam Enerji: {total_energy_combined:.2f} mAh\n\n")

        log.write(f"⏱ Süreler (saniye):\n")
        log.write(f"  - Genetik Algoritma (GA): {ga_time:.2f} s\n")
        log.write(f"  - A* Arama Algoritması (GA Yolu): {astar_time_ga:.2f} s\n") # GA rotaları için A* süresi
        log.write(f"  - CSP Çözümü ve A* Doğrulaması (CSP Yolu): {csp_time_total:.4f} s\n") # CSP toplam süresi (çözüm + A* validasyon)
        log.write(f"  - 🔁 Toplam İşlem Süreci: {total_runtime:.2f} s\n\n")

        log.write(f"📊 Zaman Dağılımı:\n")
        log.write(f"  - GA Zaman Payı: %{(ga_time/total_runtime)*100:.2f}\n" if total_runtime > 0 else "  - GA Zaman Payı: %0.00\n")
        log.write(f"  - A* (GA) Zaman Payı: %{(astar_time_ga/total_runtime)*100:.2f}\n" if total_runtime > 0 else "  - A (GA) Zaman Payı: %0.00\n")
        log.write(f"  - CSP Zaman Payı: %{(csp_time_total/total_runtime)*100:.4f}\n" if total_runtime > 0 else "  - CSP Zaman Payı: %0.0000\n")
        log.write("\n")
        
        log.write(f"🧠 Teorik Zaman Karmaşıklıkları:\n")
        log.write(f"  - Genetik Algoritma: O(P × G × N)\n")
        log.write(f"  - A*: O(E + V log V)\n")
        log.write(f"  - CSP: O(Değişken Sayısı * Değer Alanı ^ (Değişken Sayısı/2)) - Genellikle NP-complete\n\n") # CSP için daha genel karmaşıklık ifadesi
        log.write(f"  - *Not: P=Popülasyon Boyutu, G=Nesil Sayısı, N=Teslimat Sayısı (GA için), E=Kenar Sayısı, V=Düğüm Sayısı (A için)\n\n")


        log.write(f"📈 Sayısal Zaman Karmaşıklıkları:\n")
        log.write(f"  - GA: {ga_ops_count} işlem\n")
        log.write(f"  - A*: {astar_ops_count_ga + astar_ops_count_csp} işlem (GA ve CSP rotaları için toplam)\n") # A* işlem sayısı toplamı
        log.write(f"  - CSP: {csp_ops_count} işlem (İlk atama denemesi)\n\n")

        log.write(f"--- DETAYLI TESLİMAT ATAMALARI ---\n")
        # GA ve CSP'den gelen tüm atamaları birleştirip sıralı listele
        all_assignments_for_report = sorted(
            assignments_ga_paths + csp_full_assignments,
            key=lambda x: (x['drone_id'], x['delivery_id'], x['algo'])
        )
        if all_assignments_for_report:
            for a in all_assignments_for_report:
                log.write(
                    f"🔧 Drone {a['drone_id']} -> Teslimat {a['delivery_id']} ({a['algo']}): "
                    f"Mesafe = {format_dist(a['distance'])}, "
                    f"Süre = {a['time']} s, Kalan Batarya = {a['battery_left']:.2f}\n"
                )
        else:
            log.write("Hiçbir teslimat başarıyla atanamadı.\n")

        log.write(f"\n--- ATANAMAYAN TESLİMATLAR ---\n")
        if truly_unassigned_deliveries:
            for delivery in sorted(truly_unassigned_deliveries, key=lambda x: x.id): # Sıralı çıktı için
                log.write(f"⚠ Teslimat {delivery.id} atanamadı: {truly_unassigned_reasons_simplified.get(delivery.id, 'Neden belirtilmemiş')}\n")
        else:
            log.write("Tüm teslimatlar başarıyla atandı.\n")
        
    print(f"🔍 Tüm rapor '{rapor_yolu}' dosyasına kaydedildi.")

    print("\n6) Teslimat rotaları görselleştiriliyor (GA Mavi, CSP Kesikli Turuncu)...")
    fig, ax = plt.subplots(figsize=(12, 12))

    # No-Fly Zone'ları çiz
    for poly_shapely in polygons:
        patch = MplPoly(list(poly_shapely.exterior.coords), color='red', alpha=0.2, label='No-Fly Zone')
        ax.add_patch(patch)

    # Ağ kenarlarını çiz (genel harita görünümü)
    edge_w = [d['weight'] for _, _, d in G.edges(data=True)]
    max_w = max(edge_w) if edge_w else 1
    widths = [(w / max_w) * 1.5 for w in edge_w]
    nx.draw_networkx_edges(G, positions, width=widths, alpha=0.3, ax=ax, edge_color='gray')
    nx.draw_networkx_nodes(G, positions, node_size=30, node_color='lightblue', ax=ax)

    # Renk Haritaları
    cmap_ga = cm.get_cmap('Blues')
    cmap_csp = cm.get_cmap('Oranges')

    # GA Rotalarını Çiz
    # Sadece ilk GA rotası için lejant ekle
    ga_legend_added = False
    for idx, a in enumerate(assignments_ga_paths):
        if not a['path'] or len(a['path']) < 2:
            continue
        pe = list(zip(a['path'][:-1], a['path'][1:]))
        # Her rotaya farklı bir ton vererek ayrımı kolaylaştır
        color = cmap_ga(0.3 + (idx % (len(assignments_ga_paths) if len(assignments_ga_paths) > 0 else 1)) * 0.7 / (len(assignments_ga_paths) if len(assignments_ga_paths) > 0 else 1))
        nx.draw_networkx_edges(G, positions, edgelist=pe, width=3, edge_color=[color], ax=ax, alpha=0.8)
        # Sadece bu rotaya ait düğümleri çiz (opsiyonel, genel düğümler zaten çizili)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'], node_size=80, node_color=[color], ax=ax, alpha=0.8)
        if not ga_legend_added:
            ax.plot([], [], color=cmap_ga(0.5), label=f"GA Rotaları")
            ga_legend_added = True
        
    # CSP Rotalarını Çiz (Eğer varsa)
    # Sadece ilk CSP rotası için lejant ekle
    csp_legend_added = False
    for idx, a in enumerate(csp_full_assignments):
        if not a['path'] or len(a['path']) < 2:
            continue
        pe = list(zip(a['path'][:-1], a['path'][1:]))
        # Her rotaya farklı bir ton vererek ayrımı kolaylaştır
        color = cmap_csp(0.3 + (idx % (len(csp_full_assignments) if len(csp_full_assignments) > 0 else 1)) * 0.7 / (len(csp_full_assignments) if len(csp_full_assignments) > 0 else 1))
        nx.draw_networkx_edges(G, positions, edgelist=pe, width=2, edge_color=[color], style='dashed', ax=ax, alpha=0.7)
        # Sadece bu rotaya ait düğümleri çiz (opsiyonel)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'], node_size=40, node_color=[color], ax=ax, alpha=0.6)
        if not csp_legend_added:
            ax.plot([], [], linestyle='dashed', color=cmap_csp(0.5), label=f"CSP Rotaları")
            csp_legend_added = True

    # Drone başlangıç noktaları
    xs = [d.start_pos[0] for d in drones]
    ys = [d.start_pos[1] for d in drones]
    ax.scatter(xs, ys, c='green', s=150, marker='s', label='Drone Başlangıç Noktası', zorder=5, edgecolor='black', linewidth=0.5)

    # Teslimat noktaları
    del_xs = [d.x for d in deliveries_list]
    del_ys = [d.y for d in deliveries_list]
    ax.scatter(del_xs, del_ys, c='purple', s=100, marker='o', label='Teslimat Noktaları', zorder=4, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Düğüm etiketleri
    nx.draw_networkx_labels(G, positions, font_size=7, ax=ax, font_color='black')
    
    # Lejant ve başlık
    ax.legend(loc='upper left', fontsize='medium', bbox_to_anchor=(1.0, 1.0))
    ax.set_title(f'Drone Teslimat Rotaları ({scenario_name}) - GA ve CSP Karşılaştırması', fontsize=14, pad=20)
    ax.axis('off') # Eksenleri kapat
    plt.tight_layout(rect=[0, 0, 0.88, 1]) # Lejant için boşluk bırak

    out_img = os.path.join(os.path.dirname(__file__), f'assignment_graph{scenario_name}_{current_datetime_str}.png')
    plt.savefig(out_img, dpi=300)
    print(f"📸 Görsel '{out_img}' kaydedildi.")

if __name__ == "__main__":
    main()
