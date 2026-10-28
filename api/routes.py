from flask import Blueprint, render_template, request, Response, jsonify
import csv
import traceback
from io import StringIO
from decimal import Decimal
from datetime import date

from db.database_manager import DatabaseManager
from services.scraper_engine import ejecutar_extractor
from services.processor import DataProcessor
from services.ai_processor import AIProcessor
from services.indicadores import obtener_uf_actual, obtener_usd_actual, extraer_y_calcular_fecha

db = DatabaseManager()
ia_engine = AIProcessor()  # proveedor según LLM_PROVIDER en .env
main_bp = Blueprint('main', __name__)

def safe_texto(valor, default='No especificado'):
    if valor is None:
        return default
    texto = str(valor).strip()
    return texto if texto else default


@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/extraer', methods=['POST'])
def procesar():
    try:
        data = request.get_json() if request.is_json else request.form
        url_objetivo = data.get('url_busqueda')
        if not url_objetivo: return jsonify({"success": False, "message": "❌ Error: No se proporcionó una URL."}), 400

        portal_origen = "desconocido"
        url_lower = url_objetivo.lower()
        if "portalinmobiliario" in url_lower or "mercadolibre" in url_lower: portal_origen = "portalinmobiliario"
        elif "contactospropiedades" in url_lower: portal_origen = "contactospropiedades"
        elif "ipropiedadesagricolas" in url_lower: portal_origen = "ipropiedadesagricolas"

        resultado_web = ejecutar_extractor(url_objetivo, portal_origen)
        if not resultado_web: return jsonify({"success": False, "message": f"❌ Error: El Scraper no pudo leer la página de {portal_origen}."}), 500

        texto_para_ia = f"Ubicación: {resultado_web['ubicacion']}. Contenido: {resultado_web['descripcion']}"
        texto_para_ia = texto_para_ia.encode('utf-8', errors='replace').decode('utf-8')

        datos_ia = ia_engine.analizar_descripcion(texto_para_ia)
        if not datos_ia:
            return jsonify({"success": False, "message": f"❌ Error: Gemini no procesó el texto."}), 500

        # 🔄 Normalizar región para evitar duplicados (O'Higgins, VI Región, etc.)
        if 'region' in datos_ia and datos_ia['region']:
            datos_ia['region'] = DataProcessor.normalizar_region(datos_ia['region'])

        texto_fecha = resultado_web.get('fecha_relativa', '') or datos_ia.get('fecha_publicacion', '')
        fecha_final_db = extraer_y_calcular_fecha(texto_fecha)
        if not fecha_final_db: fecha_final_db = date.today()

        def safe_float(val):
            try: return float(str(val).replace(',', '.').replace('UF', '').replace('Ha', '').strip())
            except: return 0.0

        uf_hoy = obtener_uf_actual()
        precio_scraper = DataProcessor.limpiar_numero(resultado_web['precio_uf'], uf_hoy)
        precio_ia_uf = safe_float(datos_ia.get('precio_detectado_texto_uf', 0))
        precio_ia_clp = safe_float(datos_ia.get('precio_detectado_texto_clp', 0))
        
        if precio_scraper > 0: precio_final_uf = precio_scraper
        elif precio_ia_uf > 0: precio_final_uf = precio_ia_uf
        elif precio_ia_clp > 0 and uf_hoy > 0: precio_final_uf = precio_ia_clp / uf_hoy
        else: precio_final_uf = 0.0

        superficie_ia = safe_float(datos_ia.get('superficie_total_ha', 0))
        superficie_scraper = DataProcessor.limpiar_superficie_ha(resultado_web['superficie'])
        superficie_final_ha = superficie_ia if superficie_ia > 0 else superficie_scraper

        conn = db.conectar(); cur = conn.cursor()
        query = """
            INSERT INTO ofertas 
            (url_fuente, ubicacion, region, comuna, superficie_total_ha, valor_total_uf, 
             fecha_publicacion, tipo_referencia, tiene_plantaciones, superficie_plantacion_ha, 
             valor_estimado_plantacion, derechos_agua, tipologia_suelo, descripcion_breve, link_respaldo_pantallazo, detalle_plantaciones) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url_fuente) DO NOTHING;
        """
        valores = (
            url_objetivo,
            safe_texto(resultado_web.get('ubicacion', 'No especificado'))[:200],
            safe_texto(datos_ia.get('region', 'No especificado'))[:100],
            safe_texto(datos_ia.get('comuna', 'No especificado'))[:100],
            superficie_final_ha,
            precio_final_uf,
            fecha_final_db,
            safe_texto(datos_ia.get('tipo_referencia', 'Agrícola'))[:50],
            bool(datos_ia.get('tiene_plantaciones', False)),
            safe_float(datos_ia.get('hectareas_plantaciones', 0)),
            0.0,
            safe_texto(datos_ia.get('derechos_agua', 'No hay datos'))[:250],
            safe_texto(datos_ia.get('tipologia_suelo', 'No hay datos'))[:250],
            safe_texto(resultado_web.get('descripcion', 'No hay datos'))[:400],
            safe_texto(resultado_web.get('link_pantallazo', '')),
            safe_texto(datos_ia.get('detalle_plantaciones', 'No hay datos'))[:250]
        )
        cur.execute(query, valores); conn.commit(); cur.close(); conn.close()

        return jsonify({"success": True, "message": "✅ Propiedad extraída con éxito."})

    except Exception as e:
        error_detallado = traceback.format_exc()
        print("\n" + "="*50)
        print("❌ ERROR CRÍTICO ATRAPADO EN /extraer:")
        print(error_detallado)
        print("="*50 + "\n")
        return jsonify({"success": False, "message": f"Error interno."}), 500

