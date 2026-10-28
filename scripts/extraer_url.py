"""Ejecuta el scraper sobre una sola URL e imprime el resultado (sin IA ni base de datos).

Uso:  python scripts/extraer_url.py <url> [portal]
      portal: portalinmobiliario (por defecto), contactospropiedades, ipropiedadesagricolas
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.scraper_engine import ejecutar_extractor

if len(sys.argv) < 2:
    sys.exit(__doc__)

url = sys.argv[1]
portal = sys.argv[2] if len(sys.argv) > 2 else "portalinmobiliario"

print("Ejecutando extractor para:\n", url)
res = ejecutar_extractor(url, portal=portal)
print(json.dumps(res, indent=2, ensure_ascii=False))
