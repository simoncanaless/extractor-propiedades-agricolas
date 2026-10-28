import random
import time

# User-Agents reales (rotamos entre ellos)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def get_random_user_agent():
    """Devuelve un User-Agent aleatorio"""
    return random.choice(USER_AGENTS)

def human_delay(min_seconds=1, max_seconds=4):
    """
    Espera un tiempo aleatorio para simular comportamiento humano.
    min_seconds: mínimo de segundos a esperar
    max_seconds: máximo de segundos a esperar
    """
    wait_time = random.uniform(min_seconds, max_seconds)
    time.sleep(wait_time)

def scroll_human_like(page):
    """
    Simula scroll humano (aleatorio, con pausas)
    """
    # Scroll lento al fondo
    page.evaluate("window.scrollBy(0, window.innerHeight)")
    human_delay(0.5, 1.5)
    
    page.evaluate("window.scrollBy(0, window.innerHeight)")
    human_delay(0.5, 1.5)
    
    # Volver arriba
    page.evaluate("window.scrollTo(0, 0)")
    human_delay(0.5, 1)

def random_mouse_movement(page):
    """
    Simula movimiento del ratón (más realista que sin movimiento)
    """
    page.mouse.move(random.randint(100, 1200), random.randint(100, 700))
    human_delay(0.1, 0.5)
