from __future__ import annotations

import math
from datetime import datetime

from Entregas_ContraSur.algorithms import dijkstra, kruskal, mochila, merge_sort


# ════════════════════════════ CLASS: Pedido ════════════════════════════
class Pedido:
    _counter = 0

    def __init__(self, direccion, peso, volumen, prioridad="media"):
        if peso < 0 or volumen < 0:
            raise ValueError("Peso y volumen deben ser positivos")
        Pedido._counter += 1
        self.id = Pedido._counter
        self.direccion = direccion or f"Entrega {self.id}"
        self.peso = float(peso)
        self.volumen = float(volumen)
        self.prioridad = prioridad
        self.created_at = datetime.now()
        self.asignado = False

    @property
    def valor(self):
        return {"alta": 3, "media": 2, "baja": 1}.get(self.prioridad, 1) * (
            self.peso + self.volumen * 10
        )

    def __str__(self):
        return f"Pedido#{self.id} [{self.prioridad}] {self.direccion} | {self.peso}kg / {self.volumen}m³"

    @staticmethod
    def reset_counter():
        Pedido._counter = 0


# ════════════════════════════ CLASS: Vehiculo ════════════════════════════
class Vehiculo:
    _DEFAULTS = {
        "moto": {"cap_peso": 30, "cap_volumen": 0.15, "consumo": 3.0, "icon": "🏍️", "speed": 35},
        "van": {"cap_peso": 500, "cap_volumen": 5.0, "consumo": 8.0, "icon": "🚐", "speed": 45},
        "camion": {"cap_peso": 5000, "cap_volumen": 30.0, "consumo": 25.0, "icon": "🚚", "speed": 40},
    }
    _counter = 0

    def __init__(self, tipo, cap_peso=None, cap_volumen=None, consumo=None):
        if tipo not in Vehiculo._DEFAULTS:
            raise ValueError(f"Tipo de vehiculo desconocido: {tipo}")
        d = Vehiculo._DEFAULTS[tipo]
        Vehiculo._counter += 1
        self.id = Vehiculo._counter
        self.tipo = tipo
        self.cap_peso = float(cap_peso or d["cap_peso"])
        self.cap_volumen = float(cap_volumen or d["cap_volumen"])
        self.consumo = float(consumo or d["consumo"])
        self.icon = d["icon"]
        self.speed = d["speed"]
        self.disponible = True

    def can_carry(self, peso, volumen):
        return peso <= self.cap_peso and volumen <= self.cap_volumen

    def calc_fuel(self, dist_km):
        return dist_km * (self.consumo / 100)

    def calc_time(self, dist_km):
        return dist_km / self.speed * 60  # minutos

    def __str__(self):
        return f"{self.icon} {self.tipo.upper()} #{self.id} | {fmt(self.cap_peso)}kg / {fmt(self.cap_volumen)}m³"

    @staticmethod
    def get_defaults():
        return {k: dict(v) for k, v in Vehiculo._DEFAULTS.items()}

    @staticmethod
    def reset_counter():
        Vehiculo._counter = 0


def fmt(x):
    """Formatea como JS: 30.0 -> '30', 0.15 -> '0.15'."""
    return str(int(x)) if float(x).is_integer() else str(x)


# ════════════════════════════ CLASS: Ruta ════════════════════════════
class Ruta:
    def __init__(self, vehiculo, pedidos, puntos, dist_km, ruta_global=None):
        self.ruta_global = ruta_global
        self.vehiculo = vehiculo
        self.pedidos = pedidos
        self.puntos = puntos  # paradas en orden (primer y último = punto de recogida)
        self.dist_km = dist_km
        self.calculada_en = datetime.now()

    @property
    def time_min(self):
        return self.vehiculo.calc_time(self.dist_km)

    @property
    def fuel_l(self):
        return self.vehiculo.calc_fuel(self.dist_km)

    @property
    def peso_total(self):
        return sum(p.peso for p in self.pedidos)

    @property
    def volumen_total(self):
        return sum(p.volumen for p in self.pedidos)

    @property
    def carga_peso_ratio(self):
        return self.peso_total / self.vehiculo.cap_peso

    def summary(self):
        return {
            "vehiculo": str(self.vehiculo),
            "pedidos": len(self.pedidos),
            "distancia": f"{self.dist_km:.2f} km",
            "tiempo": f"{math.floor(self.time_min + 0.5)} min",
            "combustible": f"{self.fuel_l:.2f} L",
            "peso_total": f"{self.peso_total:.1f} kg",
        }

    def __str__(self):
        n = len(self.puntos)
        stops = " -> ".join(
            "Recogida" if i in (0, n - 1) else p.direccion for i, p in enumerate(self.puntos)
        )
        return f"Ruta [{self.vehiculo.tipo}] {stops} | {self.dist_km:.2f}km"


