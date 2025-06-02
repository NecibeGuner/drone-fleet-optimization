import networkx as nx
import math
from shapely.geometry import LineString, Polygon

class GraphBuilder:
    def __init__(self, delivery_points, nofly_zones=None):
        """
        delivery_points: list of DeliveryPoint örnekleri
            Her birinde .id, .x, .y, .weight, .priority alanları olmalı.
        nofly_zones: list of shapely.geometry.Polygon örnekleri
        """
        self.points = delivery_points
        self.nofly = nofly_zones or []
        self.G = nx.Graph()

    def build(self):
        # 1. Düğümleri ekle
        for p in self.points:
            self.G.add_node(p.id, x=p.x, y=p.y, weight=p.weight, priority=p.priority)

        # 2. Kenarları oluştur
        n = len(self.points)
        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = self.points[i], self.points[j]
                if not self._crosses_nofly(p1, p2):
                    dist = self._euclid(p1, p2)
                    # PDF gereği maliyet = mesafe * ağırlık + (öncelik * 100)
                    avg_weight = (p1.weight + p2.weight) / 2
                    avg_priority = (p1.priority + p2.priority) / 2
                    cost = dist * avg_weight + (avg_priority * 100)
                    self.G.add_edge(p1.id, p2.id, weight=cost, raw_distance=dist)
        return self.G

    def _euclid(self, a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def _crosses_nofly(self, a, b):
     segment = LineString([(a.x, a.y), (b.x, b.y)])
     return any(segment.crosses(zone.polygon if hasattr(zone, "polygon") else zone) for zone in self.nofly)
