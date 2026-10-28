# CLAUDE.md — Extractor de Propiedades Agrícolas

Guía para trabajar en este proyecto con Claude. Leer completo antes de cambiar código.

## Qué es

Panel web Flask para tasaciones agrícolas: el usuario pega la URL de un aviso de terreno,
Playwright extrae el texto y una captura, un LLM convierte el texto libre en datos
estructurados (superficie, precio, aguas, plantaciones, etc.) y todo se guarda en
PostgreSQL. En `/resultados` se editan, valorizan y exportan a CSV como referencias de mercado.

Autor: Simón Canales. Él diseña funcionalidades y prioridades; el código lo escribe la IA.
Explicar las decisiones técnicas en lenguaje simple y en español.

## Flujo principal (`POST /extraer` en `api/routes.py`)

1. Detecta el portal por la URL (`portalinmobiliario` / `mercadolibre`, `contactospropiedades`,
   `ipropiedadesagricolas`, si no `desconocido`).
2. `services/scraper_engine.ejecutar_extractor(url, portal)` → dict con `ubicacion`,
   `precio_uf` (texto crudo), `superficie`, `descripcion`, `fecha_relativa`, `link_pantallazo`.
3. `services/ai_processor.AIProcessor.analizar_descripcion(texto)` → dict JSON (ver contrato abajo).
4. `DataProcessor.normalizar_region`, cálculo de fecha y precio final (prioridad:
   precio del scraper > UF del LLM > CLP del LLM convertido con la UF del día).
5. `INSERT ... ON CONFLICT (url_fuente) DO NOTHING` en la tabla `ofertas`.

## Estructura

```
app.py                  Punto de entrada (crea tabla y levanta Flask en :5001)
config.py               ÚNICA fuente de configuración; lee .env
api/routes.py           Endpoints: /, /extraer, /resultados, /exportar, /guardar_ofertas_batch,
                        /actualizar_plantacion, /editar_propiedad_completa, /eliminar
services/
  scraper_engine.py     Playwright; un bloque por portal; modo simple → modo "mejorado"
  ai_processor.py       Prompt + llamada HTTP al LLM; devuelve dict o None
  processor.py          Limpieza de precios/superficies y mapa de regiones
  indicadores.py        UF y dólar (mindicador.cl, caché 12 h) y fechas relativas
  cookies_manager.py    Sesión persistente en data/cookies.json
  human_like.py         Pausas aleatorias y user-agents
db/database_manager.py  Esquema CREATE TABLE y consultas (psycopg2, sin ORM)
scripts/                Utilidades que se ejecutan con: python scripts/<nombre>.py
templates/              index.html (formulario) y resultados.html (panel, Bootstrap + JS)
docs/sesion_anti_bot.md Cómo guardar la sesión del navegador
```

## Cómo correr

```bash
.venv\Scripts\activate
python app.py                    # http://127.0.0.1:5001
python scripts/probar_bd.py      # verifica PostgreSQL
python scripts/probar_llm.py [groq|gemini] [--modelos]  # prueba el LLM con un aviso de ejemplo
python scripts/extraer_url.py <url> [portal]   # scraper solo, sin LLM ni BD
```

Entorno: Windows, Python 3.11, `.venv` dentro del proyecto, PostgreSQL local (`agricola_db`).
En la consola de Windows los `print` con emojis fallan si la salida se redirige:
usar `$env:PYTHONIOENCODING="utf-8"`.

## Reglas del proyecto

- **Secretos solo en `.env`** (ignorado por git). Nunca escribir API keys ni contraseñas en
  el código; leerlas desde `config.py`. Al agregar una variable nueva, agregarla también a
  `.env.example` con un valor de ejemplo.
- **Nada sensible en `static/`**: Flask publica esa carpeta. Cookies y diagnósticos van en
  `data/` (ignorado por git). Las capturas van en `static/respaldos/` (también ignorado),
  porque el panel las muestra por URL.
- **Orden de columnas:** `routes.py` lee las filas por posición (`o[17]`, `fila[19]`...).
  `DatabaseManager.obtener_todas()` hace un SELECT con columnas explícitas en ese orden.
  Si se agrega una columna, añadirla AL FINAL de ese SELECT y de `crear_tablas()`,
  nunca en medio, o se rompen `/resultados` y `/exportar`.
- **Scripts:** cada archivo en `scripts/` empieza agregando la raíz al `sys.path`
  (ver cualquier script existente). Mantener ese patrón.
- **Código y textos en español** (nombres de funciones, mensajes, comentarios), como el resto.
- **Repo público en GitHub:** antes de cada commit, revisar que no entren `.env`, `data/`,
  capturas ni URLs con datos personales.

