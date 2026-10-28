#!/usr/bin/env python3
"""
Script de migración: Normaliza todas las regiones en la base de datos.
Convierte O'Higgins, VI Región, etc. a un formato único.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database_manager import DatabaseManager
from services.processor import DataProcessor

def normalizar_regiones_bd():
    db = DatabaseManager()
    conn = db.conectar()
    if not conn:
        print("❌ Error: No se pudo conectar a la BD")
        return
    
    cur = conn.cursor()
    
    # Obtener todas las regiones únicas
    cur.execute("SELECT DISTINCT region FROM ofertas WHERE region IS NOT NULL ORDER BY region;")
    regiones = cur.fetchall()
    
    print(f"\n📊 Se encontraron {len(regiones)} regiones únicas en la BD:\n")
    
    # Mostrar mapeo
    mapeo = {}
    for (region_actual,) in regiones:
        region_normalizada = DataProcessor.normalizar_region(region_actual)
        mapeo[region_actual] = region_normalizada
        if region_actual != region_normalizada:
            print(f"  ✏️  '{region_actual}' -> '{region_normalizada}'")
        else:
            print(f"  ✅ '{region_actual}' (sin cambios)")
    
    # Preguntar confirmación
    print(f"\n{'='*60}")
    cambios = sum(1 for k, v in mapeo.items() if k != v)
    print(f"\n🔄 Se realizarán {cambios} cambios de región.\n")
    
    confirmar = input("¿Deseas continuar? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Migración cancelada.")
        cur.close()
        conn.close()
        return
    
    # Ejecutar actualizaciones
    actualizadas = 0
    for region_original, region_nueva in mapeo.items():
        if region_original != region_nueva:
            try:
                cur.execute(
                    "UPDATE ofertas SET region = %s WHERE region = %s;",
                    (region_nueva, region_original)
                )
                actualizadas += cur.rowcount
                print(f"  ✅ Actualizado: '{region_original}' -> '{region_nueva}' ({cur.rowcount} registros)")
            except Exception as e:
                print(f"  ❌ Error al actualizar '{region_original}': {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Migración completada: {actualizadas} registros actualizados.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    normalizar_regiones_bd()
