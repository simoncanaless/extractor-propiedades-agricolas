# 🔐 Sistema Anti-Bot con Sesión Personal

Este proyecto ahora incluye un sistema avanzado para evitar que MercadoLibre lo detecte como bot.

## 🚀 Cómo Usar

### 1️⃣ PRIMERA VEZ: Guardar tu sesión de MercadoLibre

```bash
python scripts/setup_session.py
```

**Esto hará:**
- Abrirá una ventana del navegador (NO headless - visible)
- Te llevará a MercadoLibre
- Puedes iniciar sesión o simplemente navegar por la página
- Tus cookies se guardarán automáticamente en `data/cookies.json`

**Tip:** Entre más tiempo estés en el navegador navegando, más realista parecerá tu perfil.

### 2️⃣ USAR LA APLICACIÓN NORMALMENTE

```bash
python app.py
```

Ahora todas las extracciones usarán:
- ✅ **Tu sesión personal** (cookies guardadas)
- ✅ **User-Agents rotativos** (parece diferente cada vez)
- ✅ **Delays humanoides** (no hace clic todos los 200ms como un bot)
- ✅ **Headers realistas** (aceptar idiomas, conexión, etc.)

## 🛡️ Beneficios

| Problema | Solución |
|----------|----------|
| MercadoLibre te detecta como bot | Tu sesión personal + cookies |
| Siempre pareces el mismo navegador | User-Agents rotativos |
| Clickeos demasiado rápidos | Delays aleatorios 1-4 segundos |
| Headers sospechosos | Headers HTTP reales |

## 📝 Archivos Creados

- `scripts/setup_session.py` - Script para guardar tu sesión
- `services/cookies_manager.py` - Gestor de cookies persistentes
- `services/human_like.py` - Delay aleatorio, User-Agents, scroll humano
- `data/cookies.json` - Tu sesión guardada (⚠️ NO subir a GitHub)

## 🔄 Renovar Sesión

Si MercadoLibre de repente vuelve a bloquearte, ejecuta nuevamente:

```bash
python scripts/setup_session.py
```

Esto sobrescribirá las cookies antiguas.

## ⚡ Opcional: Limpiar Cookies

```python
from services.cookies_manager import limpiar_cookies
limpiar_cookies()
```

## 📊 Cómo Verifica que Funciona

El servidor mostrará:
```
🍪 Usando tu sesión personal (anti-bot)
```

Si NO ves este mensaje, necesitas ejecutar `python scripts/setup_session.py` primero.

---

**¿Aún tienes problemas?** Intenta:
1. Ejecutar `setup_session.py` nuevamente
2. Esperar más tiempo en el navegador (10+ segundos)
3. Navegar a diferentes apartados de MercadoLibre antes de cerrar
