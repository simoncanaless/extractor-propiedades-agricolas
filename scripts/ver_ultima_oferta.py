"""Muestra la última oferta guardada en la base de datos.

Uso:  python scripts/ver_ultima_oferta.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database_manager import DatabaseManager

db = DatabaseManager()
ofertas = db.obtener_todas()

print(f"📊 Total ofertas en BD: {len(ofertas)}\n")

if ofertas:
    print("=" * 70)
    print("ÚLTIMA OFERTA EXTRAÍDA:")
    print("=" * 70)
    o = ofertas[-1]
    print(f"ID:           {o[0]}")
    print(f"URL:          {o[1]}")
    print(f"Ubicación:    {o[3]}")
    print(f"Región:       {o[4]}")
    print(f"Comuna:       {o[2]}")
    print(f"Superficie:   {o[5]} Ha")
    print(f"Precio UF:    {o[6]}")
    print(f"Fecha Pub:    {o[7]}")
    print(f"Tipo:         {o[8]}")
    print(f"Plantaciones: {o[9]}")
    print(f"Captura:      {o[16]}")
    print(f"Descripción:  {o[14][:100]}..." if o[14] else "Descripción: (vacía)")
else:
    print("❌ No hay ofertas en la BD")
