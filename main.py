import math
import sys

from Entregas_ContraSur.models import EmpresaLogistica, Vehiculo

# ── Entrada por consola ──
def preguntar(prompt, default=""):
    try:
        r = input(prompt + (f" [{default}]" if default != "" else "") + ": ")
    except EOFError:
        print("\nEntrada finalizada. Saliendo.")
        sys.exit(1)
    r = r.strip()
    return str(default) if r == "" else r


def numero(prompt, default="", minimo=0, entero=False, min_excl=False):
    while True:
        t = preguntar(prompt, default).replace(",", ".")
        try:
            n = float(t)
            ok = math.isfinite(n) and (n > minimo if min_excl else n >= minimo)
            if entero:
                ok = ok and n.is_integer()
        except ValueError:
            ok = False
        if ok:
            return int(n) if entero else n
        print(
            f"Valor invalido. Ingresa un numero{' entero' if entero else ''} "
            f"{'>' if min_excl else '≥'} {minimo}."
        )


def linea(c="─"):
    print(c * 64)


def titulo(t):
    print()
    linea("═")
    print("  " + t)
    linea("═")


def cop(x):
    return f"{math.floor(x + 0.5):,}".replace(",", ".")


# ── Pasos ──
def pedir_pedidos(empresa):
    titulo("1) PEDIDOS / PUNTOS DE ENTREGA (Ibague)")
    n = numero("¿Cuantos puntos de entrega hay?", minimo=1, entero=True)
    for i in range(1, n + 1):
        print(f"\n— Pedido {i} de {n}")
        direccion = preguntar("  Direccion o barrio (ej. Cra 5 #30-10, Jordan)", f"Entrega {i}")
        peso = numero("  Peso (kg)", default=5, minimo=0, min_excl=True)
        volumen = numero("  Volumen", default=0.02, minimo=0, min_excl=True)
        while True:
            prioridad = preguntar("  Prioridad (alta/media/baja)", "media").lower()
            if prioridad in ("alta", "media", "baja"):
                break
            print("Escribe alta, media o baja.")
        empresa.agregar_pedido(direccion=direccion, peso=peso, volumen=volumen, prioridad=prioridad)


def pedir_distancias(empresa):
    titulo("2) DISTANCIAS EN KILOMETROS")
    pedidos = empresa.pedidos
    n = len(pedidos)
    origen = preguntar("Nombre del punto de recogida", "Punto de recogida")
    empresa.origen = origen

    m = [[0.0] * (n + 1) for _ in range(n + 1)]

    print(f'\nKm desde "{origen}" hasta cada punto de entrega:')
    for i in range(n):
        d = numero(f"  -> {pedidos[i].direccion}", minimo=0, min_excl=True)
        m[0][i + 1] = m[i + 1][0] = d

    if n > 1:
        print("\nAhora los km ENTRE puntos de entrega (se necesitan para encontrar el mejor orden \n" "Si dejas vacio, se estima con la ruta mas corta pasando por la recogida.")
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                est = f"{m[0][i] + m[0][j]:.2f}"
                d = numero(
                    f"  {pedidos[i - 1].direccion}  ↔  {pedidos[j - 1].direccion}",
                    default=est, minimo=0, min_excl=True,
                )
                m[i][j] = m[j][i] = d
    empresa.set_distancias(m)


def pedir_flota(empresa):
    titulo("3) FLOTA DE VEHICULOS")
    defs = Vehiculo.get_defaults()
    print("Tipos: moto (30kg), van (500kg), camion (5000kg)")
    usar_def = preguntar("¿Usar flota por defecto (1 moto, 1 van, 1 camion)? (s/n)", "s").lower()
    if usar_def.startswith("s"):
        for tipo in ("moto", "van", "camion"):
            empresa.agregar_vehiculo(tipo=tipo)
        return
    n = numero("¿Cuantos vehiculos?", minimo=1, entero=True)
    for i in range(1, n + 1):
        while True:
            tipo = preguntar(f"  Vehiculo {i} tipo (moto/van/camion)", "moto").lower()
            if tipo in defs:
                break
            print("Tipo invalido.")
        d = defs[tipo]
        cap_peso = numero("    Capacidad peso (kg)", default=d["cap_peso"], minimo=0, min_excl=True)
        cap_vol = numero("    Capacidad volumen", default=d["cap_volumen"], minimo=0, min_excl=True)
        consumo = numero("    Consumo (L/100km)", default=d["consumo"], minimo=0, min_excl=True)
        empresa.agregar_vehiculo(tipo=tipo, cap_peso=cap_peso, cap_volumen=cap_vol, consumo=consumo)


def mostrar_resultados(empresa, rutas, mostrar_log):
    titulo("RESULTADOS")
    origen = empresa.origen or "Recogida"
    for k, r in enumerate(rutas, 1):
        print(f"\nViaje {k} — {r.vehiculo}")
        n = len(r.puntos)
        paradas = [origen if i in (0, n - 1) else p.direccion for i, p in enumerate(r.puntos)]
        print("  Ruta: " + "  ->  ".join(paradas))
        idx, m = r.ruta_global, empresa.matriz_ordenada
        if idx and m:
            for i in range(len(idx) - 1):
                print(f"    {paradas[i]} -> {paradas[i + 1]}: {m[idx[i]][idx[i + 1]]:.2f} km")
        s = r.summary()
        print(
            f"  Distancia: {s['distancia']} | Tiempo aprox: {s['tiempo']} | "
            f"Combustible: {s['combustible']} | Carga: {s['peso_total']}"
        )

    asignados = sum(len(r.pedidos) for r in rutas)
    if asignados < len(empresa.pedidos):
        print(f"\n⚠ {len(empresa.pedidos) - asignados} pedidos NO se pudieron asignar (exceden la capacidad de la flota).")

    st = empresa.get_stats()
    if st:
        linea()
        print("ESTADISTICAS GLOBALES")
        print(f"  Viajes: {st['viajes']} | Pedidos asignados: {st['pedidos_asignados']}/{len(empresa.pedidos)}")
        print(f"  Distancia total: {st['dist_total']:.2f} km")
        print(f"  Tiempo total: {math.floor(st['time_total'] + 0.5)} min")
        print(f"  Combustible: {st['fuel_total']:.2f} L  (~${cop(st['costo_total'])} COP)")
        print(f"  Sin optimizar (ida y vuelta a cada punto): {st['naive_dist']:.2f} km")
        print(f"  Ahorro: {st['ahorro_dist']:.2f} km (~${cop(st['ahorro_money'])} COP)")
    if mostrar_log:
        print()
        linea()
        print("LOG DE ALGORITMOS")
        for l in empresa.log:
            print("  " + l)


def main():
    print("\n  ENTREGAS CONTRASUR — Optimizacion de rutas CVRP · Ibague")
    print("  (todo se ingresa por terminal; Enter acepta el valor entre [corchetes])")

    empresa = EmpresaLogistica("Entregas ContraSur Ibague")
    pedir_pedidos(empresa)
    pedir_distancias(empresa)
    pedir_flota(empresa)

    titulo("4) PARAMETROS")
    empresa.precio_combustible = numero(
        "Precio combustible (COP por litro)", default=empresa.precio_combustible, minimo=0, min_excl=True
    )
    ver_log = preguntar("¿Mostrar log detallado de los algoritmos? (s/n)", "n").lower().startswith("s")

    try:
        rutas = empresa.optimizar()
        mostrar_resultados(empresa, rutas, ver_log)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()