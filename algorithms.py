from __future__ import annotations

import math


# ═════════ DIJKSTRA — camino minimo desde el punto de recogida (idx 0) ═════════
def dijkstra(dist_matrix, source=0):
    n = len(dist_matrix)
    dist = [math.inf] * n
    prev = [-1] * n
    visited = [False] * n
    dist[source] = 0

    for _ in range(n):
        u = -1
        for v in range(n):
            if not visited[v] and (u == -1 or dist[v] < dist[u]):
                u = v
        if u == -1 or dist[u] == math.inf:
            break
        visited[u] = True

        for v in range(n):
            if not visited[v] and dist_matrix[u][v] > 0:
                alt = dist[u] + dist_matrix[u][v]
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u

    return dist, prev


# ════════════════════ KRUSKAL — Árbol de expansión minima ════════════════════
def kruskal(dist_matrix):
    n = len(dist_matrix)
    edges = [(dist_matrix[i][j], i, j) for i in range(n) for j in range(i + 1, n)]
    edges.sort(key=lambda e: e[0])

    parent = list(range(n))
    rank = [0] * n

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True

    mst = []
    total = 0.0
    for w, u, v in edges:
        if union(u, v):
            mst.append((u, v, w))
            total += w
            if len(mst) == n - 1:
                break
    return mst, total


# ═════════ MOCHILA — qué pedidos caben en un vehiculo ═════════
def mochila(items, max_weight, max_volume):
    n = len(items)
    
    sw, sv = 10, 100
    while math.floor(max_weight * sw) * math.floor(max_volume * sv) > 50000:
        sw /= 2
        sv /= 2
    W = int(math.floor(max_weight * sw))
    V = int(math.floor(max_volume * sv))

    dp = [[0.0] * (V + 1) for _ in range(W + 1)]
    keep = [[bytearray(V + 1) for _ in range(W + 1)] for _ in range(n)]

    for i in range(n):
        iw = math.ceil(items[i]["weight"] * sw)
        iv = math.ceil(items[i]["volume"] * sv)
        val = items[i].get("value") or items[i]["weight"] + items[i]["volume"] * 10
        for w in range(W, iw - 1, -1):
            for v in range(V, iv - 1, -1):
                candidate = dp[w - iw][v - iv] + val
                if candidate > dp[w][v]:
                    dp[w][v] = candidate
                    keep[i][w][v] = 1

    selected = []
    w, v = W, V
    for i in range(n - 1, -1, -1):
        iw = math.ceil(items[i]["weight"] * sw)
        iv = math.ceil(items[i]["volume"] * sv)
        if keep[i][w][v]:
            selected.append(i)
            w -= iw
            v -= iv
    selected.reverse()
    return selected


# ═════════ DIVIDE Y VENCERÁS — merge sort ═════════
def merge_sort(arr, key):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    return _merge(merge_sort(arr[:mid], key), merge_sort(arr[mid:], key), key)


def _merge(left, right, key):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    return result + left[i:] + right[j:]