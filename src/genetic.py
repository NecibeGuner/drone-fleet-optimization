import os
import random
import copy
import math
import time
import matplotlib.pyplot as plt
from modules.astar import astar
from shapely.geometry import LineString
from datetime import datetime, timedelta # timedelta eklendi

def create_individual(num_drones, deliveries, drones=None):
    individual = [[] for _ in range(num_drones)]
    if drones:
        # Deliveries'i rastgele sırala ki aynı drone'a sürekli en yakın atama olmasın
        shuffled_deliveries = list(deliveries)
        random.shuffle(shuffled_deliveries)

        # En yakın drone'a atama yaparken, drone'ları da rastgele sırayla gezebiliriz
        drone_indices = list(range(num_drones))
        random.shuffle(drone_indices)

        for delivery in shuffled_deliveries:
            # En uygun drone'u bul (şimdilik sadece başlangıç konumuna göre)
            # Daha sofistike bir yaklaşım için drone'un kapasitesi, bataryası vb. de burada hesaba katılmalı
            closest_drone_idx = min(
                drone_indices,
                key=lambda i: math.hypot(
                    drones[i].start_pos[0] - delivery.x,
                    drones[i].start_pos[1] - delivery.y
                )
            )
            individual[closest_drone_idx].append(delivery.id)
    else:
        delivery_ids = [d.id for d in deliveries]
        random.shuffle(delivery_ids)
        for i, did in enumerate(delivery_ids):
            individual[i % num_drones].append(did)
    return individual

def nearest_node(pos, positions):
    x, y = pos
    return min(positions.keys(), key=lambda n: math.hypot(positions[n][0] - x, positions[n][1] - y))

def violates_nofly_zone(path, positions, nofly_zones):
    if len(path) < 2:
        return False # Tek nokta veya boş yol, ihlal yok
    try:
        # LineString için sadece düğümlerin pozisyonları gerekir
        line_coords = [positions[node_id] for node_id in path]
        line = LineString(line_coords)
        
        # Bounding box kontrolü ile performansı artır
        line_bbox = line.bounds # (minx, miny, maxx, maxy)
        
        for zone in nofly_zones:
            zone_bbox = zone.bounds
            # Bounding box'lar kesişiyorsa daha detaylı kontrol yap
            if not (line_bbox[2] < zone_bbox[0] or line_bbox[0] > zone_bbox[2] or
                    line_bbox[3] < zone_bbox[1] or line_bbox[1] > zone_bbox[3]):
                if line.intersects(zone):
                    return True
        return False
    except Exception as e:
        # Loglama veya hata işleme eklenebilir
        # print(f"Hata violates_nofly_zone'da: {e}")
        return True # Hata durumunda ihlal olarak kabul et

def violates_time_window(current_minutes, delivery_obj):
    # current_minutes artık int dakika cinsinden bir değer
    # delivery_obj.time_window varsayılan olarak [0, 1440] veya [başlangıç_dk, bitiş_dk] olmalı

    if not hasattr(delivery_obj, 'time_window') or not delivery_obj.time_window:
        return False # Zaman penceresi yoksa ihlal yok

    earliest_minutes, latest_minutes = delivery_obj.time_window
    
    # current_minutes (o anki varış süresi) pencere içinde mi?
    return not (earliest_minutes <= current_minutes <= latest_minutes)


