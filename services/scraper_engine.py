from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import datetime
import os

from config import RESPALDOS_DIR
from services.cookies_manager import cargar_cookies, cookies_existen
from services.human_like import get_random_user_agent, human_delay

# ──────────────────────────────────────────────
# TIMEOUTS
# ──────────────────────────────────────────────
# Sólo el goto usa un timeout "estricto": si la URL no existe o
# la red no responde en este tiempo, es un error real de URL/red.
GOTO_TIMEOUT       = 120_000   # 2 min – detecta URL inválida o sin red

# Para esperar selectores damos margen amplio: páginas lentas,
# CDN con lag, renderizado JS pesado, etc.
SELECTOR_TIMEOUT   = 90_000    # 1.5 min por selector

def ejecutar_extractor(url, portal="portalinmobiliario"):
    ruta_carpeta = str(RESPALDOS_DIR)
    os.makedirs(ruta_carpeta, exist_ok=True)

    with sync_playwright() as p:
        # Intento RÁPIDO y sencillo: comportamiento como antes del bloqueo.
        browser = p.chromium.launch(headless=True)
        simple_context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        simple_page = simple_context.new_page()
        simple_page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")

        use_enhanced = False
        page = simple_page
        context = simple_context

        # Primer intento: rápido y con wait_until=domcontentloaded
        # Cargar cookies en el contexto simple si existen (mejor compatibilidad)
        if cookies_existen():
            cargar_cookies(simple_page)
            print("🍪 Cargando cookies en modo simple")

        try:
            simple_page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            # Si detecta título o h1, asumimos que la carga fue correcta y procedemos (modo simple)
            if simple_page.locator(".ui-pdp-title").count() > 0 or simple_page.locator("h1").count() > 0:
                print("🔎 Modo simple: carga rápida exitosa (comportamiento por defecto)")
            else:
                # No encontramos selectores; activamos modo mejorado
                simple_context.close()
                use_enhanced = True
        except Exception:
            # Error o bloqueo: cerramos simple y activamos mitigaciones
            try:
                simple_context.close()
            except:
                pass
            use_enhanced = True

        # Modo mejorado (solo si el simple falló) — menos frecuente, más robusto
        if use_enhanced:
            print("⚠️ Modo mejorado: aplicando mitigaciones anti-bot y sesión")
            context = browser.new_context(
                user_agent=get_random_user_agent(),
                extra_http_headers={
                    "Accept-Language": "es-CL,es;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                },
                viewport={"width": 1280, "height": 900}
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")

            # Cargar cookies si existen
            if cookies_existen():
                cargar_cookies(page)
                print("🍪 Usando tu sesión personal (anti-bot)")
            else:
                print("⚠️  Sin sesión personal. Ejecuta: python scripts/setup_session.py")

            try:
                page.goto(url, wait_until="networkidle", timeout=GOTO_TIMEOUT)
                human_delay(2, 4)
            except PlaywrightTimeoutError:
                print(f"❌ La página no respondió después de {GOTO_TIMEOUT // 1000}s — URL posiblemente inválida o sin conexión.")
                context.close(); browser.close()
                return {"error": "url_invalida", "url": url}

        # ──────────────────────────────────────────────
        # NAVEGACIÓN — único punto donde un error = URL mala
        # ──────────────────────────────────────────────
        try:
            print(f"Navegando a: {url} | Portal: {portal}...")
            page.goto(url, wait_until="networkidle", timeout=GOTO_TIMEOUT)
            human_delay(2, 4)  # Delay humano aleatorio
        except PlaywrightTimeoutError:
            print(f"❌ La página no respondió después de {GOTO_TIMEOUT // 1000}s — URL posiblemente inválida o sin conexión.")
            browser.close()
            return {"error": "url_invalida", "url": url}
        except Exception as e:
            err = str(e).encode("utf-8", errors="replace").decode("utf-8")
            print(f"❌ Error de navegación: {err}")
            browser.close()
            return {"error": "url_invalida", "url": url, "detalle": err}

        # ──────────────────────────────────────────────
        # EXTRACCIÓN — errores aquí NO cancelan; devuelven
        # lo que se pudo extraer para que el usuario reintente.
        # ──────────────────────────────────────────────
        precio_raw     = "0"
        ubicacion_full = "No detectada"
        superficie_raw = "0"
        desc_raw       = ""
        fecha_raw      = ""
        captura_full_page = True

        try:

            # ==========================================
            # 1. PORTAL INMOBILIARIO (MercadoLibre)
            # ==========================================
            if portal == "portalinmobiliario":
                # Validar que NO estamos en página de bloqueo
                if page.locator("text=/suspicious-traffic|account-verification/i").count() > 0:
                    print("⚠️ ADVERTENCIA: MercadoLibre bloqueó como bot. Intentando alternativas...")
                    human_delay(3, 8)  # Esperar más
                
                # Intentar esperar a los selectores principales con reintentos
                intento = 0
                mientras_intente = True
                while intento < 3 and mientras_intente:
                    try:
                        page.wait_for_selector(".ui-pdp-title", timeout=30_000)
                        mientras_intente = False
                    except:
                        intento += 1
                        if intento < 3:
                            print(f"⚠️ Intento {intento} fallido, esperando...")
                            human_delay(2, 5)
                            page.reload()
                
                human_delay(1, 3)

                precio_raw = (
                    page.locator(".ui-pdp-price__second-line .andes-money-amount")
                    .first.inner_text()
                    if page.locator(".ui-pdp-price__second-line").count() > 0
                    else "0"
                )
                
                ubicacion_full = (
                    page.locator(".ui-pdp-media__title").last.inner_text()
                    if page.locator(".ui-pdp-media__title").count() > 0
                    else "No detectada"
                )
                
                superficie_raw = (
                    page.locator("th:has-text('Superficie total') + td").first.inner_text()
                    if page.locator("th:has-text('Superficie total')").count() > 0
                    else "0"
                )
                
                # --- Descripción: múltiples intentos / fallbacks ---
                desc_raw = ""
                desc_selectors = [
                    ".ui-pdp-description__content",
                    "div[data-testid='item-description']",
                    ".item-description__text",
                    "section[itemprop='description']",
                    ".ui-pdp__description",
                    ".ui-pdp-attributes__content",
                ]

                for sel in desc_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            desc_raw = page.locator(sel).first.inner_text()[:5000]
                            break
                    except:
                        continue

                # Intentar expandir "Ver más" si existe y volver a leer
                if not desc_raw:
                    for btn_text in ["Ver más", "Mostrar más", "Leer más", "Ver más información"]:
                        try:
                            locator_btn = page.locator(f"text=/{btn_text}/i")
                            if locator_btn.count() > 0:
                                try:
                                    locator_btn.first.click()
                                    human_delay(0.5, 1.5)
                                except:
                                    pass
                        except:
                            pass

                    for sel in desc_selectors:
                        try:
                            if page.locator(sel).count() > 0:
                                desc_raw = page.locator(sel).first.inner_text()[:5000]
                                break
                        except:
                            continue

                # Intentar meta description
                if not desc_raw:
                    try:
                        meta = page.locator("meta[name='description']")
                        if meta.count() > 0:
                            cont = meta.first.get_attribute("content")
                            if cont:
                                desc_raw = cont[:5000]
                    except:
                        pass

                # Último recurso: tomar body (más ruidoso)
                if not desc_raw:
                    try:
                        desc_raw = page.locator("body").inner_text()[:5000]
                    except:
                        desc_raw = ""

                locator_fecha = page.locator("text=/Publicado hace/i")
                fecha_raw = locator_fecha.first.inner_text() if locator_fecha.count() > 0 else ""

                captura_full_page = False

            # ==========================================
            # 2. CONTACTOS PROPIEDADES
            # ==========================================
            elif portal == "contactospropiedades":
                page.wait_for_selector("h1", timeout=SELECTOR_TIMEOUT)
                human_delay(2, 5)

                ubicacion_full = page.locator("h1").first.inner_text()

                if page.locator(".price, .precio, .valor, .monto").count() > 0:
                    precio_raw = page.locator(".price, .precio, .valor, .monto").first.inner_text()

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                human_delay(0.5, 2)
                page.evaluate("window.scrollTo(0, 0)")
                human_delay(0.5, 1.5)

                desc_raw = page.locator("body").inner_text()[:5000]

            # ==========================================
            # 3. IPROPIEDADES AGRÍCOLAS
            # ==========================================
            elif portal == "ipropiedadesagricolas":
                page.wait_for_selector("h1", timeout=SELECTOR_TIMEOUT)
                human_delay(1.5, 4)

                ubicacion_full = page.locator("h1").first.inner_text()

                if page.locator(".price, .item-price").count() > 0:
                    precio_raw = page.locator(".price, .item-price").first.inner_text()

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                human_delay(0.5, 2)
                page.evaluate("window.scrollTo(0, 0)")
                human_delay(0.5, 1.5)

                desc_raw = page.locator("body").inner_text()[:4000]

            # ==========================================
            # 4. PORTAL GENÉRICO / DESCONOCIDO
            # ==========================================
            else:
                page.wait_for_selector("h1", timeout=SELECTOR_TIMEOUT)
                human_delay(1.5, 4)

                ubicacion_full = (
                    page.locator("h1").first.inner_text()
                    if page.locator("h1").count() > 0
                    else "No detectada"
                )

                for selector in [".price", ".precio", ".valor", ".monto", ".property-price"]:
                    if page.locator(selector).count() > 0:
                        precio_raw = page.locator(selector).first.inner_text()
                        break

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                human_delay(0.5, 2)
                page.evaluate("window.scrollTo(0, 0)")
                human_delay(0.5, 1.5)

                desc_raw = page.locator("body").inner_text()[:5000]

        except Exception as e:
            # La página cargó pero algo en la extracción falló.
            # Se continúa igual: se toma captura y se devuelven los campos
            # que se lograron extraer antes del error.
            err = str(e).encode("utf-8", errors="replace").decode("utf-8")
            print(f"⚠️ Error parcial en extracción (se devolverá lo extraído hasta ahora): {err}")

        # ──────────────────────────────────────────────
        # FIX ENCODING
        # ──────────────────────────────────────────────
        ubicacion_full = ubicacion_full.encode("utf-8", errors="replace").decode("utf-8")
        desc_raw       = desc_raw.encode("utf-8", errors="replace").decode("utf-8")
        precio_raw     = precio_raw.encode("utf-8", errors="replace").decode("utf-8")

        print(f"  ✅ Título detectado: '{ubicacion_full}'")
        print(f"  📅 Texto de fecha:   '{fecha_raw}'")
        print(f"  📄 Preview desc:     '{desc_raw[:100]}'")

        # ──────────────────────────────────────────────
        # CAPTURA DE PANTALLA
        # ──────────────────────────────────────────────
        timestamp   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_foto = f"captura_{portal}_{timestamp}.png"
        ruta_foto   = os.path.join(ruta_carpeta, nombre_foto)

        try:
            page.set_viewport_size({"width": 1280, "height": 900})
            page.screenshot(path=ruta_foto, full_page=captura_full_page)
        except Exception as e:
            err = str(e).encode("utf-8", errors="replace").decode("utf-8")
            print(f"⚠️ No se pudo tomar la captura: {err}")
            nombre_foto = None

        browser.close()

        return {
            "url":             url,
            "link_pantallazo": f"/static/respaldos/{nombre_foto}" if nombre_foto else None,
            "ubicacion":       ubicacion_full,
            "precio_uf":       precio_raw,
            "superficie":      superficie_raw,
            "descripcion":     desc_raw,
            "fecha_relativa":  fecha_raw,
        }