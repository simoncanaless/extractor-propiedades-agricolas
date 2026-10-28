"""Prueba el proveedor de IA configurado (o el que indiques) con un aviso de ejemplo.

Uso:  python scripts/probar_llm.py            # usa LLM_PROVIDER del .env
      python scripts/probar_llm.py groq       # fuerza un proveedor
      python scripts/probar_llm.py groq --modelos   # además lista los modelos disponibles
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

import config
from services.ai_processor import AIProcessor

args = [a for a in sys.argv[1:] if not a.startswith("--")]
proveedor = args[0] if args else config.LLM_PROVIDER

if "--modelos" in sys.argv:
    print(f"📋 Modelos disponibles en {proveedor}:\n")
    if proveedor == "groq":
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"}, timeout=10).json()
        for m in sorted(x["id"] for x in r.get("data", [])):
            print(f"  - {m}")
    else:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={config.GEMINI_API_KEY}", timeout=10).json()
        for m in r.get("models", []):
            print(f"  - {m['name']}")
    if "error" in r:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    print()

texto = (
    "Ubicación: Pichidegua, VI Región. Contenido: Se vende campo de 19 hectáreas planas "
    "con 12 ha de paltos en producción. Derechos de agua de 28 lt/seg del canal. "
    "Suelo franco arcilloso. Precio 687 UF. Publicado hace 2 meses."
)
print(f"📡 Analizando aviso de ejemplo con {proveedor.upper()}...\n")
resultado = AIProcessor(proveedor).analizar_descripcion(texto)
print(json.dumps(resultado, indent=2, ensure_ascii=False) if resultado else "❌ Sin resultado")
