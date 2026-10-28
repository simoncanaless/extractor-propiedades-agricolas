import json
import os

from config import COOKIES_FILE

def guardar_cookies(page):
    """Guarda las cookies de la página en archivo JSON"""
    cookies = page.context.cookies()
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
    with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)
    print(f"✅ Cookies guardadas en {COOKIES_FILE}")

def cargar_cookies(page):
    """Carga cookies guardadas en una nueva página"""
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
            page.context.add_cookies(cookies)
            print(f"✅ Cookies cargadas desde {COOKIES_FILE}")
            return True
    return False

def limpiar_cookies():
    """Borra el archivo de cookies"""
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        print(f"🗑️  Cookies eliminadas")

def cookies_existen():
    """Verifica si existen cookies guardadas"""
    return os.path.exists(COOKIES_FILE)
