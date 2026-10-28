"""
SCRIPT PARA GUARDAR TUS COOKIES DE MERCADOLIBRE
Esto evita que seas detectado como bot.

INSTRUCCIONES:
1. Ejecuta: python scripts/setup_session.py
2. Se abrirá una ventana del navegador (NO headless)
3. Inicia sesión en MercadoLibre o simplemente navega
4. Las cookies se guardarán automáticamente en data/cookies.json
5. Todas las futuras extracciones usarán TUS cookies
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from services.cookies_manager import guardar_cookies

def setup_session():
    print("\n" + "="*70)
    print("🔐 CONFIGURAR SESIÓN MERCADOLIBRE")
    print("="*70)
    print("\n📋 INSTRUCCIONES:")
    print("1. Se abrirá una ventana del navegador (NO headless)")
    print("2. Inicia sesión en MercadoLibre o navega un poco")
    print("3. Presiona Enter aquí cuando hayas terminado")
    print("4. Las cookies se guardarán automáticamente")
    print("\n💡 Tip: Entre más navegues, más realista parecerá tu sesión\n")
    
    with sync_playwright() as p:
        # Abrimos navegador VISIBLE (headless=False)
        browser = p.chromium.launch(
            headless=False,  # Ventana visible
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900}
        )
        
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
        
        # Navegamos a MercadoLibre
        print("🌐 Abriendo MercadoLibre...\n")
        page.goto("https://www.mercadolibre.cl", wait_until="networkidle")
        
        # Esperamos a que el usuario termine
        input("⏸️  Presiona Enter cuando hayas terminado en el navegador...\n")
        
        # Guardamos las cookies
        guardar_cookies(page)
        
        browser.close()
        
        print("\n✅ ¡LISTO! Tus cookies se guardarán en todos los siguientes scrapes")
        print("🚀 Ahora MercadoLibre te reconocerá como usuario real")
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    setup_session()