def fitness(individual, drones, graph, positions,
            battery_consumption_rate, deliveries, nofly_zones, current_simulation_start_minutes):
    
    drones_copy = [copy.deepcopy(d) for d in drones]
    deliveries_dict = {d.id: d for d in deliveries}

    total_successful_deliveries = 0
    total_energy_consumed = 0.0
    total_violation_penalty = 0

    # Her drone için
    for di, route in enumerate(individual):
        drone = drones_copy[di]
        # Her drone başlangıçta tam bataryaya sahip olmalı
        drone.current_mah = drone.battery
        
        # Drone'un başlangıç düğümü
        current_node = nearest_node(drone.start_pos, positions)
        
        # Drone'un şu anki simülasyon zamanı (dakika cinsinden)
        # Bu, genetic_algorithm'dan gelen genel başlangıç zamanıdır
        drone_current_time_minutes = current_simulation_start_minutes

        for did in route:
            delivery = deliveries_dict.get(did)
            if not delivery:
                total_violation_penalty += 250 # Geçersiz teslimat ID'si
                continue

            # 1. Ağırlık Kontrolü
            if delivery.weight > drone.max_weight:
                total_violation_penalty += 150 # Ağırlık ihlali
                continue

            # A* ile yol bulma (noflyzones ve current_time artık doğru şekilde iletilir)
            path, _, dist = astar(graph, current_node, did, positions, drone.speed, noflyzones=nofly_zones, current_time=drone_current_time_minutes)
            
            # 2. Yol Bulunamadı Kontrolü
            if not path:
                total_violation_penalty += 300 # Yol bulunamadı, çok ciddi ihlal
                continue

            # 3. No-Fly Zone İhlali Kontrolü (yol üzerinden)
            # A* aslında no-fly zone'ları dikkate almalı, ama GA'da da kontrol etmek iyi olur
            if violates_nofly_zone(path, positions, nofly_zones):
                total_violation_penalty += 200 # No-fly zone ihlali
                continue
            
            # 4. Batarya Kontrolü
            needed_energy = dist * battery_consumption_rate
            if drone.current_mah < needed_energy:
                total_violation_penalty += 100 # Batarya yetersiz
                continue
            
            # Drone bataryasını düşür
            drone.current_mah -= needed_energy

            # Teslimat süresini hesapla (saniye cinsinden)
            time_to_delivery_seconds = dist / drone.speed
            time_to_delivery_minutes = time_to_delivery_seconds / 60.0

            # Drone'un teslimata varış zamanı
            arrival_time_at_delivery_minutes = drone_current_time_minutes + time_to_delivery_minutes
            
            # 5. Zaman Penceresi Kontrolü
            if violates_time_window(arrival_time_at_delivery_minutes, delivery):
                # Zaman penceresi ihlalinde verilen ceza
                total_violation_penalty += 50 
                # continue # Zaman penceresi ihlalinde bile teslimat tamamlanmış sayılabilir
                            # ancak cezalandırılır. Eğer tamamlanmaması gerekiyorsa 'continue' eklenebilir.
            
            # Teslimat başarılı sayılır
            total_successful_deliveries += 1
            total_energy_consumed += needed_energy
            
            # Drone'un mevcut zamanını güncelle
            drone_current_time_minutes = arrival_time_at_delivery_minutes
            
            # Bir sonraki teslimat için başlangıç noktasını güncelle
            current_node = did 

    # Fitness skoru: Ne kadar çok teslimat yapıldıysa o kadar iyi,
    # ne kadar çok enerji harcandıysa ve ihlal varsa o kadar kötü.
    score = (100 * total_successful_deliveries) - (0.05 * total_energy_consumed) - total_violation_penalty
    return score

def crossover(p1, p2):
    c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
    
    # Kross-over noktası seçimi (route bazında)
    num_drones = len(p1)
    if num_drones > 1:
        crossover_point_drone_idx = random.randrange(num_drones)
        # Bu drone'un rotasını değiştir
        c1[crossover_point_drone_idx], c2[crossover_point_drone_idx] = \
            c2[crossover_point_drone_idx], c1[crossover_point_drone_idx]

    # Teslimatları tüm drone'lar arasında rastgele karıştır
    all_deliveries_p1 = [did for route in c1 for did in route]
    all_deliveries_p2 = [did for route in c2 for did in route]
    
    # Duplikatları kaldır ve eksik olanları ekle
    # Bu, tüm teslimatların tekilleştirilmesini ve ardından yeniden dağıtılmasını sağlar.
    def reallocate_deliveries(individual, all_delivery_ids):
        seen_deliveries = set()
        unique_deliveries = []
        for did in all_delivery_ids:
            if did not in seen_deliveries:
                unique_deliveries.append(did)
                seen_deliveries.add(did)
        
        # Eğer bir teslimat eksikse (p1 veya p2'den gelmemişse), onu ekle.
        # Bu kısım genellikle tüm teslimatların başlangıçta bireye dağıtılmış olduğu varsayıldığında gereksizdir.
        # Ancak sağlamlık için eklenebilir.
        # Örneğin, crossover sonrası toplam teslimat sayısı orijinalden azsa
        # eksik olanları bulup eklemek gerekebilir.
        # Basit bir yol: tüm teslimatları bir listeye topla, unique yap, sonra yeniden dağıt.
        
        new_individual = [[] for _ in range(len(individual))]
        random.shuffle(unique_deliveries) # Teslimatları rastgele dağıtmak için karıştır
        for i, did in enumerate(unique_deliveries):
            new_individual[i % len(new_individual)].append(did)
        return new_individual

    return reallocate_deliveries(c1, all_deliveries_p1), reallocate_deliveries(c2, all_deliveries_p2)


def mutate(ind, rate=0.1):
    # Route içi mutasyon (teslimatların sırasını değiştir)
    for route_idx in range(len(ind)):
        if random.random() < rate and len(ind[route_idx]) > 1:
            i, j = random.sample(range(len(ind[route_idx])), 2)
            ind[route_idx][i], ind[route_idx][j] = ind[route_idx][j], ind[route_idx][i]

    # Drone'lar arası mutasyon (teslimatı bir drone'dan diğerine taşı)
    if len(ind) > 1 and len(ind[0]) > 0 and random.random() < rate:
        from_drone_idx = random.randrange(len(ind))
        if len(ind[from_drone_idx]) > 0:
            delivery_to_move_idx = random.randrange(len(ind[from_drone_idx]))
            delivery_id = ind[from_drone_idx].pop(delivery_to_move_idx)
            
            to_drone_idx = random.randrange(len(ind))
            # Hedef drone aynı olmasın diye kontrol edebiliriz
            while to_drone_idx == from_drone_idx and len(ind) > 1:
                to_drone_idx = random.randrange(len(ind))
            
            ind[to_drone_idx].append(delivery_id)


