"""⚠️ Borra la tabla 'ofertas' y la vuelve a crear vacía.

Uso:  python scripts/reset_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database_manager import DatabaseManager

# Conectamos a la base de datos
db = DatabaseManager()
conn = db.conectar()
cur = conn.cursor()

print("🗑️ Borrando la tabla antigua (si existe)...")
cur.execute("DROP TABLE IF EXISTS ofertas;")
conn.commit()

cur.close()
conn.close()

print("🏗️ Creando la tabla nueva con todas las columnas actualizadas...")
db.crear_tablas()

print("✅ ¡Listo! Base de datos reseteada a la versión final.")