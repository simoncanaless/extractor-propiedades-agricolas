# Extractor de Propiedades Agrícolas

Panel web que recopila publicaciones de terrenos agrícolas desde portales inmobiliarios chilenos, usa IA para convertir el texto libre de cada aviso en datos estructurados y los guarda en una base de datos para compararlos como referencias de mercado.

Pensado para tasaciones agrícolas: en vez de copiar a mano superficie, precio, derechos de agua y plantaciones desde cada aviso, se pega la URL y el sistema arma la ficha.

## Qué hace

- **Extracción web** con Playwright desde Portal Inmobiliario, Contactos Propiedades e iPropiedades Agrícolas (y un modo genérico para otros sitios). Guarda una captura de pantalla de cada aviso como respaldo.
- **Estructuración con IA (Groq o Google Gemini, intercambiables desde `.env`):** a partir del texto del aviso obtiene comuna, región, superficie en hectáreas, precio (UF o CLP), plantaciones, derechos de agua, tipo de suelo y fecha de publicación, resolviendo contradicciones del texto (por ejemplo, superficies distintas en título y descripción).
- **Normalización:** convierte m² a hectáreas, CLP a UF con el valor del día ([mindicador.cl](https://mindicador.cl)) y unifica nombres de regiones ("VI Región", "O'Higgins", "Libertador B. O'Higgins" → `O'Higgins`).
- **Valorización:** permite marcar avisos como oferta con un % de descuento y restar el valor de las plantaciones (USD/ha) para obtener el **valor del suelo depurado** por hectárea.
- **Panel de resultados** con edición en línea, filtros y **exportación a CSV** compatible con Excel.

## Stack

Python 3.11 · Flask · Playwright · PostgreSQL (psycopg2) · Groq API / Google Gemini API · Bootstrap

## Estructura

```
├── app.py                  # Punto de entrada (servidor Flask)
├── config.py               # Configuración; lee secretos desde .env
├── api/
│   └── routes.py           # Endpoints del panel
├── services/
│   ├── scraper_engine.py   # Extracción con Playwright por portal
│   ├── ai_processor.py     # Prompt y llamada al LLM (Groq o Gemini)
│   ├── processor.py        # Limpieza de precios, superficies y regiones
│   ├── indicadores.py      # UF, dólar y fechas relativas ("hace 3 meses")
│   ├── cookies_manager.py  # Sesión persistente del navegador
│   └── human_like.py       # Pausas y user-agents para navegación realista
├── db/
│   └── database_manager.py # Esquema y consultas a PostgreSQL
├── scripts/                # Utilidades de mantención y diagnóstico
├── templates/              # Vistas HTML (Jinja2)
├── static/css/
└── docs/                   # Guía de configuración de sesión
```

## Instalación

Requisitos: Python 3.11+ y PostgreSQL.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
playwright install chromium
```

Crea la base de datos y configura las variables de entorno:

```bash
createdb agricola_db
copy .env.example .env          # y completa GROQ_API_KEY y DB_PASSWORD
python scripts/probar_bd.py     # verifica la conexión
python scripts/probar_llm.py    # prueba la IA con un aviso de ejemplo
```

## Uso

```bash
python app.py
```

Abre `http://127.0.0.1:5001`, pega la URL de un aviso y presiona extraer. Las propiedades guardadas se ven en `/resultados`.

Si un portal bloquea las solicitudes, guarda una sesión de navegador una vez con `python scripts/setup_session.py` (ver [docs/sesion_anti_bot.md](docs/sesion_anti_bot.md)).

### Scripts útiles

| Script | Para qué sirve |
|---|---|
| `scripts/extraer_url.py <url>` | Prueba el scraper con una URL, sin IA ni base de datos |
| `scripts/debug_scraper.py <url>` | Muestra qué selectores encuentra en la página (útil si el portal cambia su HTML) |
| `scripts/probar_llm.py [groq\|gemini] [--modelos]` | Prueba la IA con un aviso de ejemplo y lista los modelos disponibles |
| `scripts/comparar_modelos.py <modelo> ...` | Compara modelos de Groq contra las propiedades ya guardadas |
| `scripts/normalizar_regiones.py` | Unifica nombres de regiones ya guardados |
| `scripts/ver_ultima_oferta.py` | Muestra el último registro de la base |
| `scripts/reset_db.py` | ⚠️ Borra y recrea la tabla `ofertas` |

## Uso responsable

Proyecto de uso personal y académico. Extrae avisos de a uno, a solicitud del usuario y con pausas entre acciones; no está diseñado para descargas masivas. Antes de usarlo, revisa los términos de uso de cada portal.

## Autor

Simón Canales — Estudiante de Ingeniería Civil Informática.
