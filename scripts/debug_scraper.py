"""Abre una URL y muestra qué selectores CSS del scraper encuentra. Útil cuando un portal cambia su HTML.

Uso:  python scripts/debug_scraper.py <url>
"""
from playwright.sync_api import sync_playwright
import sys
import time

if len(sys.argv) < 2:
    print("❌ Uso: python scripts/debug_scraper.py <url>")
    sys.exit(1)

url = sys.argv[1]
print(f"🔍 Analizando: {url}\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        extra_http_headers={
            "Accept-Language": "es-CL,es;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
    
    try:
        page.goto(url, wait_until="networkidle", timeout=120_000)
        print("✅ Página cargada (networkidle)\n")
        time.sleep(3)
        print("✅ Esperados 3 segundos\n")
        
        # Detectar si estamos en página de bloqueo
        if page.locator("text=/suspicious-traffic|account-verification/i").count() > 0:
            print("⚠️ ALERTA: MercadoLibre está bloqueando como bot\n")
        
        # Detectar portal
        html = page.content()
        
        print("=" * 60)
        print("BUSCANDO SELECTORES CLAVE:")
        print("=" * 60)
        
        # Selectores del DOM
        selectores = [
            (".ui-pdp-title", "MercadoLibre Title"),
            (".ui-pdp-price__second-line", "MercadoLibre Price"),
            (".andes-money-amount", "MercadoLibre Money Amount"),
            (".ui-pdp-media__title", "MercadoLibre Media Title"),
            ("th:has-text('Superficie total')", "Superficie"),
            (".ui-pdp-description__content", "Description"),
            ("text=/Publicado hace/i", "Fecha Publication"),
            ("h1", "Título genérico"),
            (".price", "Price genérico"),
            (".precio", "Precio (ES)"),
            (".valor", "Valor"),
            (".monto", "Monto"),
        ]
        
        for selector, desc in selectores:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    text = page.locator(selector).first.inner_text()[:100]
                    print(f"✅ [{selector}] ({desc})")
                    print(f"   Encontrados: {count}")
                    print(f"   Texto: {text}\n")
                else:
                    print(f"❌ [{selector}] ({desc}) — 0 elementos\n")
            except Exception as e:
                print(f"⚠️  [{selector}] ({desc}) — Error: {str(e)[:80]}\n")
        
        print("=" * 60)
        print("CONTENIDO HTML (primeros 2000 caracteres):")
        print("=" * 60)
        print(html[:2000])
        
    except Exception as e:
        print(f"❌ Error al cargar la página: {e}")
    finally:
        browser.close()