# ════════════════════════════ CLASS: EmpresaLogistica ════════════════════════════
class EmpresaLogistica:
    def __init__(self, nombre="Entregas ContraSur Ibague"):
        self.nombre = nombre
        self.pedidos: list[Pedido] = []
        self.vehiculos: list[Vehiculo] = []
        self.rutas: list[Ruta] = []
        self.dist_matrix = None 
        self.matriz_ordenada = None
        self.origen = None
        self.precio_combustible = 4200 
        self._log: list[str] = []

    # ── Pedidos ──
    def agregar_pedido(self, **data):
        p = Pedido(**data)
        self.pedidos.append(p)
        return p

    def eliminar_pedido(self, id):
        self.pedidos = [p for p in self.pedidos if p.id != id]

    def limpiar_pedidos(self):
        self.pedidos = []
        Pedido.reset_counter()

    # ── Vehículos ──
    def agregar_vehiculo(self, **data):
        v = Vehiculo(**data)
        self.vehiculos.append(v)
        return v

    def eliminar_vehiculo(self, id):
        self.vehiculos = [v for v in self.vehiculos if v.id != id]

    def set_distancias(self, matrix):
        self.dist_matrix = matrix

    # ── Optimización principal ──
    def optimizar(self):
        self._log = []
        log = self._log
        if not self.pedidos:
            raise ValueError("Sin pedidos")
        if not self.vehiculos:
            raise ValueError("Sin vehículos")
        if not self.dist_matrix:
            raise ValueError("Faltan las distancias en km")

        orders = self.pedidos
        log.append(f"[CVRP] Iniciando con {len(orders)} pedidos y {len(self.vehiculos)} vehiculos")

        # Divide y vencerás: ordenar pedidos por distancia al punto de recogida
        with_idx = [(o, i, self.dist_matrix[0][i + 1]) for i, o in enumerate(orders)]
        sorted_idx = merge_sort(with_idx, key=lambda x: x[2])
        sorted_orders = [x[0] for x in sorted_idx]
        order = [0] + [x[1] + 1 for x in sorted_idx]
        dm = [[self.dist_matrix[a][b] for b in order] for a in order]
        points = [{"nombre": "Punto de recogida"}, *sorted_orders]
        log.append("[D&C] Pedidos ordenados por distancia al punto de recogida")

        shortest_from_depot, _ = dijkstra(dm, 0)
        log.append("[Dijkstra] Distancias minimas desde depósito calculadas")

        _, mst_weight = kruskal(dm)
        log.append(f"[Kruskal] MST peso total: {mst_weight:.2f}km (cota inferior)")

        prio = {"alta": 3, "media": 2}
        rutas = []
        remaining = list(range(1, len(sorted_orders) + 1))

        while remaining:
            assigned = False
            for vehicle in sorted(self.vehiculos, key=lambda v: -(v.cap_peso + v.cap_volumen * 100)):
                items = [
                    {
                        "id": idx,
                        "weight": sorted_orders[idx - 1].peso,
                        "volume": sorted_orders[idx - 1].volumen,
                        "value": prio.get(sorted_orders[idx - 1].prioridad, 1) * 10
                        + shortest_from_depot[idx],
                    }
                    for idx in remaining
                ]
                log.append(f"[Mochila] Evaluando {len(items)} pedidos para {vehicle.tipo}")
                selected_local = mochila(items, vehicle.cap_peso, vehicle.cap_volumen)
                if not selected_local:
                    continue

                # ids ascendentes = de menor a mayor distancia a la recogida
                selected = sorted(items[i]["id"] for i in selected_local)
                log.append(f"[Mochila] Seleccionados {len(selected)} pedidos para {vehicle.tipo}")

                route_global = [0, *selected, 0]
                dist_km = sum(dm[route_global[i]][route_global[i + 1]] for i in range(len(route_global) - 1))
                rutas.append(Ruta(
                    vehiculo=vehicle,
                    pedidos=[sorted_orders[i - 1] for i in selected],
                    puntos=[points[i] for i in route_global],
                    dist_km=dist_km,
                    ruta_global=route_global,
                ))
                remaining = [idx for idx in remaining if idx not in selected]
                assigned = True
                break

            if not assigned:
                log.append(f"[WARN] {len(remaining)} pedidos no pudieron asignarse (exceden capacidad)")
                break

        self.rutas = rutas
        self.matriz_ordenada = dm if rutas else None
        log.append(f"[CVRP] Solución completada: {len(rutas)} rutas generadas")
        return self.rutas

    # ── Estadísticas globales ──
    def get_stats(self, precio_combustible=None):
        precio = self.precio_combustible if precio_combustible is None else precio_combustible
        if not self.rutas:
            return None
        dist_total = sum(r.dist_km for r in self.rutas)
        time_total = sum(r.time_min for r in self.rutas)
        fuel_total = sum(r.fuel_l for r in self.rutas)
        costo_total = fuel_total * precio

        # Sin optimizar: ida y vuelta a cada cliente por separado
        naive_dist = sum(2 * self.dist_matrix[0][i + 1] for i in range(len(self.pedidos)))
        # mismo consumo promedio (L/km) que las rutas reales, para comparar justo
        naive_fuel = naive_dist * (fuel_total / dist_total) if dist_total > 0 else 0
        ahorro_dist = naive_dist - dist_total
        ahorro_fuel = naive_fuel - fuel_total
        ahorro_money = ahorro_fuel * precio

        return {
            "dist_total": dist_total,
            "time_total": time_total,
            "fuel_total": fuel_total,
            "costo_total": costo_total,
            "viajes": len(self.rutas),
            "pedidos_asignados": sum(len(r.pedidos) for r in self.rutas),
            "ahorro_dist": ahorro_dist,
            "ahorro_fuel": ahorro_fuel,
            "ahorro_money": ahorro_money,
            "naive_dist": naive_dist,
        }

    @property
    def log(self):
        return list(self._log)