@main_bp.route('/resultados')
def ver_resultados():
    ofertas_raw = db.obtener_todas()
    valor_uf = Decimal(str(obtener_uf_actual()))
    valor_usd = Decimal(str(obtener_usd_actual()))
    ofertas_procesadas = []
    
    for o in ofertas_raw:
        es_ofertable = o[17] if len(o) > 17 and o[17] is not None else False
        porc_oferta = o[18] if len(o) > 18 and o[18] is not None else Decimal('15.0')
        valor_oferta_manual = o[19] if len(o) > 19 and o[19] is not None else None
        
        v_total = o[6] if o[6] else Decimal('0')
        superficie = Decimal(str(o[5])) if (o[5] and o[5] > 0) else Decimal('1')
        
        if es_ofertable:
            if valor_oferta_manual is not None and valor_oferta_manual > 0: v_ajustado = valor_oferta_manual
            else: v_ajustado = v_total * (Decimal('1') - (Decimal(str(porc_oferta)) / Decimal('100')))
        else: v_ajustado = v_total
            
        u_hectarea = v_total / superficie 
        fecha_db = o[7]
        
        tiene_plantas = o[9]
        ha_plantas = Decimal(str(o[10])) if o[10] else Decimal('0')
        detalle_plantas = o[20] if len(o) > 20 and o[20] else 'No hay datos'
        cultivo_nombre = o[21] if len(o) > 21 and o[21] else 'No valorizado'
        valor_usd_ha = Decimal(str(o[22])) if len(o) > 22 and o[22] else Decimal('0')
        
        valor_plantacion_usd = ha_plantas * valor_usd_ha
        valor_plantacion_uf = (valor_plantacion_usd * valor_usd) / valor_uf if valor_uf > 0 else Decimal('0')
        valor_depurado_total = v_ajustado - valor_plantacion_uf
        valor_depurado_ha = valor_depurado_total / superficie

        ofertas_procesadas.append({
            'id': o[0], 'url': o[1], 'ubicacion': safe_texto(o[2], 'No especificado'), 'region': safe_texto(o[3], 'No especificado'), 'comuna': safe_texto(o[4], 'No especificado'),
            'superficie': o[5], 'v_total': v_total, 'tipo_ref': safe_texto(o[8], 'Agrícola'), 
            'tiene_plantas': tiene_plantas, 'ha_plantas': float(ha_plantas),
            'detalle_plantas': detalle_plantas, 'cultivo_nombre': cultivo_nombre, 'valor_usd_ha': float(valor_usd_ha),
            'valor_plantacion_usd': float(valor_plantacion_usd), 'valor_plantacion_uf': float(valor_plantacion_uf),
            'valor_depurado_total': float(valor_depurado_total), 'valor_depurado_ha': float(valor_depurado_ha),
            'agua': safe_texto(o[12], 'No hay datos'), 'suelo': safe_texto(o[13], 'No hay datos'), 'desc': safe_texto(o[14], 'No se especifica'), 'foto': o[15],
            'es_ofertable': es_ofertable, 'porc_oferta': float(porc_oferta),
            'v_ajustado': float(v_ajustado), 'u_hectarea': u_hectarea,
            'fecha_pub': fecha_db.strftime('%m-%Y') if fecha_db else "Sin Fecha"
        })
        
    return render_template('resultados.html', ofertas=ofertas_procesadas, valor_uf=valor_uf, valor_usd=valor_usd)

@main_bp.route('/guardar_ofertas_batch', methods=['POST'])
def guardar_ofertas_batch():
    datos = request.get_json()
    if db.actualizar_ofertas_multiples(datos.get('ofertas', [])): return jsonify({"success": True})
    return jsonify({"success": False}), 500

