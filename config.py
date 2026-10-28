"""Configuración central del proyecto.

Los secretos (API key de Gemini, contraseña de PostgreSQL) se leen desde
un archivo .env en la raíz, que NO se sube a git. Ver .env.example.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- IA: proveedor activo ("groq" o "gemini") ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Groq (https://console.groq.com/keys)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Google Gemini (https://aistudio.google.com/apikey)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- Base de datos (PostgreSQL) ---
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "agricola_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# --- Servidor web ---
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

# --- Archivos generados en ejecución (ignorados por git) ---
# Las cookies quedan fuera de /static para que Flask no las publique.
COOKIES_FILE = BASE_DIR / "data" / "cookies.json"
RESPALDOS_DIR = BASE_DIR / "static" / "respaldos"
