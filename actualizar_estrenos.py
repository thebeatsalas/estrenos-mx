"""
Actualizador de calendario de estrenos de cine en México (vía TMDB).

Qué hace:
1. Consulta TMDB (now_playing + upcoming) filtrado a México (region=MX).
2. Compara contra estrenos.json (la corrida anterior).
3. Actualiza estrenos.json con los datos nuevos.
4. Regenera estrenos.ics con todos los estrenos vigentes.
5. Imprime un resumen de cambios (nuevas películas / fechas modificadas).

Requiere la variable de entorno TMDB_API_KEY (API Read Access Token, tipo v4 "Bearer").
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from ics import Calendar, Event

TMDB_BASE = "https://api.themoviedb.org/3"
REGION = "MX"
LANGUAGE = "es-MX"

DATA_FILE = Path(__file__).parent / "estrenos.json"
ICS_FILE = Path(__file__).parent / "estrenos.ics"

# Cuántos meses hacia adelante buscar estrenos "upcoming"
MESES_ADELANTE = 6


def get_api_key() -> str:
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        print("ERROR: falta la variable de entorno TMDB_API_KEY", file=sys.stderr)
        sys.exit(1)
    return key


def tmdb_get(session: requests.Session, path: str, params: dict) -> dict:
    resp = session.get(f"{TMDB_BASE}{path}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def obtener_estrenos(session: requests.Session) -> dict:
    """
    Junta 'now_playing' y 'discover' (con fecha de estreno en MX a futuro)
    y devuelve un dict {tmdb_id: {titulo, fecha, popularidad}}.
    """
    resultados = {}

    hoy = datetime.utcnow().date()
    fin = hoy + timedelta(days=30 * MESES_ADELANTE)

    # now_playing: lo que ya está en cartelera en México
    for pagina in range(1, 4):
        data = tmdb_get(
            session,
            "/movie/now_playing",
            {"region": REGION, "language": LANGUAGE, "page": pagina},
        )
        for peli in data.get("results", []):
            if peli.get("release_date"):
                resultados[peli["id"]] = {
                    "titulo": peli.get("title"),
                    "fecha": peli["release_date"],
                    "popularidad": peli.get("popularity", 0),
                }
        if pagina >= data.get("total_pages", 1):
            break

    # discover: estrenos futuros en México, ordenados por fecha
    for pagina in range(1, 6):
        data = tmdb_get(
            session,
            "/discover/movie",
            {
                "region": REGION,
                "language": LANGUAGE,
                "with_release_type": "2|3",  # 2=limitado, 3=amplio (theatrical)
                "release_date.gte": hoy.isoformat(),
                "release_date.lte": fin.isoformat(),
                "sort_by": "primary_release_date.asc",
                "page": pagina,
            },
        )
        for peli in data.get("results", []):
            if peli.get("release_date"):
                resultados[peli["id"]] = {
                    "titulo": peli.get("title"),
                    "fecha": peli["release_date"],
                    "popularidad": peli.get("popularity", 0),
                }
        if pagina >= data.get("total_pages", 1):
            break

    return resultados


def cargar_datos_previos() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_datos(datos: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=True)


def comparar(previos: dict, nuevos: dict) -> list[str]:
    cambios = []
    for tmdb_id, info in nuevos.items():
        sid = str(tmdb_id)
        if sid not in previos:
            cambios.append(f"🆕 Nueva: {info['titulo']} — {info['fecha']}")
        elif previos[sid]["fecha"] != info["fecha"]:
            cambios.append(
                f"🔄 Cambio de fecha: {info['titulo']} — "
                f"{previos[sid]['fecha']} → {info['fecha']}"
            )
    ids_nuevos = set(str(k) for k in nuevos.keys())
    for sid, info in previos.items():
        if sid not in ids_nuevos:
            cambios.append(f"❌ Ya no aparece: {info['titulo']} ({info['fecha']})")
    return cambios


def generar_ics(datos: dict) -> None:
    cal = Calendar()
    for tmdb_id, info in datos.items():
        try:
            fecha = datetime.strptime(info["fecha"], "%Y-%m-%d").date()
        except ValueError:
            continue
        ev = Event()
        ev.name = f"🎬 {info['titulo']}"
        ev.begin = fecha.isoformat()
        ev.make_all_day()
        ev.description = "Estreno en cines de México (fuente: TMDB)"
        ev.uid = f"tmdb-{tmdb_id}@estrenos-mx"
        cal.events.add(ev)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())


def main() -> None:
    api_key = get_api_key()
    session = requests.Session()
    session.headers.update(
        {"Authorization": f"Bearer {api_key}", "accept": "application/json"}
    )

    previos = cargar_datos_previos()
    nuevos = obtener_estrenos(session)

    cambios = comparar(previos, nuevos)

    # Formato final para guardar: claves como string (JSON no admite int como key)
    nuevos_str_keys = {str(k): v for k, v in nuevos.items()}
    guardar_datos(nuevos_str_keys)
    generar_ics(nuevos_str_keys)

    print(f"Total de estrenos en el calendario: {len(nuevos_str_keys)}")
    if cambios:
        print("\nCambios detectados:")
        for c in cambios:
            print(f"  {c}")
    else:
        print("Sin cambios respecto a la corrida anterior.")


if __name__ == "__main__":
    main()
