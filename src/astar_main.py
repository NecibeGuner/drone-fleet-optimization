import os
import copy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Polygon
from matplotlib.patches import Polygon as MplPoly
import matplotlib.cm as cm

from data_loader import load_data
from modules.graph_builder import GraphBuilder
from modules.astar import astar
from genetic import genetic_algorithm, nearest_node, format_dist

def main():
    # 1) Verileri yükle
    drones, deliveries, nofly_zones = load_data()
    polygons = [Polygon(z.coordinates) for z in nofly_zones]

    # 2) Grafik oluştur
    G = GraphBuilder(deliveries, polygons).build()
    positions = {n: (d['x'], d['y']) for n, d in G.nodes(data=True)}

    # 3) GA ile görev ataması yap
    best_assign = genetic_algorithm(
        drones=drones,
        deliveries=deliveries,
        graph=G,
        positions=positions,
        nofly_zones=polygons,
        battery_consumption_rate=0.008,
        population_size=1000,
        generations=10
    )

    # 4) A* ile rota oluştur, sonuçları yaz
    assignments = []
    sim_drones = [copy.deepcopy(d) for d in drones]
    for di, route in enumerate(best_assign):
        drone = sim_drones[di]
        current = nearest_node(drone.start_pos, positions)
        for did in route:
            delivery = next((d for d in deliveries if d.id == did), None)
            if not delivery or delivery.weight > drone.max_weight:
                continue
            path, _, dist = astar(
                G, current, did, positions,
                drone.speed, noflyzones=polygons
            )
            if not path:
                print(f"Drone {drone.id} -> Delivery {did} için yol bulunamadı.")
                continue
            needed = dist * 0.1
            if drone.battery < needed:
                print(f"Drone {drone.id} -> Delivery {did} için yeterli batarya yok.")
                break
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

    # 5) assignment_info.txt kaydet
    out_txt = os.path.join(os.path.dirname(__file__), 'assignment_info.txt')
    with open(out_txt, 'w', encoding='utf-8') as f:
        for a in assignments:
            f.write(
                f"Drone {a['drone_id']} -> Delivery {a['delivery_id']}: "
                f"path={a['path']}, dist={format_dist(a['distance'])}, "
                f"time={a['time']}s, battery left={a['battery_left']} mAh\n"
            )
    print(f"Atamalar '{out_txt}' dosyasına kaydedildi.")

    # 6) Görsel oluştur
    fig, ax = plt.subplots(figsize=(10, 10))
    for poly in polygons:
        patch = MplPoly(list(poly.exterior.coords), color='red', alpha=0.2)
        ax.add_patch(patch)

    # Ağ çizimleri
    edge_w = [d['weight'] for _, _, d in G.edges(data=True)]
    max_w = max(edge_w) if edge_w else 1
    widths = [(w / max_w) * 1.5 for w in edge_w]
    nx.draw_networkx_edges(G, positions, width=widths, alpha=0.3, ax=ax)
    nx.draw_networkx_nodes(G, positions, node_size=30, node_color='lightblue', ax=ax)

    # Rotalar
    cmap = cm.get_cmap('tab10')
    for idx, a in enumerate(assignments):
        pe = list(zip(a['path'], a['path'][1:]))
        color = cmap(idx % 10)
        nx.draw_networkx_edges(G, positions, edgelist=pe, width=3,
                               edge_color=[color], ax=ax)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'],
                               node_size=80, node_color=[color], ax=ax)
        ax.plot([], [], color=color, label=f"D{a['drone_id']}→Del{a['delivery_id']}")

    # Başlangıç noktaları
    xs = [d.start_pos[0] for d in drones]
    ys = [d.start_pos[1] for d in drones]
    ax.scatter(xs, ys, c='green', s=100, marker='s', label='Start')

    nx.draw_networkx_labels(G, positions, font_size=6, ax=ax)
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title('GA + A* ile Drone Teslimat Rotaları')
    ax.axis('off')
    plt.tight_layout()
    out_img = os.path.join(os.path.dirname(__file__), 'assignment_graph.png')
    plt.savefig(out_img)
    print(f"Görsel '{out_img}' kaydedildi.")

if __name__ == '__main__':
    main()
