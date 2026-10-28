"""Indicadores económicos (UF y dólar desde mindicador.cl) y cálculo de fechas
de publicación a partir de textos como "hace 3 meses"."""
import re
import time
from datetime import date

import requests
from dateutil.relativedelta import relativedelta

# Los valores se cachean 12 horas para no consultar la API en cada request
api_cache = {'uf': None, 'usd': None, 'ultima_actualizacion': 0}
TIEMPO_CACHE_SEGUNDOS = 43200


def obtener_uf_actual():
    if api_cache['uf'] and (time.time() - api_cache['ultima_actualizacion'] < TIEMPO_CACHE_SEGUNDOS): return api_cache['uf']
    try:
        data = requests.get("https://mindicador.cl/api/uf", headers={'User-Agent': 'Mozilla'}, timeout=10).json()
        api_cache['uf'] = float(data['serie'][0]['valor']); api_cache['ultima_actualizacion'] = time.time(); return api_cache['uf']
    except: return api_cache['uf'] if api_cache['uf'] else 38000.0


def obtener_usd_actual():
    if api_cache['usd'] and (time.time() - api_cache['ultima_actualizacion'] < TIEMPO_CACHE_SEGUNDOS): return api_cache['usd']
    try:
        data = requests.get("https://mindicador.cl/api/dolar", headers={'User-Agent': 'Mozilla'}, timeout=10).json()
        api_cache['usd'] = float(data['serie'][0]['valor']); return api_cache['usd']
    except: return api_cache['usd'] if api_cache['usd'] else 950.0


def extraer_y_calcular_fecha(texto):
    """Convierte "hoy", "ayer" o "hace N días/meses/años" al primer día del mes correspondiente."""
    if not texto: return None
    hoy = date.today()
    texto_limpio = str(texto).lower()
    if "ayer" in texto_limpio: return date((hoy - relativedelta(days=1)).year, (hoy - relativedelta(days=1)).month, 1)
    if "hoy" in texto_limpio: return date(hoy.year, hoy.month, 1)
    match = re.search(r"hace\s+(\d+)\s+(día|dias|días|mes|meses|año|años)", texto_limpio)
    if match:
        try:
            valor, unidad = int(match.group(1)), match.group(2)
            if unidad in ["año", "años"]: fc = hoy - relativedelta(years=valor)
            elif unidad in ["mes", "meses"]: fc = hoy - relativedelta(months=valor)
            elif unidad in ["día", "dias", "días"]: fc = hoy - relativedelta(days=valor)
            else: return None
            return date(fc.year, fc.month, 1)
        except: return None
    return None
