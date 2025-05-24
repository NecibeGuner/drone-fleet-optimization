import os
import math
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
from genetic import genetic_algorithm

def nearest_node(pos, positions):
    """Verilen pozisyona en yakın düğümü bulur."""
    x, y = pos
    return min(positions.keys(), key=lambda node: math.hypot(positions[node][0] - x, positions[node][1] - y))

def main():
    # 1) Verileri yükle ve grafı oluştur
    drones, deliveries, nofly_zones = load_data()
    polygons = [Polygon(z.coordinates) for z in nofly_zones]
    G = GraphBuilder(deliveries, polygons).build()
    positions = {n: (d['x'], d['y']) for n, d in G.nodes(data=True)}

    # 2) Genetik algoritma ile teslimatları ata
    best_assignment = genetic_algorithm(
        drones=drones,
        deliveries=deliveries,
        graph=G,
        positions=positions,
        nofly_zones=nofly_zones,
        battery_consumption_rate=0.1,
        population_size=50,
        generations=10
    )

    # 3) A* ile her drone için rota planla
    assignments = []
    for drone_id, delivery_ids in enumerate(best_assignment):
        drone = drones[drone_id]
        drone.battery = 100.0
        start_node = nearest_node(drone.start_pos, positions)

        for delivery_id in delivery_ids:
            delivery = next((d for d in deliveries if d.id == delivery_id), None)
            if not delivery or delivery.weight > drone.max_weight:
                continue  # kapasiteyi aşan paketi atla

            goal_node = delivery.id
            path, total_cost, total_distance = astar(G, start_node, goal_node, positions, drone.speed, noflyzones=polygons)
            if not path:
                continue  # erişilemezse atla

            required_battery = total_distance * 0.1  # 0.1 batarya/m
            if drone.battery < required_battery:
                break  # yeterli batarya yok

            drone.battery -= required_battery
            time = round(total_distance / drone.speed, 2)
            assignments.append({
                'drone_id': drone.id,
                'delivery_id': delivery.id,
                'path': path,
                'distance': total_distance,
                'time': time,
                'battery_left': drone.battery
            })
            start_node = goal_node

    # 4) Atama bilgilerini yaz
    def format_dist(d):
        return f"{d*100:.0f}cm" if d < 1 else f"{d:.2f}m"

    out_txt = os.path.join(os.path.dirname(__file__), 'assignment_info.txt')
    with open(out_txt, 'w', encoding='utf-8') as f:
        for a in assignments:
            f.write(f"Drone {a['drone_id']} -> Delivery {a['delivery_id']}: "
                    f"path={a['path']}, dist={format_dist(a['distance'])}, "
                    f"time={a['time']:.1f}s, battery left={a['battery_left']:.1f}%\n")
    print(f"Atamalar '{out_txt}' dosyasına kaydedildi.")

    # 5) Görselleştirme
    fig, ax = plt.subplots(figsize=(10, 10))

    for poly in polygons:
        patch = MplPoly(list(poly.exterior.coords), color='red', alpha=0.2)
        ax.add_patch(patch)

    edge_data = G.edges(data=True)
    max_w = max((a['weight'] for _, _, a in edge_data), default=1)
    widths = [(a['weight'] / max_w) * 1.5 for _, _, a in edge_data]
    nx.draw_networkx_edges(G, positions, width=widths, alpha=0.3, ax=ax)
    nx.draw_networkx_nodes(G, positions, node_size=30, node_color='lightblue', ax=ax)

    cmap = matplotlib.colormaps.get_cmap('tab10')
    for idx, a in enumerate(assignments):
        path_edges = list(zip(a['path'], a['path'][1:]))
        color = cmap(idx)
        nx.draw_networkx_edges(G, positions, edgelist=path_edges, width=3, edge_color=[color], ax=ax)
        nx.draw_networkx_nodes(G, positions, nodelist=a['path'], node_size=100, node_color=[color], ax=ax)
        ax.plot([], [], color=color, label=f"D{a['drone_id']}→Del{a['delivery_id']}")

    xs = [d.start_pos[0] for d in drones]
    ys = [d.start_pos[1] for d in drones]
    ax.scatter(xs, ys, c='green', s=100, marker='s', label='Drone Start')

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
