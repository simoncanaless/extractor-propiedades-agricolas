import psycopg2

from config import DB_PARAMS


class DatabaseManager:
    def __init__(self):
        self.config = dict(DB_PARAMS)

    def conectar(self):
        try:
            return psycopg2.connect(**self.config)
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return None

    def crear_tablas(self):
        conn = self.conectar()
        if not conn: return
        cur = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS ofertas (
            id SERIAL PRIMARY KEY,
            url_fuente TEXT UNIQUE,
            ubicacion TEXT,
            region VARCHAR(100),
            comuna VARCHAR(100),
            superficie_total_ha NUMERIC(12,2),
            valor_total_uf NUMERIC(15,2),
            fecha_publicacion DATE,
            tipo_referencia VARCHAR(100),
            tiene_plantaciones BOOLEAN DEFAULT FALSE,
            superficie_plantacion_ha NUMERIC(12,2),
            valor_estimado_plantacion NUMERIC(15,2),
            derechos_agua TEXT,
            tipologia_suelo TEXT,
            descripcion_breve TEXT,
            link_respaldo_pantallazo TEXT,
            detalle_plantaciones TEXT,      -- ¡COLUMNA NUEVA AGREGADA!
            cultivo_nombre VARCHAR(100),    -- ¡COLUMNA NUEVA AGREGADA!
            valor_usd_ha NUMERIC(15,2),     -- ¡COLUMNA NUEVA AGREGADA!
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            es_ofertable BOOLEAN DEFAULT FALSE,
            porcentaje_oferta NUMERIC(5,2) DEFAULT 15.0,
            valor_oferta_uf NUMERIC(15,2)
        );
        """
        try:
            cur.execute(query)
            conn.commit()
            print("✅ Estructura de Base de Datos lista en pgAdmin.")
        except Exception as e:
            print(f"❌ Error al crear tabla: {e}")
        finally:
            cur.close()
            conn.close()

    def obtener_todas(self):
        conn = self.conectar()
        if not conn: return []
        cur = conn.cursor()
        try:
            # Columnas explícitas: routes.py lee las filas por posición, así que
            # el orden debe ser fijo aunque la tabla tenga otro orden físico.
            cur.execute("""
                SELECT id, url_fuente, ubicacion, region, comuna,                     -- 0-4
                       superficie_total_ha, valor_total_uf, fecha_publicacion,        -- 5-7
                       tipo_referencia, tiene_plantaciones, superficie_plantacion_ha, -- 8-10
                       valor_estimado_plantacion, derechos_agua, tipologia_suelo,     -- 11-13
                       descripcion_breve, link_respaldo_pantallazo, fecha_registro,   -- 14-16
                       es_ofertable, porcentaje_oferta, valor_oferta_uf,              -- 17-19
                       detalle_plantaciones, cultivo_nombre, valor_usd_ha             -- 20-22
                FROM ofertas ORDER BY id DESC
            """)
            return cur.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener datos: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def eliminar_ofertas(self, ids):
        conn = self.conectar()
        if not conn: return False
        cur = conn.cursor()
        try:
            ids_enteros = [int(i) for i in ids]
            cur.execute("DELETE FROM ofertas WHERE id = ANY(%s)", (ids_enteros,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al eliminar: {e}")
            return False
        finally:
            cur.close()
            conn.close()

    def actualizar_ofertas_multiples(self, lista_datos):
        conn = self.conectar()
        if not conn: return False
        cur = conn.cursor()
        try:
            for d in lista_datos:
                cur.execute("""
                    UPDATE ofertas 
                    SET es_ofertable = %s, porcentaje_oferta = %s, valor_oferta_uf = %s 
                    WHERE id = %s
                """, (d['es_ofertable'], d['porcentaje'], d['valor_oferta'], d['id']))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar múltiples ofertas: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    
    def actualizar_datos_plantacion(self, id_oferta, tiene_plantaciones, hectareas, detalle, cultivo_nombre, valor_usd_ha):
        conn = self.conectar()
        if not conn: return False
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE ofertas 
                SET tiene_plantaciones = %s, 
                    superficie_plantacion_ha = %s, 
                    detalle_plantaciones = %s,
                    cultivo_nombre = %s,
                    valor_usd_ha = %s
                WHERE id = %s
            """, (tiene_plantaciones, hectareas, detalle, cultivo_nombre, valor_usd_ha, id_oferta))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar plantación: {e}")
            return False
        finally:
            cur.close()
            conn.close()
            
    def actualizar_propiedad_completa(self, id_oferta, comuna, region, superficie, v_total, tipo_ref, agua, suelo, desc):
        conn = self.conectar()
        if not conn: return False
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE ofertas 
                SET comuna = %s, region = %s, superficie_total_ha = %s, 
                    valor_total_uf = %s, tipo_referencia = %s, 
                    derechos_agua = %s, tipologia_suelo = %s, descripcion_breve = %s
                WHERE id = %s
            """, (comuna, region, superficie, v_total, tipo_ref, agua, suelo, desc, id_oferta))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar propiedad: {e}")
            return False
        finally:
            cur.close()
            conn.close()