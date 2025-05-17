import heapq
import math
from datetime import datetime
from drone import Drone
from delivery import Delivery
from noflyzone import NoFlyZone

# ❯ Heuristic function: Euclidean distance
def heuristic(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

# ❯ Komşu noktalar: 4 yön (yukarı, aşağı, sağ, sol)
def neighbors(pos, max_x, max_y):
    x, y = pos
    directions = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return [(nx, ny) for nx, ny in directions if 0 <= nx <= max_x and 0 <= ny <= max_y]

# ❯ Belirli bir noktada no-fly zone var mı ve aktif mi
def is_in_active_no_fly_zone(pos, no_fly_zones, current_time):
    for zone in no_fly_zones:
        if zone.is_active(current_time):
            xs = [c[0] for c in zone.coordinates]
            ys = [c[1] for c in zone.coordinates]
            if min(xs) <= pos[0] <= max(xs) and min(ys) <= pos[1] <= max(ys):
                return True
    return False

# ❯ Yol geri izleme
def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

# ❯ Hareket maliyeti hesaplama: (mesafe × ağırlık) + öncelik cezası
def movement_cost(current, neighbor, weight, priority):
    distance = heuristic(current, neighbor)
    return (distance * weight) + (priority * 100)

# ❯ A* algoritması
def astar(start, goal, drone, delivery, no_fly_zones, current_time, max_x=100, max_y=100):
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        visited.add(current)

        for neighbor in neighbors(current, max_x, max_y):
            if is_in_active_no_fly_zone(neighbor, no_fly_zones, current_time):
                continue  # No-fly zone varsa atla

            tentative_g = g_score[current] + movement_cost(current, neighbor, delivery.weight, delivery.priority)

            if neighbor in visited and tentative_g >= g_score.get(neighbor, float('inf')):
                continue

            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                h = heuristic(neighbor, goal)
                # Ekstra ceza: No-fly zone tahmini varsa cezalandır
                if is_in_active_no_fly_zone(neighbor, no_fly_zones, current_time):
                    h += 1000

                f = tentative_g + h
                heapq.heappush(open_set, (f, neighbor))

    return None  # Rota bulunamadı

# ❯ Drone için tüm teslimatları kapsayan path

def find_optimal_route(drone, deliveries, no_fly_zones, current_time, max_x=100, max_y=100):
    total_route = [drone.start_pos]
    current_pos = drone.start_pos
    total_weight = 0

    for delivery in deliveries:
        total_weight += delivery.weight
        if total_weight > drone.capacity:
            print(f"Uyarı: {delivery.id} için kapasite aşıldı. Rota sonlandırılıyor.")
            break

        path = astar(current_pos, delivery.pos, drone, delivery, no_fly_zones, current_time, max_x, max_y)
        if path is None:
            print(f"{delivery.id} için rota bulunamadı.")
            continue

        total_route.extend(path[1:])
        current_pos = delivery.pos

    return total_route