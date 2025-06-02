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

from data_loader import load_data
from modules.graph_builder import GraphBuilder
from modules.astar import astar
from genetic import genetic_algorithm, nearest_node, format_dist
from modules.csp import assign_drones_one_delivery_each
from nofly_api import get_dynamic_nofly_zones, get_random_weather

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', type=str, default='2', help="Senaryo numarası (1, 2) veya JSON dosya yolu (örnek: data/veri.json)")
    args = parser.parse_args()

    if args.scenario.isdigit():
        scenario_id = int(args.scenario)
        drones, deliveries, nofly_zones = load_data(scenario=scenario_id)
        scenario_name = f"senaryo{scenario_id}"
        if scenario_id == 2:
            current_time = time.strftime("%H:%M")
            weather = get_random_weather()
            nofly_zones = get_dynamic_nofly_zones(current_time, weather)
    else:
        json_path = args.scenario
        drones, deliveries, nofly_zones = load_data(json_path=json_path)
        scenario_name = os.path.splitext(os.path.basename(json_path))[0]
        scenario_id = None

    G = GraphBuilder(deliveries, nofly_zones).build()
    positions = {n: (d['x'], d['y']) for n, d in G.nodes(data=True)}

    t0 = time.time()
    best_assign = genetic_algorithm(
        drones=drones,
        deliveries=deliveries,
        graph=G,
        positions=positions,
        nofly_zones=nofly_zones,
        battery_consumption_rate=0.008,
        population_size=1500,
        generations=50
    )
    ga_time = time.time() - t0
    ga_ops = 1500 * 50
    print("Yüklenen no-fly zone sayısı:", len(nofly_zones))

    assignments = []
    sim_drones = [copy.deepcopy(d) for d in drones]
    t1 = time.time()
    for di, route in enumerate(best_assign):
        drone = sim_drones[di]
        current = nearest_node(drone.start_pos, positions)
        for did in route:
            delivery = next((d for d in deliveries if d.id == did), None)
            if not delivery or delivery.weight > drone.max_weight:
                continue
            if any(Point(delivery.x, delivery.y).within(p) for p in nofly_zones):
                continue
            path, _, dist = astar(G, current, did, positions, drone.speed, noflyzones=nofly_zones)
            if not path or len(path) < 2:
                continue
            if any(LineString([positions[n] for n in path]).intersects(p) for p in nofly_zones):
                continue
            needed = dist * 0.1
            if drone.battery < needed:
                continue
            drone.battery -= needed
            t = round(dist / drone.speed, 2)
            assignments.append({
                'drone_id': drone.id,
                'delivery_id': delivery.id,
                'path': path,
                'distance': dist,
                'time': t,
                'battery_left': drone.battery
            })
            current = did
    astar_time = time.time() - t1
    astar_ops = len(assignments)

    csp_assignments, csp_time, csp_ops = assign_drones_one_delivery_each(
    drones=copy.deepcopy(drones),
    deliveries=deliveries,
    graph=G,
    positions=positions,
    noflyzones=nofly_zones
)


    fig, ax = plt.subplots(figsize=(10, 10))
    for poly in nofly_zones:
     if hasattr(poly, "polygon"):
        patch = MplPoly(list(poly.polygon.exterior.coords), color='red', alpha=0.2)
     else:
        patch = MplPoly(list(poly.exterior.coords), color='red', alpha=0.2)
     ax.add_patch(patch)


    edge_w = [d['weight'] for _, _, d in G.edges(data=True)]
    max_w = max(edge_w) if edge_w else 1
    widths = [(w / max_w) * 1.5 for w in edge_w]
    nx.draw_networkx_edges(G, positions, width=widths, alpha=0.3, ax=ax)
    nx.draw_networkx_nodes(G, positions, node_size=30, node_color='lightblue', ax=ax)

    cmap = cm.get_cmap('tab10')
    for idx, a in enumerate(assignments):
        pe = list(zip(a['path'], a['path'][1:]))
        color = cmap(idx % 10)
        nx.draw_networkx_edges(G, positions, edgelist=pe, width=3, edge_color=[color], ax=ax)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'], node_size=80, node_color=[color], ax=ax)
        ax.plot([], [], color=color, label=f"GA D{a['drone_id']}→Del{a['delivery_id']}")

    for idx, a in enumerate(csp_assignments):
        pe = list(zip(a['path'], a['path'][1:]))
        color = cmap((idx + 5) % 10)
        nx.draw_networkx_edges(G, positions, edgelist=pe, width=2, edge_color=[color], style='dashed', ax=ax)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'], node_size=40, node_color=[color], ax=ax)
        ax.plot([], [], linestyle='dashed', color=color, label=f"CSP D{a['drone_id']}→Del{a['delivery_id']}")

    xs = [d.start_pos[0] for d in drones]
    ys = [d.start_pos[1] for d in drones]
    ax.scatter(xs, ys, c='green', s=100, marker='s', label='Start')

    nx.draw_networkx_labels(G, positions, font_size=6, ax=ax)
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title(f'Drone Teslimat Rotaları ({scenario_name})')
    ax.axis('off')
    plt.tight_layout()

    out_img = f'assignment_graph_{scenario_name}.png'
    plt.savefig(out_img)

    rapor_yolu = f'performance_log_{scenario_name}.txt'
    success_rate = (len(assignments) / len(deliveries)) * 100 if deliveries else 0
    total_energy = sum(d['distance'] * 0.1 for d in assignments)
    avg_energy = total_energy / len(assignments) if assignments else 0
    total_runtime = ga_time + astar_time + csp_time
    ga_percent = (ga_time / total_runtime) * 100
    astar_percent = (astar_time / total_runtime) * 100
    csp_percent = (csp_time / total_runtime) * 100

    atanan_teslimat_ids = set(a['delivery_id'] for a in assignments)
    reasons = []
    for d in deliveries:
        if d.id not in atanan_teslimat_ids:
            neden = "Uygun drone bulunamadı"
            for drone in drones:
                if d.weight > drone.max_weight:
                    neden = "Ağırlık sınırı aşıldı"
                    break
            reasons.append((d.id, neden))

    with open(rapor_yolu, 'w', encoding='utf-8') as log:
        log.write(f"\n📘 SENARYO: {scenario_name}\n")
        log.write(f"🚁 Drone Sayısı: {len(drones)} | 📦 Teslimat Sayısı: {len(deliveries)} | ⛔ No-Fly Bölge: {len(nofly_zones)}\n\n")
        log.write(f"✅ Başarılı Teslimatlar: {len(assignments)} / {len(deliveries)} (%{success_rate:.2f})\n")
        log.write(f"🔋 Ortalama Enerji Tüketimi: {avg_energy:.2f} birim | Toplam Enerji: {total_energy:.2f} birim\n\n")
        log.write(f"⏱️ Süreler (saniye):\n")
        log.write(f" - Genetik Algoritma (GA): {ga_time:.2f} s\n")
        log.write(f" - A* Arama Algoritması: {astar_time:.2f} s\n")
        log.write(f" - CSP Kontrolleri: {csp_time:.4f} s\n")
        log.write(f" - 🔁 Toplam İşlem Süreci: {total_runtime:.2f} s\n\n")
        log.write(f"📊 Zaman Dağılımı:\n")
        log.write(f" - GA Zaman Payı: %{ga_percent:.2f}\n")
        log.write(f" - A* Zaman Payı: %{astar_percent:.2f}\n")
        log.write(f" - CSP Zaman Payı: %{csp_percent:.4f}\n\n")
        log.write("🧠 Teorik Zaman Karmaşıklıkları:\n")
        log.write(" - Genetik Algoritma: O(P × G × N)\n")
        log.write(" - A*: O(E + V log V)\n")
        log.write(" - CSP: O(P × Z)\n\n")
        log.write("📈 Sayısal Zaman Karmaşıklıkları:\n")
        log.write(f" - GA: {ga_ops} işlem\n")
        log.write(f" - A*: {astar_ops} işlem\n")
        log.write(f" - CSP: {csp_ops} işlem\n\n")
        for a in assignments:
            log.write(f"🔧 Drone {a['drone_id']} -> Teslimat {a['delivery_id']}: Mesafe = {a['distance']:.2f} m, Süre = {a['time']} s, Kalan Batarya = {a['battery_left']:.2f}\n")
        for did, reason in reasons:
            log.write(f"⚠️ Teslimat {did} atanamadı: {reason}\n")

    print(f"📄 Rapor yazıldı: {rapor_yolu}")
    print(f"🖼️ Grafik kaydedildi: {out_img}")

if __name__ == '__main__':
    main()