def plot_fitness_evolution(best_list, scenario_name, current_datetime_str):
    plt.figure(figsize=(10, 5))
    plt.plot(best_list, marker='o', linestyle='-')
    plt.title(f"Genetik Algoritma Fitness Evrimi ({scenario_name})")
    plt.xlabel("Jenerasyon")
    plt.ylabel("Fitness Skoru")
    plt.grid(True)
    plt.tight_layout()
    
    # Grafiği kaydet
    plot_path = os.path.join(os.path.dirname(__file__), f'fitness_evolution_{scenario_name}_{current_datetime_str}.png')
    plt.savefig(plot_path, dpi=300)
    plt.close() # Belleği serbest bırak
    print(f"📈 Fitness grafiği '{plot_path}' dosyasına kaydedildi.")


def format_dist(distance):
    return f"{distance:.2f} m"

def genetic_algorithm(drones, deliveries, graph, positions,
                      nofly_zones, battery_consumption_rate,
                      current_time, # !!! BURAYA EKLENDİ !!!
                      population_size=500, generations=30,
                      patience=5): 
    start_time = time.time()
    MAX_ALGO_TIME = 60 # Genetik algoritmanın çalışabileceği maksimum süre (saniye)

    # current_time (başlangıç simülasyon zamanı) fitness fonksiyonuna iletiliyor
    pop = [create_individual(len(drones), deliveries, drones=drones) for _ in range(population_size)]
    best_history = []

    best_fitness_overall = -float('inf') # Genel en iyi fitness
    best_individual_overall = None
    
    stagnant_generations = 0

    for gen in range(generations):
        if time.time() - start_time > MAX_ALGO_TIME:
            print("⏱️ Genetik Algoritma: Süre sınırı aşıldı, erken durduruldu.")
            break

        # Fitness hesaplaması, current_time'ı şimdi doğru bir şekilde alıyor
        scores = [
            fitness(ind, drones, graph, positions,
                    battery_consumption_rate,
                    deliveries, nofly_zones, current_time) # current_time buraya iletildi
            for ind in pop
        ]
        
        current_best_fitness_in_gen = max(scores)
        current_best_individual_in_gen = pop[scores.index(current_best_fitness_in_gen)]
        
        best_history.append(current_best_fitness_in_gen)
        print(f"Gen {gen + 1}: En iyi fitness = {current_best_fitness_in_gen:.2f}")

        # İlerleme kontrolü
        if current_best_fitness_in_gen > best_fitness_overall:
            best_fitness_overall = current_best_fitness_in_gen
            best_individual_overall = copy.deepcopy(current_best_individual_in_gen)
            stagnant_generations = 0 # İlerleme kaydedildi, sayacı sıfırla
        else:
            stagnant_generations += 1
            print(f"⚠️ İlerleme yok: {stagnant_generations} jenerasyon sabit.")

        if stagnant_generations >= patience:
            print(f"🛑 {patience} jenerasyon boyunca gelişme yok, erken durduruluyor.")
            break

        # Selection (turnuva seçimi veya rulet tekerleği gibi daha gelişmiş yöntemler kullanılabilir)
        # Basit: En iyi yarıyı seç
        ranked_pop = [ind for _, ind in sorted(zip(scores, pop), key=lambda x: x[0], reverse=True)]
        
        # Elitist seçilim: En iyi bireyi doğrudan bir sonraki nesile aktar
        elite = ranked_pop[0] 
        selected = ranked_pop[:population_size // 2] # En iyi yarısı

        next_pop = []
        # Eliti doğrudan ekle
        next_pop.append(elite) 

        # Çiftler halinde çaprazlama ve mutasyon ile yeni popülasyon oluştur
        while len(next_pop) < population_size:
            p1, p2 = random.sample(selected, 2) # Seçilenler arasından rastgele 2 ebeveyn
            c1, c2 = crossover(p1, p2)
            mutate(c1)
            mutate(c2)
            next_pop.extend([c1, c2])
        
        # Popülasyonu population_size'a sığdır
        pop = next_pop[:population_size]

    # Son olarak, tüm geçmişteki en iyi bireyi döndür
    # Eğer hiç ilerleme olmadıysa best_individual_overall hala None olabilir, bu durumda pop'un en iyisini döndür
    if best_individual_overall is None:
         # Bir kez daha fitness hesapla (zaten hesaplandı ama emin olmak için)
        final_scores = [
            fitness(ind, drones, graph, positions,
                    battery_consumption_rate,
                    deliveries, nofly_zones, current_time)
            for ind in pop
        ]
        best_idx = final_scores.index(max(final_scores))
        best_individual_overall = pop[best_idx]


    # Fitness evrimini görselleştir (burası main fonksiyondan çağrılmalı)
    # plot_fitness_evolution(best_history) 
    
    return best_individual_overall, best_history