@main_bp.route('/actualizar_plantacion', methods=['POST'])
def actualizar_plantacion():
    data = request.get_json()
    tiene_plantaciones = bool(data.get('tiene_plantaciones'))
    hectareas = float(data.get('ha_plantas', 0) or 0)
    detalle = safe_texto(data.get('detalle_plantas', 'No especificado'), 'No especificado')
    cultivo_nombre = safe_texto(data.get('cultivo_nombre', 'No valorizado'), 'No valorizado')
    valor_usd_ha = float(data.get('valor_usd_ha', 0) or 0)
    if db.actualizar_datos_plantacion(data.get('id'), tiene_plantaciones, hectareas, detalle, cultivo_nombre, valor_usd_ha):
        return jsonify({"success": True})
    return jsonify({"success": False}), 500

@main_bp.route('/exportar')
def exportar_csv():
    filas_bd = db.obtener_todas(); si = StringIO(); cw = csv.writer(si, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    cw.writerow(['Ubicación Específica', 'Región', 'Comuna', 'Superficie Total (Ha)', 'Precio Lista Total (UF)', 'Precio Lista Unitario (UF/Ha)', 'Fecha Publicación', 'Tipo', 'Precio Propuesto/Oferta (UF)', 'Precio Propuesto Unitario (UF/Ha)', 'Sup. Plantada (Ha)', 'Cultivo Seleccionado', 'Valor Plantación (USD/Ha)', 'Suelo Depurado Total (UF)', 'Suelo Depurado Unitario (UF/Ha)', 'Derechos de Agua', 'Topografía predominante', 'Link Publicación', 'Breve descripción'])
    valor_uf = Decimal(str(obtener_uf_actual())); valor_usd = Decimal(str(obtener_usd_actual()))
    for fila in filas_bd:
        es_ofertable = fila[17] if len(fila) > 17 else False; pct_oferta = fila[18] if len(fila) > 18 else Decimal('15.0'); val_oferta_manual = fila[19] if len(fila) > 19 else None
        superficie = fila[5] if fila[5] else Decimal('1'); v_lista = fila[6] if fila[6] else Decimal('0'); u_lista_ha = v_lista / superficie
        if es_ofertable: v_propuesto = val_oferta_manual if val_oferta_manual and val_oferta_manual > 0 else v_lista * (Decimal('1') - (Decimal(str(pct_oferta)) / Decimal('100')))
        else: v_propuesto = v_lista
        u_propuesto_ha = v_propuesto / superficie; fecha_str = fila[7].strftime('%d-%m-%Y') if fila[7] else "Sin Fecha"
        tiene_plantas = fila[9]; sup_plantada = fila[10] if tiene_plantas else Decimal('0.0'); cultivo_nombre = fila[21] if len(fila) > 21 and fila[21] else ''; val_usd_ha = Decimal(str(fila[22])) if len(fila) > 22 and fila[22] else Decimal('0.0')
        valor_plantacion_usd = sup_plantada * val_usd_ha; valor_plantacion_uf = (valor_plantacion_usd * valor_usd) / valor_uf if valor_uf > 0 else Decimal('0'); valor_depurado_total = v_propuesto - valor_plantacion_uf; valor_depurado_ha = valor_depurado_total / superficie
        cw.writerow([fila[2], fila[3], fila[4], "{:.2f}".format(superficie), "{:.0f}".format(v_lista), "{:.1f}".format(u_lista_ha), fecha_str, "Oferta" if es_ofertable else "Venta", "{:.0f}".format(v_propuesto), "{:.1f}".format(u_propuesto_ha), "{:.1f}".format(sup_plantada), cultivo_nombre, "{:.0f}".format(val_usd_ha), "{:.0f}".format(valor_depurado_total), "{:.1f}".format(valor_depurado_ha), fila[12], fila[13], fila[1], fila[14]])
    return Response(si.getvalue().encode('utf-8-sig'), mimetype="text/csv; charset=utf-8", headers={"Content-disposition": "attachment; filename=referencias_mercado.csv"})

@main_bp.route('/editar_propiedad_completa', methods=['POST'])
def editar_propiedad_completa():
    data = request.get_json()
    try:
        # 🔄 Normalizar región si se proporciona
        region_normalizada = DataProcessor.normalizar_region(data.get('region', '')) if data.get('region') else 'No especificado'
        comuna = safe_texto(data.get('comuna', 'No especificado'))
        tipo_ref = safe_texto(data.get('tipo_ref', 'Agrícola'))
        agua = safe_texto(data.get('agua', 'No hay datos'))
        suelo = safe_texto(data.get('suelo', 'No hay datos'))
        desc = safe_texto(data.get('desc', 'No hay datos'))
        if db.actualizar_propiedad_completa(int(data.get('id')), comuna, region_normalizada, float(data.get('superficie', 1)), float(data.get('v_total', 0)), tipo_ref, agua, suelo, desc): return jsonify({"success": True})
        return jsonify({"success": False, "message": "Error al guardar en base de datos"}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@main_bp.route('/eliminar', methods=['POST'])
def eliminar():
    data = request.get_json()
    if db.eliminar_ofertas([int(i) for i in data.get('ids')]): return {"success": True}
    return {"success": False}, 500