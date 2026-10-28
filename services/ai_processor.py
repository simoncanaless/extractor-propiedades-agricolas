"""Convierte el texto de un aviso en datos estructurados usando un LLM.

Proveedores soportados (se elige con LLM_PROVIDER en .env):
  - groq:   API compatible con OpenAI en https://api.groq.com/openai/v1
  - gemini: API REST de Google AI Studio
"""
import json

import requests

import config

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


class AIProcessor:
    def __init__(self, proveedor=None):
        self.proveedor = (proveedor or config.LLM_PROVIDER).lower()
        if self.proveedor not in ("groq", "gemini"):
            raise ValueError(f"LLM_PROVIDER desconocido: '{self.proveedor}' (usa 'groq' o 'gemini')")

    def analizar_descripcion(self, texto_completo):
        # --- TU FIX ENCODING: Limpiamos caracteres especiales ---
        texto_completo = texto_completo.encode('utf-8', errors='replace').decode('utf-8')

        prompt = f"""
        ERES UN ANALISTA DE INTELIGENCIA DE MERCADO AGRÍCOLA EXPERTO EN CHILE.
        
        MISION: Limpiar texto web bruto, ignorar el ruido y extraer data técnica en JSON puro.
        
        INSTRUCCIONES DE LECTURA (REGLAS ESTRICTAS):
        1. UBICACIÓN: Determina 'comuna' y 'region' de Chile.
        2. SUPERFICIE (ANTI-CONTRADICCIONES): Extrae la superficie total en Hectáreas (Ha). Si el texto tiene contradicciones (ej: el título dice 3.0 y abajo dice 3.5), PRIORIZA EL NÚMERO MAYOR que se refiera al terreno total. Si dice "m2", divídelo por 10.000. Guárdalo como número.
        3. PRECIO (RESCATE FINANCIERO): Busca el valor de venta. 
           - En UF: extrae el número en 'precio_detectado_texto_uf'.
           - En Pesos (CLP): extrae el número sin puntos en 'precio_detectado_texto_clp'.
           - Si no hay precio, usa 0.0. NO CONVIERTAS MONEDAS.
        4. PLANTACIONES: 
           - "tiene_plantaciones": true SOLO si ya tiene árboles cultivados. "Apto para" es false.
           - "hectareas_plantaciones": Suma de Ha plantadas (0.0 si no hay).
           - "detalle_plantaciones": Enumera especies y características.
        5. AGUAS Y SUELO: Extrae rigurosamente si menciona acciones, pozos, o tipo de tierra.
        6. FECHA (IMPORTANTE): Si el texto menciona cuándo se publicó o actualizó (ej: "marzo 2026", "hace 2 días"), extráelo en 'fecha_publicacion'. Si no dice nada, pon "".
        7. TIPO: 'Agrícola', 'Forestal', o 'Parcelación'.

        TEXTO BRUTO A ANALIZAR:
        -------------------------------------------
        {texto_completo}
        -------------------------------------------

        RESPONDE EXCLUSIVAMENTE CON ESTE FORMATO JSON PURO:
        {{
            "comuna": "Nombre",
            "region": "Nombre",
            "superficie_total_ha": 0.0,
            "precio_detectado_texto_uf": 0.0,
            "precio_detectado_texto_clp": 0.0,
            "tiene_plantaciones": true,
            "hectareas_plantaciones": 0.0,
            "detalle_plantaciones": "Especies",
            "derechos_agua": "Resumen",
            "tipologia_suelo": "Relieve/Calidad",
            "fecha_publicacion": "",
            "tipo_referencia": "Clasificación"
        }}
        """
        
        nombre = self.proveedor.upper()
        try:
            if self.proveedor == "groq":
                texto_ia = self._llamar_groq(prompt)
            else:
                texto_ia = self._llamar_gemini(prompt)
        except requests.exceptions.Timeout:
            print(f"\n❌ ERROR: {nombre} se demoró demasiado en responder (Timeout).\n")
            return None
        except Exception as e:
            print(f"❌ Error en IA ({nombre}): {str(e).encode('utf-8', errors='replace').decode('utf-8')}")
            return None

        if not texto_ia:
            return None

        texto_ia = self._quitar_markdown(texto_ia)
        try:
            return json.loads(texto_ia)
        except json.JSONDecodeError:
            print(f"\n❌ {nombre} NO DEVOLVIÓ UN JSON VÁLIDO. Texto recibido:\n{texto_ia}\n")
            return None

    # ── Proveedores ─────────────────────────────────────────────

    def _llamar_groq(self, prompt):
        if not config.GROQ_API_KEY:
            print("❌ Falta GROQ_API_KEY en el archivo .env")
            return None
        payload = {
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=90)
        datos = response.json()

        if 'error' in datos:
            print(f"\n❌ ERROR DE GROQ API ({response.status_code}): {datos['error'].get('message')}\n")
            return None
        try:
            return datos['choices'][0]['message']['content']
        except (KeyError, IndexError):
            print(f"⚠️ Groq respondió sin choices: {str(datos)[:300]}")
            return None

    def _llamar_gemini(self, prompt):
        if not config.GEMINI_API_KEY:
            print("❌ Falta GEMINI_API_KEY en el archivo .env")
            return None
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        }
        url = GEMINI_URL.format(model=config.GEMINI_MODEL, key=config.GEMINI_API_KEY)
        datos = requests.post(url, json=payload, timeout=90).json()

        if 'error' in datos:
            print(f"\n❌ ERROR DE GOOGLE API: {datos['error']['message']}\n")
            return None
        if datos.get('candidates'):
            candidato = datos['candidates'][0]
            # Filtros de seguridad de Gemini
            if 'content' not in candidato:
                print(f"\n❌ GEMINI CENSURÓ LA RESPUESTA (Safety): {candidato}\n")
                return None
            return candidato['content']['parts'][0]['text']
        print(f"⚠️ Gemini respondió sin candidates: {str(datos)[:300]}")
        return None

    @staticmethod
    def _quitar_markdown(texto):
        """Algunos modelos envuelven el JSON en ```json ... ```; se quita."""
        texto = texto.strip()
        comillas = "`" * 3
        if texto.startswith(comillas + "json"): texto = texto[7:]
        elif texto.startswith(comillas): texto = texto[3:]
        if texto.endswith(comillas): texto = texto[:-3]
        return texto.strip()