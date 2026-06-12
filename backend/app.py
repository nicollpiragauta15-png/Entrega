from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.gestor_porteros import GestorPorteros 
#from gestor_porteros import GestorPorteros
from datetime import datetime, timedelta
import traceback
import pandas as pd
from flask import send_file
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
import holidays 
from datetime import datetime
import os



app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
gestor = GestorPorteros()
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')
@app.route('/api/porteros', methods=['GET'])
def obtener_porteros():
    try:
        return jsonify({'success': True, 'data': gestor.obtener_porteros()})
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/asignar', methods=['POST'])
def asignar_turno():
    try:
        datos = request.json
        print(f"Recibiendo asignación: {datos}")      
        exito, mensaje = gestor.asignar_turno(
            datos.get('portero_id'), 
            datos.get('fecha'),
            datos.get('dia_descanso'),
            datos.get('dia_asignar'),
            datos.get('hora_inicio'),
            datos.get('hora_fin'),
            datos.get('horas_mantenimiento')
        )        
        print(f"Resultado: {exito} - {mensaje}")
        return jsonify({'success': exito, 'message': mensaje})
    except Exception as e:
        print(f"Error en asignación: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/asignaciones', methods=['GET'])
def obtener_asignaciones():
    try:
        fecha = request.args.get('fecha')
        print(f"Consultando asignaciones para fecha: {fecha}")
        
        if fecha:
            asignaciones = gestor.obtener_asignaciones_por_fecha(fecha)
        else:
            asignaciones = gestor.obtener_todas_asignaciones()      
        print(f"Asignaciones encontradas: {len(asignaciones)}")
        return jsonify({'success': True, 'data': asignaciones})
    except Exception as e:
        print(f"Error obteniendo asignaciones: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/api/reiniciar', methods=['POST'])
def reiniciar_registros():
    try:
        gestor.asignaciones = []
        gestor.novedades = []
        gestor.guardar_datos()
        return jsonify({
            'success': True,
            'message': 'Todos los registros fueron eliminados'
        })
    except Exception as e:
        print(f"Error reiniciando registros: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/novedades', methods=['GET'])
def obtener_novedades():
    return jsonify({
        "success": True,
        "data": gestor.novedades
    })

@app.route('/api/recomendacion', methods=['POST'])
def obtener_recomendacion():
    try:
        datos = request.json
        # Obtener datos
        fecha = datos.get('fecha')
        hora_inicio = datos.get(
            'hora_inicio'
        )
        mantenimiento = bool(
            datos.get('mantenimiento', False)
        )
        # Generar recomendación
        recomendacion = gestor.generar_recomendacion(
            fecha, hora_inicio, datos.get('portero_id'), datos.get('dia_descanso'), mantenimiento
        )
        return jsonify({
            'success': True,
            'data': recomendacion
        })

    except Exception as e:
        print(
            f"Error recomendación: {e}"
        )
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route(
    '/api/modificar-portero',
    methods=['PUT']
)
def modificar_portero():
    try:
        datos = request.json
        exito, mensaje = (
            gestor.modificar_portero_turno(
                int(datos['asignacion_id']),
                int(datos['nuevo_portero_id'])
            )
        )
        return jsonify({
            'success': exito,
            'message': mensaje
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/eliminar-turno/<int:asignacion_id>', methods=['DELETE'])
def eliminar_turno(asignacion_id):
    try:
        exito, mensaje = gestor.eliminar_turno(asignacion_id)
        if exito:
            return jsonify({'success': True, 'message': mensaje})
        else:
            return jsonify({'success': False, 'message': mensaje}), 400
            
    except Exception as e:
        print(f"Error eliminando turno: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route(
    '/api/editar-turno',
    methods=['PUT']
)
def editar_turno():
    try:
        datos = request.json
        exito, mensaje = (
            gestor.editar_turno(datos)
        )
        return jsonify({
            'success': exito,
            'message': mensaje
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
    
def construir_matriz_turnos(asignaciones):
    dias_es = [
        'Lunes',
        'Martes',
        'Miércoles',
        'Jueves',
        'Viernes',
        'Sábado',
        'Domingo'
    ]

    fechas = sorted(
        list(
            set(
                a["fecha"]
                for a in asignaciones
            )
        )
    )

    horas = []
    for h in range(24):
        hora = datetime.strptime(
            f"{h}:00",
            "%H:%M"
        )
        horas.append(
            hora.strftime("%I:00 %p")
        )
    matriz = {}
    for fecha in fechas:
        matriz[fecha] = {}
        for hora in horas:
            matriz[fecha][hora] = ""

    # Llenar con porteros
    for asignacion in asignaciones:
        fecha = asignacion["fecha"]
        hora_inicio = datetime.strptime(
            asignacion["hora_inicio"],
            "%H:%M"
        ).strftime("%I:00 %p")
        matriz[fecha][hora_inicio] = (
            asignacion["portero_nombre"]
        )
    return fechas, horas, matriz

def obtener_fila_hora(hora):
    """
    Convierte 06:00 -> fila correspondiente
    """
    hora_obj = datetime.strptime(hora, "%H:%M")
    fila_inicio = 3
    return fila_inicio + hora_obj.hour
festivos_co = holidays.Colombia()

def es_festivo_colombia(fecha):
    try:
        if isinstance(fecha, datetime):
            return fecha.date() in festivos_co
        if isinstance(fecha, str):
            return (
                datetime.strptime(
                    fecha,
                    "%Y-%m-%d"
                ).date()
                in festivos_co
            )
        return False
    except:
        return False

def obtener_fechas_calendario(asignaciones):

    if not asignaciones:
        return []

    fechas_reales = sorted([
        datetime.strptime(
            a["fecha"],
            "%Y-%m-%d"
        )
        for a in asignaciones
    ])

    fecha_inicio = fechas_reales[0]

    return [
        fecha_inicio + timedelta(days=i)
        for i in range(30)
    ]

def obtener_contadores_turnos(asignaciones):

    contadores = {}

    contador_por_portero = {}

    asignaciones_ordenadas = sorted(
        asignaciones,
        key=lambda x: (
            x["portero_nombre"],
            x["fecha"],
            x["hora_inicio"]
        )
    )

    for asignacion in asignaciones_ordenadas:

        nombre = asignacion["portero_nombre"]

        if nombre not in contador_por_portero:

            contador_por_portero[nombre] = 1

        numero_actual = contador_por_portero[nombre]

        contadores[
            asignacion["id"]
        ] = numero_actual

        contador_por_portero[nombre] += 1

        # reinicia después de 7

        if contador_por_portero[nombre] > 7:

            contador_por_portero[nombre] = 1

    return contadores

@app.route('/api/exportar-excel', methods=['GET'])
def exportar_excel():
    try:
        asignaciones = gestor.obtener_todas_asignaciones()
        if not asignaciones:
            return jsonify({
                "success": False,
                "message": "No existen turnos"
            }), 400
        wb = Workbook()
        ws = wb.active
        ws.title = "Turnos"
        borde = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        centro = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )
        gris = PatternFill(
            "solid",
            fgColor="D9D9D9"
        )
        naranja = PatternFill(
            "solid",
            fgColor="F4B183"
        )
        rojo = PatternFill(
            "solid",
            fgColor="FF0000"
        )
        azul = PatternFill(
            "solid",
            fgColor="B4C6E7"
        )
        amarillo = PatternFill(
            "solid",
            fgColor="FFFF00"
        )

        fuente_negra = Font(
            color="000000",
            bold=True
        )

        fill_sabado = PatternFill(
            start_color="F4CCCC",
            end_color="F4CCCC",
            fill_type="solid"
        )

        fill_rojo = PatternFill(
            start_color="FF0000",
            end_color="FF0000",
            fill_type="solid"
        )

        contadores_turnos = obtener_contadores_turnos(
            asignaciones
        ) 
                
        fechas = obtener_fechas_calendario(asignaciones)

        print(
            "RANGO CALENDARIO:",
            fechas[0],
            fechas[-1]
        )

        bloques = [
            fechas[i:i+10]
            for i in range(0, len(fechas), 10)
        ]

        dias = [
            "LUNES",
            "MARTES",
            "MIÉRCOLES",
            "JUEVES",
            "VIERNES",
            "SÁBADO",
            "DOMINGO"
        ]

        fila_inicio_bloque = 1

        for bloque in bloques:

            # FILA DIA Y FECHA

            ws.cell(
                fila_inicio_bloque,
                1
            ).value = "DIA"

            ws.cell(
                fila_inicio_bloque + 1,
                1
            ).value = "FECHA"

            ws.cell(
                fila_inicio_bloque,
                1
            ).fill = gris

            ws.cell(
                fila_inicio_bloque + 1,
                1
            ).fill = gris

            for col, fecha in enumerate(
                bloque,
                start=2
            ):

                celda_dia = ws.cell(
                    fila_inicio_bloque,
                    col
                )

                celda_fecha = ws.cell(
                    fila_inicio_bloque + 1,
                    col
                )

                celda_dia.value = dias[
                    fecha.weekday()
                ]

                celda_fecha.value = fecha.strftime(
                    "%d/%m/%Y"
                )

                if fecha.weekday() == 5:

                    celda_dia.fill = fill_sabado
                    celda_fecha.fill = fill_sabado

                elif (
                    fecha.weekday() == 6
                    or es_festivo_colombia(
                        fecha.strftime("%Y-%m-%d")
                    )
                ):

                    celda_dia.fill = fill_rojo
                    celda_fecha.fill = fill_rojo

                else:

                    celda_dia.fill = gris
                    celda_fecha.fill = gris
            # FILAS HORAS

            fila_hora = fila_inicio_bloque + 2

            for hora in range(24):

                texto_hora = (
                    datetime.strptime(
                        f"{hora}:00",
                        "%H:%M"
                    )
                    .strftime("%I:00 %p")
                    .lstrip("0")
                )

                ws.cell(
                    fila_hora,
                    1
                ).value = (
                    f"ENTRADA {texto_hora}"
                )

                ws.cell(
                    fila_hora,
                    1
                ).fill = gris

                fila_hora += 1

            # UBICAR TURNOS

            for asignacion in asignaciones:

                fecha_turno = datetime.strptime(
                    asignacion["fecha"],
                    "%Y-%m-%d"
                )

                for col, fecha in enumerate(
                    bloque,
                    start=2
                ):

                    if (
                        fecha.date()
                        ==
                        fecha_turno.date()
                    ):

                        fila_turno = (
                            fila_inicio_bloque
                            + 2
                            + int(
                                asignacion[
                                    "hora_inicio"
                                ].split(":")[0]
                            )
                        )

                        numero_turno = contadores_turnos[
                            asignacion["id"]
                        ]

                        ws.cell(
                            fila_turno,
                            col
                        ).value = (
                            f"{asignacion['portero_nombre']} "
                            f"{numero_turno}/8"
                        )

                        break

            # FILA DESCANSOS

            fila_descanso = (
                fila_inicio_bloque + 26
            )

            ws.cell(
                fila_descanso,
                1
            ).value = "DESCANSOS"

            for col in range(
                1,
                len(bloque) + 2
            ):

                ws.cell(
                    fila_descanso,
                    col
                ).fill = azul

            for col, fecha in enumerate(
                bloque,
                start=2
            ):
                nombre_dia = dias[
                    fecha.weekday()
                ].capitalize()

                descanso = ""

                for portero in gestor.porteros.values():

                    if (
                        portero[
                            "dia_descanso"
                        ]
                        ==
                        nombre_dia
                    ):

                        descanso += (
                            f"DESCANSA "
                            f"{portero['nombre']}"
                        )

                ws.cell(
                    fila_descanso,
                    col
                ).value = descanso
            fila_novedades = fila_descanso + 1
            ws.cell(
                fila_novedades,
                1
            ).value = "NOVEDADES"
            ws.cell(
                fila_novedades,
                1
            ).font = fuente_negra
            for col in range(
                1,
                len(bloque) + 2
            ):
                celda = ws.cell(
                    fila_novedades,
                    col
                )
                celda.fill = amarillo
                celda.font = fuente_negra

            for col, fecha in enumerate(
                bloque,
                start=2
            ):
                texto = ""
                for novedad in gestor.novedades:
                    if (
                        novedad["fecha"]
                        ==
                        fecha.strftime("%Y-%m-%d")
                    ):
                        texto += (
                            f"• {novedad['portero_nombre']} "
                            f"({novedad['horas']}h)\n"
                            f"{novedad['descripcion']}\n"
                        )

                ws.cell(
                    fila_novedades,
                    col
                ).value = texto
            for fila in range(
                fila_inicio_bloque,
                fila_inicio_bloque + 28
            ):
                for col in range(
                    1,
                    len(bloque) + 2
                ):
                    celda = ws.cell(
                        fila,
                        col
                    )
                    celda.border = borde
                    celda.alignment = centro
            fila_inicio_bloque += 31
        output = BytesIO()
        ws.column_dimensions["A"].width = 22
        for col in range(2, 12):
            letra = get_column_letter(col)
            ws.column_dimensions[
                letra
            ].width = 18
        for bloque_num in range(len(bloques)):
            fila_novedades = 28 + (bloque_num * 31)
            ws.row_dimensions[fila_novedades].height = 40    
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="reporte_turnos.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    
@app.route('/api/excel-preview', methods=['GET'])
def excel_preview():
    try:
        asignaciones = gestor.obtener_todas_asignaciones()

        contadores_turnos = obtener_contadores_turnos(
            asignaciones
        )

        if not asignaciones:
            return jsonify({
                "success": True,
                "html": """
                <div class='empty-preview'>
                    No hay asignaciones registradas
                </div>
                """
            })
        fechas = obtener_fechas_calendario(
            asignaciones
        )
        bloques = [
            fechas[i:i+10]
            for i in range(
                0,
                len(fechas),
                10
            )
        ]
        dias_es = [
            "LUNES",
            "MARTES",
            "MIÉRCOLES",
            "JUEVES",
            "VIERNES",
            "SÁBADO",
            "DOMINGO"
        ]
        html = """
        <div class="excel-grid-wrapper">
        """
        for bloque in bloques:
            html += """
            <table class="excel-grid">
           """
            html += "<tr>"
            html += "<th>DIA</th>"
            for fecha in bloque:
                clase = ""
                if fecha.weekday() == 5:
                    clase = "sabado"
                elif (
                    fecha.weekday() == 6
                    or es_festivo_colombia(
                        fecha.strftime("%Y-%m-%d")
                    )
                ):
                    clase = "festivo"
                html += (
                    f"<th class='{clase}'>"
                    f"{dias_es[fecha.weekday()]}"
                    f"</th>"
                )
            html += "</tr>"
            html += "<tr>"
            html += "<th>FECHA</th>"
            for fecha in bloque:
                clase = ""
                if fecha.weekday() == 5:
                    clase = "sabado"
                elif (
                    fecha.weekday() == 6
                    or es_festivo_colombia(
                        fecha.strftime("%Y-%m-%d")
                    )
                ):
                    clase = "festivo"
                html += (
                    f"<td class='{clase}'>"
                    f"{fecha.strftime('%d/%m/%Y')}"
                    f"</td>"
                )
            html += "</tr>"
            for hora in range(24):
                texto_hora = (
                    datetime.strptime(
                        f"{hora}:00",
                        "%H:%M"
                    )
                    .strftime("%I:00 %p")
                    .lstrip("0")
                )
                html += "<tr>"
                html += (
                    f"<td class='hora'>"
                    f"ENTRADA {texto_hora}"
                    f"</td>"
                )
                for fecha in bloque:
                    contenido = ""
                    #fecha_actual = fecha.strftime("%Y-%m-%d")
                    fecha_actual = fecha.date()
                    for asignacion in asignaciones:
                        fecha_asignacion = datetime.strptime(
                            asignacion["fecha"][:10],
                            "%Y-%m-%d"
                        ).date()

                        if fecha_asignacion == fecha_actual:
                            hora_asignada = int(
                                asignacion["hora_inicio"]
                                .split(":")[0]
                            )
                            if hora_asignada == hora:
                                numero_turno = contadores_turnos[
                                    asignacion["id"]
                                ]

                                contenido = (
                                    f"{asignacion['portero_nombre']} "
                                    f"{numero_turno}/8"
                                )
                                break
                    html += f"<td>{contenido}</td>"
                html += "</tr>"
            html += "<tr>"
            html += (
                "<td class='descanso-titulo'>"
                "DESCANSOS"
                "</td>"
            
            )
            for fecha in bloque:
                nombre_dia = dias_es[
                    fecha.weekday()
                ].capitalize()
                descanso = ""
                for portero in gestor.porteros.values():
                    if (
                        portero["dia_descanso"]
                        == nombre_dia
                    ):
                        descanso += (
                            f"DESCANSA "
                            f"{portero['nombre']}"
                        )
                html += (
                    f"<td class='descanso'>"
                    f"{descanso}"
                    f"</td>"
                )
            html += "<tr>"
            html += (
                "<td class='descanso-titulo'>"
                "NOVEDADES"
                "</td>"
            )
            for fecha in bloque:
                texto = ""
                for novedad in gestor.novedades:
                    if (
                        novedad["fecha"]
                        ==
                        fecha.strftime("%Y-%m-%d")
                    ):
                        texto += (
                            f"<strong>"
                            f"{novedad['portero_nombre']}"
                            f"</strong><br>"
                            f"{novedad['horas']} horas<br>"
                            f"{novedad['descripcion']}<br><br>"
                        )
                html += (
                    f"<td class='novedad'>"
                    f"{texto}"
                    f"</td>"
                )
            html += "</tr>"
            html += "</table><br>"
        html += "</div>"
        return jsonify({
            "success": True,
            "html": html
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
@app.route(
    '/api/agregar-portero',
    methods=['POST']
)
def agregar_portero():
    datos = request.json
    exito, mensaje = gestor.agregar_portero(
        datos["nombre"],
        datos["dia_descanso"]
    )
    if exito:
        gestor.guardar_porteros()
    return jsonify({
        "success": exito,
        "message": mensaje
    })

@app.route(
    '/api/eliminar-portero',
    methods=['DELETE']
)
def eliminar_portero():
    datos = request.json
    exito, mensaje = gestor.eliminar_portero(
        int(datos["portero_id"])
    )
    if exito:
        gestor.guardar_porteros()
    return jsonify({
        "success": exito,
        "message": mensaje
    })

@app.route(
    '/api/agregar-novedad',
    methods=['POST']
)
def agregar_novedad():
    datos = request.json
    exito, mensaje = (
        gestor.agregar_novedad(
            datos["descripcion"],
            datos["portero_id"],
            datos["fecha"],
            datos["horas"] 
        )
    )
    return jsonify({
        "success": exito,
        "message": mensaje
    })

def obtener_resumen_horas_excel():
    resumen = []
    if not gestor.asignaciones:
        return resumen
    fecha_final = max(
        a["fecha"]
        for a in gestor.asignaciones
    )
    for portero_id, portero in gestor.porteros.items():
        if not portero["activo"]:
            continue
        semanal = (
            gestor.calcular_total_horas_portero(
                portero_id,
                fecha_final,
                portero["dia_descanso"]
            )
        )
        limite = (
            gestor.obtener_horas_semanales(
                fecha_final
            )
        )
        mensual = (
            gestor.calcular_total_horas_mensual(
                portero_id,
                fecha_final
            )
        )
        resumen.append({

            "nombre":
                portero["nombre"],

            "semanal":
                semanal,

            "limite":
                limite,

            "mensual":
                mensual
        })

    return resumen

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
