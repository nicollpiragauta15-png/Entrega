import os
import json
from datetime import datetime, timedelta

class GestorPorteros:
    def __init__(self):
        self.dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        self.porteros = {
            1: {"nombre": "HOA", "activo": True, "dia_descanso": "Sábado"},
            2: {"nombre": "CR7", "activo": True, "dia_descanso": "Lunes"},
            3: {"nombre": "YA", "activo": True, "dia_descanso": "Martes"},
            4: {"nombre": "FIM", "activo": True, "dia_descanso": "Domingo"}
        }
        
        self.asignaciones = []
        self.cargar_datos()
    
    def obtener_porteros(self):

        return [

            {
                "id": id,
                "nombre": p["nombre"],
                "dia_descanso": p.get("dia_descanso")
            }

            for id, p in self.porteros.items()

            if p["activo"]
        ]
    
    def calcular_horas(self, hora_inicio, hora_fin):
        """Calcula horas cruzando la medianoche si es necesario"""
        try:
            inicio = datetime.strptime(hora_inicio, "%H:%M")
            fin = datetime.strptime(hora_fin, "%H:%M")
            
            if fin <= inicio:
                fin = fin.replace(day=fin.day + 1)
            
            diferencia = (fin - inicio).seconds / 3600
            return round(diferencia, 1)
        except:
            return 0
    
    def verificar_conflicto_horario(self, fecha, dia_asignar, hora_inicio, hora_fin):
        """Verifica si hay conflicto de horario con asignaciones existentes"""
        for asig in self.asignaciones:
            if asig["fecha"] == fecha and asig["dia_asignar"] == dia_asignar:
                inicio_existente = datetime.strptime(asig["hora_inicio"], "%H:%M")
                fin_existente = datetime.strptime(asig["hora_fin"], "%H:%M")
                nuevo_inicio = datetime.strptime(hora_inicio, "%H:%M")
                nuevo_fin = datetime.strptime(hora_fin, "%H:%M")
                
                if fin_existente <= inicio_existente:
                    fin_existente = fin_existente.replace(day=fin_existente.day + 1)
                if nuevo_fin <= nuevo_inicio:
                    nuevo_fin = nuevo_fin.replace(day=nuevo_fin.day + 1)
                
                if not (nuevo_fin <= inicio_existente or nuevo_inicio >= fin_existente):
                    return True, f"Conflicto con turno existente: {asig['hora_inicio']} - {asig['hora_fin']}"
        return False, ""
    
    def asignar_turno(self, portero_id, fecha_real, dia_descanso, dia_asignar, hora_inicio, hora_fin,horas_mantenimiento):

        if portero_id not in self.porteros:
            return False, "Portero no encontrado"

        # Día descanso fijo
        dia_descanso = self.porteros[
            portero_id
        ]["dia_descanso"]

        if dia_asignar == dia_descanso:

            return False, (
                f"El portero descansa el "
                f"{dia_descanso}"
            )

        horas = self.calcular_horas(
            hora_inicio,
            hora_fin
        )

        limite = self.obtener_horas_semanales(
            fecha_real
        )

        horas_actuales = (
            self.calcular_total_horas_portero(
                portero_id,
                fecha_real,
                dia_descanso
            )
        )

        nuevo_total = horas_actuales + horas

        if nuevo_total > limite:

            return False, (
                f"El portero ya tiene "
                f"{horas_actuales} horas. "
                f"Con este turno tendría "
                f"{nuevo_total} horas "
                f"(máximo {limite})"
            )

        if horas > 8:

            print(
                f"⚠️ Advertencia: "
                f"Turno con {horas} horas"
            )

        if horas <= 0:

            return False, (
                "Las horas deben "
                "ser mayores a 0"
            )

        if horas_mantenimiento != "Si":

            hay_conflicto, mensaje = (
                self.verificar_conflicto_horario(
                    fecha_real,
                    dia_asignar,
                    hora_inicio,
                    hora_fin
                )
            )

            if hay_conflicto:
                return False, mensaje

        actividad = "Porteria"

        if horas_mantenimiento == "Si":
            actividad = "Mantenimiento"

        fecha_calculada = self.calcular_fecha_real(
            fecha_real,
            dia_asignar
        )
        
        asignacion = {

            "id": len(self.asignaciones) + 1,

            "portero_id": portero_id,

            "portero_nombre": self.porteros[
                portero_id
            ]["nombre"],

            "fecha": fecha_calculada,

            "dia_descanso": dia_descanso,

            "dia_asignar": dia_asignar,

            "hora_inicio": hora_inicio,

            "hora_fin": hora_fin,

            "horas": horas,

            "actividad": actividad,

            "fecha_registro": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        self.asignaciones.append(asignacion)

        self.guardar_datos()

        return True, (
            f"Turno asignado a "
            f"{self.porteros[portero_id]['nombre']}"
        )

    def obtener_asignaciones_por_fecha(self, fecha):
        return [a for a in self.asignaciones if a.get("fecha") == fecha]
    
    def obtener_todas_asignaciones(self):
        return self.asignaciones
    
    def guardar_datos(self):
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            with open('data/asignaciones.json', 'w', encoding='utf-8') as f:
                json.dump(self.asignaciones, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al guardar: {e}")
    
    def cargar_datos(self):
        try:
            if os.path.exists('data/asignaciones.json'):
                with open('data/asignaciones.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.asignaciones = data
                    else:  
                        self.asignaciones = []
        except Exception as e:
            print(f"Error al cargar: {e}")
            self.asignaciones = []


    def generar_recomendacion(self, fecha, hora_inicio, portero_id, dia_descanso, mantenimiento=False):
        limite = self.obtener_horas_semanales(fecha)
        horas_actuales = (self.calcular_total_horas_portero(portero_id, fecha, dia_descanso))
        horas_restantes = (limite - horas_actuales)
        if horas_restantes <= 0:
            return {
                "horas_turno": 0,
                "hora_inicio": hora_inicio,
                "hora_fin": hora_inicio,
                "mensaje": "Este portero ya completo sus horas"
            }
        
        if mantenimiento:
            actividad = "Mantenimiento"
            horas_turno = min(2, horas_restantes)

        elif horas_restantes <= 2:
            horas_turno = horas_restantes
            actividad = "Mantenimiento"
        else:
            actividad = "Porteria"
            if limite == 42:
                horas_turno = min(
                    7, horas_restantes
                )
            else:
                horas_turno = min(8, horas_restantes)
        inicio = datetime.strptime(hora_inicio, "%H:%M")
        fin = (
            inicio +
            timedelta(hours=horas_turno) -
            timedelta(minutes=1)
        )
        return {
            "horas_semanales": limite,
            "horas_actuales": horas_actuales,
            "horas_restantes": horas_restantes,
            "horas_turno": horas_turno,
            "actividad": actividad,
            "hora_inicio": hora_inicio,
            "hora_fin": fin.strftime("%H:%M")
        }
    
    def obtener_horas_semanales(self, fecha):
        fecha_obj = datetime.strptime(
            fecha,
            "%Y-%m-%d"
        )

        fecha_cambio = datetime(
            2026,
            7,
            15
        )

        return 42 if fecha_obj >= fecha_cambio else 44
    
    def calcular_total_horas_portero(
        self,
        portero_id,
        fecha,
        dia_descanso
    ):

        total = 0

        inicio_semana, fin_semana = (
            self.obtener_rango_semana_portero(
                fecha,
                dia_descanso
            )
        )

        for asignacion in self.asignaciones:

            if asignacion["portero_id"] != portero_id:
                continue

            fecha_asig = datetime.strptime(
                asignacion["fecha"],
                "%Y-%m-%d"
            )

            if (
                inicio_semana <= fecha_asig <= fin_semana
            ):

                total += asignacion["horas"]

        return total
    
    def modificar_portero_turno(
        self,
        asignacion_id,
        nuevo_portero_id
    ):

        if nuevo_portero_id not in self.porteros:

            return False, "Portero no encontrado"

        for asignacion in self.asignaciones:

            if asignacion["id"] == asignacion_id:

                horas_turno = asignacion["horas"]

                dia_descanso = self.porteros[
                    nuevo_portero_id
                ]["dia_descanso"]

                horas_actuales = (
                    self.calcular_total_horas_portero(
                        nuevo_portero_id,
                        asignacion["fecha"],
                        dia_descanso
                    )
                )

                limite = self.obtener_horas_semanales(
                    asignacion["fecha"]
                )

                if (
                    horas_actuales + horas_turno > limite
                ):

                    return False, (
                        f"El nuevo portero excede "
                        f"el límite semanal "
                        f"de {limite} horas"
                    )

                asignacion["portero_id"] = (
                    nuevo_portero_id
                )

                asignacion["portero_nombre"] = (
                    self.porteros[
                        nuevo_portero_id
                    ]["nombre"]
                )

                asignacion["dia_descanso"] = (
                    dia_descanso
                )

                self.guardar_datos()

                return True, (
                    "Portero actualizado correctamente"
                )

        return False, "Asignación no encontrada"
    
    def obtener_rango_semana_portero(
        self,
        fecha,
        dia_descanso
    ):

        dias = {
            "Lunes": 0,
            "Martes": 1,
            "Miércoles": 2,
            "Jueves": 3,
            "Viernes": 4,
            "Sábado": 5,
            "Domingo": 6
        }

        fecha_obj = datetime.strptime(
            fecha,
            "%Y-%m-%d"
        )

        # Día en que inicia semana
        inicio_semana_num = (
            dias[dia_descanso] + 1
        ) % 7

        dia_actual_num = fecha_obj.weekday()

        diferencia = (
            dia_actual_num -
            inicio_semana_num
        ) % 7

        inicio_semana = (
            fecha_obj -
            timedelta(days=diferencia)
        )

        fin_semana = (
            inicio_semana +
            timedelta(days=6)
        )

        return inicio_semana, fin_semana
        
    def calcular_fecha_real(self, fecha_base, dia_asignar):
        """
        Calcula la fecha real respetando la semana de la fecha base
        """
        dias = {
            "Lunes": 0,
            "Martes": 1,
            "Miércoles": 2,
            "Jueves": 3,
            "Viernes": 4,
            "Sábado": 5,
            "Domingo": 6
        }
        
        print(f"DEBUG - fecha_base recibida: {fecha_base}")
        print(f"DEBUG - dia_asignar: {dia_asignar}")
        
        fecha_obj = datetime.strptime(fecha_base, "%Y-%m-%d")
        dia_base = fecha_obj.weekday()
        dia_objetivo = dias[dia_asignar]
        
        print(f"DEBUG - fecha_obj: {fecha_obj}")
        print(f"DEBUG - dia_base (0=Lunes): {dia_base}")
        print(f"DEBUG - dia_objetivo: {dia_objetivo}")
        
        # Calcular diferencia
        if dia_objetivo >= dia_base:
            diferencia = dia_objetivo - dia_base
        else:
            diferencia = (7 - dia_base) + dia_objetivo
        
        print(f"DEBUG - diferencia en días: {diferencia}")
        
        fecha_real = fecha_obj + timedelta(days=diferencia)
        resultado = fecha_real.strftime("%Y-%m-%d")
        
        print(f"DEBUG - fecha_real calculada: {resultado}")
        
        return resultado

    def editar_turno(self, datos):

        for asignacion in self.asignaciones:
            if asignacion["id"] == int(datos["id"]):
                portero_id = int(
                    datos["portero_id"]
                )
                dia_descanso = self.porteros[
                    portero_id
                ]["dia_descanso"]

                if (
                    datos["dia_asignar"] ==
                    dia_descanso
                ):
                    return False, (
                        f"El portero descansa "
                        f"el {dia_descanso}"
                    )
                horas = self.calcular_horas(
                    datos["hora_inicio"],
                    datos["hora_fin"]
                )
                if horas <= 0:
                    return False, (
                        "Horas inválidas"
                    )
                if horas > 8:
                    print(
                        f"⚠️ Advertencia: "
                        f"Turno editado con "
                        f"{horas} horas"
                    )
                # Restar horas actuales
                horas_actuales = (
                    self.calcular_total_horas_portero(
                        portero_id,
                        asignacion["fecha"],
                        dia_descanso
                    )
                ) - asignacion["horas"]
                limite = self.obtener_horas_semanales(
                    asignacion["fecha"]
                )
                nuevo_total = (
                    horas_actuales + horas
                )
                if nuevo_total > limite:

                    return False, (
                        f"El portero excede "
                        f"las {limite} horas"
                    )
                # Verificar conflictos
                for otra in self.asignaciones:
                    if otra["id"] == asignacion["id"]:
                        continue
                    if (
                        otra["fecha"] ==
                        asignacion["fecha"]
                        and
                        otra["dia_asignar"] ==
                        datos["dia_asignar"]
                    ):
                        inicio_existente = datetime.strptime(
                            otra["hora_inicio"],
                            "%H:%M"
                        )
                        fin_existente = datetime.strptime(
                            otra["hora_fin"],
                            "%H:%M"
                        )
                        nuevo_inicio = datetime.strptime(
                            datos["hora_inicio"],
                            "%H:%M"
                        )

                        nuevo_fin = datetime.strptime(
                            datos["hora_fin"],
                            "%H:%M"
                        )

                        if (
                            fin_existente <=
                            inicio_existente
                        ):

                            fin_existente = (
                                fin_existente.replace(
                                    day=fin_existente.day + 1
                                )
                            )

                        if (
                            nuevo_fin <=
                            nuevo_inicio
                        ):

                            nuevo_fin = (
                                nuevo_fin.replace(
                                    day=nuevo_fin.day + 1
                                )
                            )

                        if not (
                            nuevo_fin <= inicio_existente
                            or
                            nuevo_inicio >= fin_existente
                        ):

                            return False, (
                                "Conflicto con otro turno"
                            )

                asignacion["portero_id"] = (
                    portero_id
                )

                asignacion["portero_nombre"] = (
                    self.porteros[portero_id]["nombre"]
                )

                asignacion["dia_descanso"] = (
                    dia_descanso
                )

                asignacion["dia_asignar"] = (
                    datos["dia_asignar"]
                )

                asignacion["hora_inicio"] = (
                    datos["hora_inicio"]
                )

                asignacion["hora_fin"] = (
                    datos["hora_fin"]
                )

                asignacion["actividad"] = (
                    datos["actividad"]
                )

                asignacion["horas"] = horas

                self.guardar_datos()

                return True, (
                    "Turno actualizado correctamente"
                )

        return False, "Turno no encontrado"
    
    def eliminar_turno(self, asignacion_id):
        try:
            # Buscar el turno
            turno_encontrado = None
            for turno in self.asignaciones:
                if turno["id"] == asignacion_id:
                    turno_encontrado = turno
                    break
            
            if not turno_encontrado:
                return False, "Turno no encontrado"
            
            # Guardar información para el mensaje
            nombre_portero = turno_encontrado["portero_nombre"]
            fecha = turno_encontrado["fecha"]
            hora_inicio = turno_encontrado["hora_inicio"]
            hora_fin = turno_encontrado["hora_fin"]
            
            # Eliminar el turno
            self.asignaciones = [t for t in self.asignaciones if t["id"] != asignacion_id]
            
            # Guardar cambios
            self.guardar_datos()
            
            mensaje = f"Turno eliminado: {nombre_portero} - {fecha} ({hora_inicio} a {hora_fin})"
            return True, mensaje
            
        except Exception as e:
            print(f"Error eliminando turno: {e}")
            return False, f"Error al eliminar: {str(e)}"