## Contrato del LLM (`AIProcessor.analizar_descripcion`)

Recibe texto plano del aviso y debe devolver **un dict** con estas claves, o `None` si falla:

```json
{
  "comuna": "", "region": "", "superficie_total_ha": 0.0,
  "precio_detectado_texto_uf": 0.0, "precio_detectado_texto_clp": 0.0,
  "tiene_plantaciones": false, "hectareas_plantaciones": 0.0,
  "detalle_plantaciones": "", "derechos_agua": "", "tipologia_suelo": "",
  "fecha_publicacion": "", "tipo_referencia": ""
}
```

`routes.py` solo depende de este contrato, no del proveedor. Cualquier cambio de LLM debe
hacerse dentro de `services/ai_processor.py` (y `config.py` / `.env`) sin tocar las rutas.

## Proveedor del LLM

Decisión tomada: **Groq** es el proveedor principal; Gemini queda como alternativa.
Se elige con `LLM_PROVIDER=groq|gemini` en `.env`. El prompt es el mismo para ambos.

- **Groq:** `POST https://api.groq.com/openai/v1/chat/completions` (formato OpenAI),
  `Authorization: Bearer GROQ_API_KEY`, `response_format: {"type": "json_object"}`,
  `temperature 0.1`. Modelo por defecto `openai/gpt-oss-120b` (`GROQ_MODEL`).
  Es un servicio en la nube: necesita internet y API key. No corre local.
  Elección hecha el 28-10-2026 con `scripts/comparar_modelos.py` sobre los 6 avisos de la BD:
  gpt-oss-120b acertó 6/6 regiones y no inventó datos; qwen3.8-27b es más rápido pero
  respondió "Región del Maule" para Pichidegua (incorrecto) y su plan gratis permite solo
  1.000 tokens de salida por minuto; gpt-oss-20b quedó entre ambos. `llama-3.3-70b-versatile`
  ya no está disponible en la cuenta. Límites del plan gratis: 1.000 consultas/día y
  8.000 tokens/minuto por modelo, suficiente para extraer avisos de a uno.
- **Gemini:** REST `generativelanguage.googleapis.com` con `responseMimeType: application/json`.
  La key antigua dejó de ser válida (28-10-2026); solo sirve si se genera una nueva.

Para agregar otro proveedor: un método `_llamar_<nombre>(prompt)` en `AIProcessor` que
devuelva el texto crudo, y su rama en `analizar_descripcion`. La limpieza del JSON es común.
Si algún día se quiere correr local, Ollama expone la misma API que Groq
(`http://localhost:11434/v1`), así que bastaría parametrizar la URL de `_llamar_groq`.
El PC de desarrollo tiene una RTX 3060 Ti (8 GB), suficiente para modelos de ~8B.

Antes de dar por bueno un cambio de modelo: correr `scripts/probar_llm.py` y comparar
los campos que devuelve contra los 6 avisos ya guardados en la BD.

## Idea en evaluación: reverse-api-engineer (REA)

Repo: https://github.com/kalil0321/reverse-api-engineer. Graba el tráfico del navegador en
un sitio y, con un agente de código (Claude Code, Codex, Cursor), genera un cliente Python
tipado para las APIs internas que usa esa página.

Encaja en la parte del **scraper**, no reemplaza al LLM:
- Si un portal carga sus datos por JSON (probable en Portal Inmobiliario/MercadoLibre),
  precio, superficie y ubicación saldrían ya estructurados, sin selectores CSS frágiles
  ni el "modo mejorado" anti-bot.
- El LLM sigue haciendo falta para el texto libre: derechos de agua, plantaciones, suelo.
- Se usa en desarrollo, una vez por portal; el cliente generado vive en `services/` y se
  llama desde `scraper_engine.py` con fallback al scraping actual.
- Portales que arman el HTML en el servidor (posiblemente Contactos Propiedades) no tienen
  API que descubrir; ahí se mantiene Playwright.
- Llamar APIs internas no documentadas sigue sujeto a los términos de uso del sitio.

## Problemas conocidos (no corregidos aún)

- `scraper_engine.py` navega dos veces a la misma URL (una en el modo simple o mejorado y
  otra en el bloque "NAVEGACIÓN"), lo que duplica el tiempo de carga.
- Muchos `except:` vacíos ocultan errores, sobre todo en `indicadores.py` y en el scraper.
- `obtener_usd_actual()` no actualiza `ultima_actualizacion`, así que su caché depende de la UF.
- `scripts/ver_ultima_oferta.py` imprime región y comuna con los índices cruzados.
- No hay tests automáticos.
