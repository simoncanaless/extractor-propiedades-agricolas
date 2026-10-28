"""Compara modelos de Groq contra las propiedades ya guardadas en la BD.

Usa la ubicación y la descripción guardadas de cada oferta como entrada y compara
superficie, precio y región que devuelve cada modelo contra los valores de la BD.

Uso:  python scripts/comparar_modelos.py openai/gpt-oss-120b qwen/qwen3.8-27b
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from db.database_manager import DatabaseManager
from services.ai_processor import AIProcessor
from services.processor import DataProcessor

modelos = sys.argv[1:] or [config.GROQ_MODEL]
ofertas = DatabaseManager().obtener_todas()


def cerca(a, b, tol=0.05):
    a, b = float(a or 0), float(b or 0)
    return abs(a - b) <= tol * max(abs(b), 1)


norm = DataProcessor.normalizar_region

for i, modelo in enumerate(modelos):
    if i > 0:
        time.sleep(60)  # el plan gratis de Groq permite 8.000 tokens/minuto por modelo
    config.GROQ_MODEL = modelo
    ia = AIProcessor("groq")
    aciertos = {"superficie": 0, "precio": 0, "region": 0}
    t0 = time.time()
    print(f"\n===== {modelo}")
    for o in ofertas:
        texto = f"Ubicación: {o[2]}. Contenido: {o[14]}"
        r = ia.analizar_descripcion(texto) or {}
        sup_ok = cerca(r.get("superficie_total_ha"), o[5])
        precio = r.get("precio_detectado_texto_uf") or 0
        pre_ok = cerca(precio, o[6])
        reg_ok = bool(r.get("region")) and norm(str(r["region"])) == norm(str(o[3]))
        aciertos["superficie"] += sup_ok
        aciertos["precio"] += pre_ok
        aciertos["region"] += reg_ok
        marca = lambda ok: "OK" if ok else "--"
        print(f"  [{o[4]:<12}] sup {marca(sup_ok)} {r.get('superficie_total_ha')} vs {o[5]} | "
              f"UF {marca(pre_ok)} {precio} vs {o[6]} | región {marca(reg_ok)} {r.get('region')!r}")
        print(f"      agua: {str(r.get('derechos_agua'))[:70]!r} | suelo: {str(r.get('tipologia_suelo'))[:50]!r}"
              f" | plant.: {r.get('hectareas_plantaciones')} ha {str(r.get('detalle_plantaciones'))[:40]!r}")
    n = len(ofertas)
    print(f"  → superficie {aciertos['superficie']}/{n}, precio {aciertos['precio']}/{n}, "
          f"región {aciertos['region']}/{n}, {time.time() - t0:.1f} s")
