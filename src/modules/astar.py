import math
import networkx as nx
from heapq import heappush, heappop
from shapely.geometry import LineString

def calculate_heuristic(u, v, positions, speed, noflyzones=None, penalty_weight=1000):
    """
    A* algoritması için tahmin fonksiyonu.
    Uzaklık + no-fly zone cezası içerir.
    """
    x1, y1 = positions[u]
    x2, y2 = positions[v]
    distance = math.hypot(x1 - x2, y1 - y2)

    penalty = 0
    if noflyzones:
        line = LineString([positions[u], positions[v]])
        for zone in noflyzones:
            if line.intersects(zone):
                penalty += penalty_weight

    return (distance + penalty) / speed

def astar(graph: nx.Graph, start: int, goal: int, positions: dict, speed: float, noflyzones=None, penalty_weight=1000):
    """
    A* algoritması ile en kısa rotayı bulur.

    Returns:
        path (list): Düğüm ID’leri listesi
        total_cost (float): Graf üzerindeki kenar ağırlıkları toplamı
        total_distance (float): Gerçek fiziksel mesafe (raw_distance toplamı)
    """
    open_set = []
    heappush(open_set, (calculate_heuristic(start, goal, positions, speed, noflyzones, penalty_weight), 0.0, start, [start]))
    g_scores = {start: 0.0}

    while open_set:
        f_score, g_score_current, current, path = heappop(open_set)

        if current == goal:
            # Gerçek fiziksel mesafe (raw_distance)
            total_distance = sum(graph.edges[u, v]['raw_distance'] for u, v in zip(path, path[1:]))
            return path, g_score_current, total_distance

        for neighbor, attrs in graph[current].items():
            edge_weight = attrs.get('weight', 1.0)
            tentative_g_score = g_score_current + edge_weight
            if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                g_scores[neighbor] = tentative_g_score
                f = tentative_g_score + calculate_heuristic(neighbor, goal, positions, speed, noflyzones, penalty_weight)
                heappush(open_set, (f, tentative_g_score, neighbor, path + [neighbor]))

    return None, float('inf'), float('inf')
