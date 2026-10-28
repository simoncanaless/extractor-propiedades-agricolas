"""Verifica que la conexión a PostgreSQL funciona con los datos del .env.

Uso:  python scripts/probar_bd.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from config import DB_PARAMS

try:
    conn = psycopg2.connect(**DB_PARAMS)
    print('✅ OK', conn.dsn)
    conn.close()
except Exception as e:
    print('❌ ERROR', e)
