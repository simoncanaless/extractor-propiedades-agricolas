import re

class DataProcessor:
    @staticmethod
    def limpiar_numero(texto_numero, valor_uf_hoy=1.0):
        """
        Limpia los precios. En Chile, los precios grandes suelen usar punto para los miles 
        (ej: 216.160), por lo que aquí sí nos sirve extraer solo los dígitos puros.
        """
        if not texto_numero:
            return 0.0

        print(f"  🔍 Procesando precio: '{texto_numero}'")
        es_clp = '$' in texto_numero
        
        numero_str = re.sub(r'[^\d]', '', texto_numero)
        
        try:
            valor_numerico = float(numero_str)
        except Exception:
            print(f"  ⚠️ No se pudo extraer número de '{texto_numero}', usando 0.0")
            return 0.0

        if es_clp:
            uf_final = valor_numerico / valor_uf_hoy
            print(f"  ✅ Conversión: {valor_numerico} CLP -> {uf_final} UF (UF hoy: {valor_uf_hoy})")
            return uf_final
        else:
            return valor_numerico

    @staticmethod
    def limpiar_superficie_ha(texto_superficie):
        """
        Limpia el texto de superficie, respetando los decimales.
        Convierte de m² a Ha si es necesario (1 Ha = 10,000 m²).
        """
        if not texto_superficie:
            return 0.0

        print(f"  🔍 Procesando superficie: '{texto_superficie}'")
        
        # --- LA SOLUCIÓN ---
        # 1. Cambiamos comas por puntos por si el vendedor escribe "42,2" en vez de "42.2"
        texto_limpio = texto_superficie.replace(',', '.')
        
        # 2. Eliminamos letras y espacios, pero MANTENEMOS los dígitos (\d) y el punto (.)
        numero_str = re.sub(r'[^\d.]', '', texto_limpio)
        
        try:
            superficie_final = float(numero_str)
        except Exception:
            print(f"  ⚠️ No se pudo extraer número de '{texto_superficie}', usando 0.0")
            return 0.0

        # Detectar la unidad y convertir a Hectáreas si es m²
        unidad_texto = texto_superficie.lower()
        
        if 'm²' in unidad_texto or 'm2' in unidad_texto:
            superficie_convertida = superficie_final / 10000.0
            print(f"  ✅ Conversión: {superficie_final} m² -> {superficie_convertida} Ha")
            return superficie_convertida
        
        return superficie_final

    @staticmethod
    def normalizar_region(region_texto):
        """
        Normaliza variantes de nombres de regiones chilenas.
        Convierte "O'Higgins", "VI Región", "VI región", etc. a un nombre estándar único.
        """
        if not region_texto:
            return region_texto
        
        # Diccionario de mapeo: cualquier variante -> nombre estándar
        mapeo_regiones = {
            # Región I - Arica y Parinacota
            "arica": "Arica y Parinacota",
            "arica y parinacota": "Arica y Parinacota",
            "región arica": "Arica y Parinacota",
            "i región": "Arica y Parinacota",
            "1 región": "Arica y Parinacota",
            
            # Región II - Tarapacá
            "tarapacá": "Tarapacá",
            "tarapaca": "Tarapacá",
            "región tarapacá": "Tarapacá",
            "ii región": "Tarapacá",
            "2 región": "Tarapacá",
            
            # Región III - Atacama
            "atacama": "Atacama",
            "región atacama": "Atacama",
            "iii región": "Atacama",
            "3 región": "Atacama",
            
            # Región IV - Coquimbo
            "coquimbo": "Coquimbo",
            "región coquimbo": "Coquimbo",
            "iv región": "Coquimbo",
            "4 región": "Coquimbo",
            
            # Región V - Valparaíso
            "valparaíso": "Valparaíso",
            "valparaiso": "Valparaíso",
            "región valparaíso": "Valparaíso",
            "v región": "Valparaíso",
            "5 región": "Valparaíso",
            
            # Región VI - O'Higgins (LA MÁS IMPORTANTE PARA TI)
            "o'higgins": "O'Higgins",
            "ohiggins": "O'Higgins",
            "o higgins": "O'Higgins",
            "región o'higgins": "O'Higgins",
            "región del libertador general bernardo o'higgins": "O'Higgins",
            "libertador general bernardo o'higgins": "O'Higgins",
            "vi región": "O'Higgins",
            "6 región": "O'Higgins",
            "sexta región": "O'Higgins",
            
            # Región VII - Maule
            "maule": "Maule",
            "región maule": "Maule",
            "vii región": "Maule",
            "7 región": "Maule",
            "séptima región": "Maule",
            
            # Región VIII - Bío Bío
            "bío bío": "Bío Bío",
            "bio bio": "Bío Bío",
            "bío-bío": "Bío Bío",
            "región bío bío": "Bío Bío",
            "viii región": "Bío Bío",
            "8 región": "Bío Bío",
            "octava región": "Bío Bío",
            
            # Región IX - La Araucanía
            "araucanía": "La Araucanía",
            "araucania": "La Araucanía",
            "la araucanía": "La Araucanía",
            "región araucanía": "La Araucanía",
            "ix región": "La Araucanía",
            "9 región": "La Araucanía",
            "novena región": "La Araucanía",
            
            # Región X - Los Lagos
            "los lagos": "Los Lagos",
            "región los lagos": "Los Lagos",
            "x región": "Los Lagos",
            "10 región": "Los Lagos",
            "décima región": "Los Lagos",
            
            # Región XI - Aysén
            "aysén": "Aysén",
            "aysen": "Aysén",
            "región aysén": "Aysén",
            "xi región": "Aysén",
            "11 región": "Aysén",
            "undécima región": "Aysén",
            
            # Región XII - Magallanes
            "magallanes": "Magallanes",
            "región magallanes": "Magallanes",
            "magallanes y de la antártica chilena": "Magallanes",
            "xii región": "Magallanes",
            "12 región": "Magallanes",
            "duodécima región": "Magallanes",
            
            # Región XIII - Metropolitana (RM)
            "metropolitana": "Metropolitana",
            "región metropolitana": "Metropolitana",
            "rm": "Metropolitana",
            "región metropolitana de santiago": "Metropolitana",
            "xiii región": "Metropolitana",
            
            # Región XIV - Los Ríos (nueva, antes era parte de Los Lagos)
            "los ríos": "Los Ríos",
            "los rios": "Los Ríos",
            "región los ríos": "Los Ríos",
            "xiv región": "Los Ríos",
            "14 región": "Los Ríos",
            
            # Región XV - Ñuble (nueva, antes era parte del Bío Bío)
            "ñuble": "Ñuble",
            "nuble": "Ñuble",
            "región ñuble": "Ñuble",
            "xv región": "Ñuble",
            "15 región": "Ñuble",
        }
        
        # Minúsculas y apóstrofo curvo (’) -> recto
        region_limpia = region_texto.lower().strip().replace("’", "'")

        resultado = mapeo_regiones.get(region_limpia)

        # Segundo intento: comparar sin tildes ("vi region" == "vi región")
        if resultado is None:
            sin_tildes = DataProcessor._sin_tildes(region_limpia)
            for clave, valor in mapeo_regiones.items():
                if DataProcessor._sin_tildes(clave) == sin_tildes:
                    resultado = valor
                    break

        # Tercer intento: nombres largos o abreviados ("Libertador B. O'Higgins",
        # "VI Región del Libertador General Bernardo O'Higgins")
        if resultado is None:
            sin_tildes = DataProcessor._sin_tildes(region_limpia)
            for palabra, valor in DataProcessor.PALABRAS_CLAVE_REGION:
                if palabra in sin_tildes:
                    resultado = valor
                    break

        if resultado is None:
            return region_texto
        if resultado != region_texto:  # Solo imprimir si hay cambio
            print(f"  🔄 Normalización de región: '{region_texto}' -> '{resultado}'")
        return resultado

    # Palabras que identifican una región sin ambigüedad (texto sin tildes, en minúsculas).
    # Se usan solo si falla la búsqueda exacta; gana la primera que aparezca en la lista.
    PALABRAS_CLAVE_REGION = [
        ("higgins", "O'Higgins"),
        ("arica", "Arica y Parinacota"),
        ("tarapaca", "Tarapacá"),
        ("antofagasta", "Antofagasta"),
        ("atacama", "Atacama"),
        ("coquimbo", "Coquimbo"),
        ("valparaiso", "Valparaíso"),
        ("metropolitana", "Metropolitana"),
        ("maule", "Maule"),
        ("nuble", "Ñuble"),
        ("bio bio", "Bío Bío"),
        ("biobio", "Bío Bío"),
        ("bio-bio", "Bío Bío"),
        ("araucania", "La Araucanía"),
        ("los rios", "Los Ríos"),
        ("los lagos", "Los Lagos"),
        ("aysen", "Aysén"),
        ("magallanes", "Magallanes"),
    ]

    @staticmethod
    def _sin_tildes(texto):
        import unicodedata
        return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")