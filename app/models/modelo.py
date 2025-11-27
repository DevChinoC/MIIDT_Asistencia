from datetime import datetime
from sqlite3 import IntegrityError
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta   # arriba del archivo, si aún no lo tienes
class Modelo:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor()

    # Agregar un nuevo estudiante
    from mysql.connector.errors import IntegrityError  # o pymysql.err.IntegrityError, según el conector que uses
    
    def _id_por_nombre(self, tabla: str, nombre):
        """Devuelve el id del catálogo; lo crea si no existe. Acepta None/''."""
        if not nombre or not str(nombre).strip():
            return None
        nombre = str(nombre).strip()
        # crear si no existe (idempotente por UNIQUE(nombre))
        self.cursor.execute(f"INSERT IGNORE INTO {tabla} (nombre) VALUES (%s)", (nombre,))
        self.cursor.execute(f"SELECT id FROM {tabla} WHERE nombre = %s LIMIT 1", (nombre,))
        row = self.cursor.fetchone()
        return row[0] if row else None

 
    def registrar_estudiante(
        self, email, matricula, nombre, apellido_p, apellido_m,
        huella_digital, generacion, area_conocimiento, carrera,
        asesor, id_asesor,
    ):
        """Registra un nuevo alumno. Evita duplicados por matrícula, conserva ceros a la izquierda
        y resuelve catálogos a *_id (generacion_id, area_id, carrera_id)."""
        try:
            fecha_registro = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

            # --- validar duplicado por matrícula ---
            self.cursor.execute(
                "SELECT 1 FROM alumnos WHERE matricula = %s LIMIT 1",
                (matricula.strip(),)
            )
            if self.cursor.fetchone():
                print(f"⚠️ Matrícula duplicada detectada: {matricula}")
                return "duplicado"
            
            self.cursor.execute(
                "SELECT 1 FROM alumnos WHERE email = %s LIMIT 1",
                (str(email).strip(),)
            )
            if self.cursor.fetchone():
                print(f"⚠️ Gmail duplicada detectada: {email}")
                return "duplicado_email"

            # --- resolver IDs de catálogos (crea si no existen) ---
            gen_id  = self._id_por_nombre("generaciones", generacion)
            area_id = self._id_por_nombre("areas_conocimiento", area_conocimiento)
            car_id  = self._id_por_nombre("carreras", carrera)

            # --- inserción segura: guardamos textos y *_id ---
            self.cursor.execute(
                """
                INSERT INTO alumnos (
                    email, matricula, nombre, apellido_paterno, apellido_materno,
                    huella_digital,
                    generacion, area_conocimiento, carrera,   -- textos (se conservan)
                    generacion_id, area_id, carrera_id,       -- nuevos FK IDs
                    asesor, asesor_id, 
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s,  %s, %s, %s,  %s, %s, %s,  %s, %s, %s,)
                """,
                (
                    email,
                    str(matricula).strip(),                  # conserva ceros a la izq.
                    nombre.title(),
                    apellido_p.capitalize(),
                    apellido_m.capitalize(),
                    huella_digital,
                    generacion, area_conocimiento, (carrera.title() if carrera else None),
                    gen_id, area_id, car_id,
                    asesor, id_asesor, 
                    fecha_registro,
                ),
            )
            self.db.commit()
            return True

            # Manejo de duplicados por UNIQUE (matricula/email) o FK
        except IntegrityError as e:
            print(f"Error de integridad (posible duplicado o FK): {e}")
            self.db.rollback()
            # Si quieres distinguir por código 1062, puedes parsear e.args
            return "duplicado"
        except Exception as e:
            print(f"Error general al registrar estudiante: {e}")
            self.db.rollback()
            return False



    def obtener_asesores(self):
        self.cursor.execute("SELECT id, name FROM teachers")
        rows = self.cursor.fetchall()
        asesores = []
        for row in rows:
            asesores.append({
                'id': row[0],
                'name': row[1]
            })
        return asesores

    def obtener_estudiantes(self):
        self.cursor.execute("SELECT id, matricula, nombre, apellido_paterno, apellido_materno FROM alumnos")
        rows = self.cursor.fetchall()
        estudiantes = []
        for row in rows:
            estudiantes.append({
                'id': row[0],
                'matricula': row[1],
                'nombre': row[2],
                'apellido_p': row[3],
                'apellido_m': row[4]
            })
        return estudiantes

    def obtener_estudiantes_registrados(self):
        """Obtiene la lista de todos los estudiantes"""
        try:
            query = """
                SELECT 
                id, 
                nombre, 
                apellido_paterno, 
                apellido_materno, 
                matricula, 
                email, 
                generacion, 
                asesor, 
                area_conocimiento, 
                carrera, 
                huella_digital
                FROM alumnos 
                ORDER BY apellido_paterno, apellido_materno, nombre;
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener la lista de estudiantes: {e}")
            return []

    def editar_estudiante(
    self, estudiante_id, email, matricula, nombre, apellido_p, apellido_m,
    huella_digital, generacion, area_conocimiento, carrera,
    asesor_nombre, id_asesor
    ):
        """Edita datos del alumno conservando la matrícula como texto."""
        try:
            fecha_actualizacion = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

            self.cursor.execute(
                """
                UPDATE alumnos
                SET email = %s,
                    matricula = %s,
                    nombre = %s,
                    apellido_paterno = %s,
                    apellido_materno = %s,
                    huella_digital = %s,
                    generacion = %s,
                    area_conocimiento = %s,
                    carrera = %s,
                    asesor = %s,
                    asesor_id = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    email,
                    str(matricula).strip(),  # conserva ceros a la izquierda
                    nombre.title(),
                    apellido_p.capitalize(),
                    apellido_m.capitalize(),
                    huella_digital,
                    generacion,
                    area_conocimiento,
                    carrera.title(),
                    asesor_nombre,
                    id_asesor,
                    fecha_actualizacion,
                    estudiante_id,
                ),
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al editar estudiante: {e}")
            self.db.rollback()
            return False

    def eliminar_estudiante(self, estudiante_id):
        try:
            # Primero eliminamos los registros relacionados en registro_asistencias
            self.cursor.execute("DELETE FROM registro_asistencias WHERE alumno_id = %s", (estudiante_id,))
            # Luego eliminamos al estudiante
            self.cursor.execute("DELETE FROM alumnos WHERE id = %s", (estudiante_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar estudiante: {e}")
            self.db.rollback()
            return False

    def get_huella_digital(self, id):
        self.cursor.execute("SELECT huella_digital FROM alumnos WHERE id = %s", (id,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return None

    def verificar_asistencia_existente(self, estudiante_id):
        """
        Verifica si un estudiante ya tiene un registro de asistencia para el día actual
        
        Args:
            estudiante_id (int): ID del estudiante a verificar
            
        Returns:
            bool: True si ya existe un registro de asistencia para hoy, False en caso contrario
        """
        try:
            fecha_actual = datetime.now().astimezone().strftime("%Y-%m-%d")
            self.cursor.execute(
                "SELECT id FROM registro_asistencias WHERE alumno_id = %s AND asistencia = %s",
                (estudiante_id, fecha_actual)
                )

            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Error al verificar asistencia existente: {e}")
            return False

    def registrar_asistencia(self, estudiante_id):
        try:
            # Verificar si ya existe un registro de asistencia para hoy
            if self.verificar_asistencia_existente(estudiante_id):
                return False  # Ya existe un registro para hoy
                
            # Registrar la asistencia
            create_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
            fecha = datetime.now().astimezone().strftime("%Y-%m-%d")
            hora_entrada = datetime.now().astimezone().strftime("%H:%M:%S")
            print(f"Intentando registrar asistencia para estudiante_id: {estudiante_id}")
            print(f"Datos: fecha={fecha}, hora_entrada={hora_entrada}, create_at={create_at}")
            self.cursor.execute(
                "INSERT INTO registro_asistencias (alumno_id, asistencia, hora_entrada, created_at) VALUES (%s, %s, %s, %s)",
                (estudiante_id, fecha, hora_entrada, create_at)
            )
            self.db.commit()
            print("Asistencia registrada exitosamente")
            return True
        except Exception as e:
            print(f"Error al registrar asistencia: {e}")
            self.db.rollback()
            return False
    
    

    def obtener_ultima_asistencia_hoy(self, estudiante_id):
        """
        Devuelve el último registro de asistencia de HOY para un estudiante.
        - Si no hay registros hoy -> None
        - Si hay, regresa dict con id, asistencia, hora_entrada, hora_salida
        """
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")

            self.cursor.execute("""
                SELECT id, asistencia, hora_entrada, hora_salida
                FROM registro_asistencias
                WHERE alumno_id = %s
                  AND DATE(asistencia) = %s
                ORDER BY asistencia DESC, id DESC
                LIMIT 1
            """, (estudiante_id, hoy))

            row = self.cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "asistencia": row[1],
                "hora_entrada": row[2],
                "hora_salida": row[3],
            }
        except Exception as e:
            print(f"Error al obtener última asistencia de hoy: {e}")
            return None


    def obtener_asistencias_hoy(self):
        try:
            hoy = datetime.now().astimezone().strftime("%Y-%m-%d")
            print(f"Buscando asistencias para la fecha: {hoy}")
            
            self.cursor.execute("""
                SELECT r.id, a.nombre, a.apellido_paterno, a.apellido_materno, 
                       r.hora_entrada, r.hora_salida, a.id as alumno_id
                FROM registro_asistencias r
                JOIN alumnos a ON r.alumno_id = a.id
                WHERE r.asistencia = %s
                ORDER BY r.asistencia DESC, r.hora_entrada DESC
            """, (hoy,))
            asistencias = self.cursor.fetchall()
            print(f"Se encontraron {len(asistencias)} asistencias para hoy")
            return asistencias
        except Exception as e:
            print(f"Error al obtener asistencias: {e}")
            return []

    def obtener_asistencias_hoy_completo(self):
        """
        Obtiene las asistencias de hoy con formato de diccionario para reportes.
        Devuelve: [{nombre, fecha, hora_entrada, hora_salida, horas_presentes}, ...]
        """
        try:
            hoy = datetime.now().astimezone().strftime("%Y-%m-%d")
            
            self.cursor.execute("""
                SELECT 
                    a.nombre, a.apellido_paterno, a.apellido_materno,
                    r.asistencia, r.hora_entrada, r.hora_salida,
                    CASE
                        WHEN r.hora_entrada IS NOT NULL AND r.hora_salida IS NOT NULL
                        THEN TIME_TO_SEC(TIMEDIFF(r.hora_salida, r.hora_entrada)) / 3600.0
                        ELSE 0
                    END AS horas_presentes
                FROM registro_asistencias r
                JOIN alumnos a ON r.alumno_id = a.id
                WHERE r.asistencia = %s
                ORDER BY a.apellido_paterno, a.apellido_materno, a.nombre
            """, (hoy,))
            
            rows = self.cursor.fetchall()
            resultado = []
            
            for row in rows:
                nombre_completo = f"{row[0]} {row[1]} {row[2]}".strip()
                fecha = row[3]
                hora_entrada = row[4]
                hora_salida = row[5]
                horas_val = float(row[6]) if row[6] else 0.0
                
                # Formateo
                fecha_str = str(fecha)
                hora_ent_str = str(hora_entrada) if hora_entrada else "--:--"
                hora_sal_str = str(hora_salida) if hora_salida else "--:--"
                
                # Topar a 8 horas (regla de negocio vista en obtener_estadisticas_estudiante)
                if horas_val > 8.0:
                    horas_val = 8.0
                
                resultado.append({
                    "nombre": nombre_completo,
                    "fecha": fecha_str,
                    "hora_entrada": hora_ent_str,
                    "hora_salida": hora_sal_str,
                    "horas_presentes": f"{horas_val:.2f}"
                })
                
            return resultado
        except Exception as e:
            print(f"Error al obtener asistencias completas de hoy: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    def registrar_salida(self, registro_id):
        """
        Registra o actualiza la hora de salida de un estudiante.
        
        Args:
            registro_id (int): ID del registro de asistencia
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            hora_salida = datetime.now().strftime("%H:%M:%S")
            
            query = """
                UPDATE registro_asistencias 
                SET hora_salida = %s
                WHERE id = %s
            """
            self.cursor.execute(query, (hora_salida, registro_id))
            self.db.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error al registrar salida: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'db'):
                self.db.rollback()
            return False
            
    def obtener_estudiante_por_registro(self, registro_id):
        """Obtiene el ID del estudiante asociado a un registro de asistencia"""
        try:
            query = "SELECT alumno_id FROM registro_asistencias WHERE id = %s"
            self.cursor.execute(query, (registro_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error al obtener estudiante por registro: {e}")
            return None
            
    def obtener_huella_estudiante(self, estudiante_id):
        """Obtiene la plantilla de huella del estudiante"""
        try:
            query = "SELECT huella_digital FROM alumnos WHERE id = %s"
            self.cursor.execute(query, (estudiante_id,))
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error al obtener huella del estudiante: {e}")
            return None
            
    def obtener_asistencia_por_id(self, registro_id):
        """Obtiene los detalles de una asistencia por su ID"""
        try:
            query = """
                SELECT id, alumno_id, asistencia, hora_entrada, hora_salida, created_at 
                FROM registro_asistencias 
                WHERE id = %s
            """
            self.cursor.execute(query, (registro_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener asistencia por ID: {e}")
            return None
            
    def obtener_todos_los_estudiantes(self):
        """Obtiene la lista de todos los estudiantes"""
        try:
            query = """
                SELECT id, nombre, apellido_paterno, apellido_materno, huella_digital
                FROM alumnos 
                ORDER BY apellido_paterno, apellido_materno, nombre
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener la lista de estudiantes: {e}")
            return []

    def obtener_todos_los_estudiantes_reportes(self):
        """Obtiene la lista de todos los estudiantes para reportes"""
        try:
            query = """
                SELECT id, email, matricula, nombre, apellido_paterno, apellido_materno, generacion, asesor, area_conocimiento, carrera
                FROM alumnos 
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener la lista de estudiantes: {e}")
            return []

    def obtener_estadisticas_estudiante(self, estudiante_id, mes=None, anio=None, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las estadísticas de un estudiante.
        - Las horas diarias se TOPAN a 8.00 para efectos de reporte.
        """
        try:
            # Consulta base
            query = """
                SELECT 
                    asistencia as fecha,
                    CASE 
                        WHEN hora_entrada IS NOT NULL THEN hora_entrada
                        ELSE NULL
                    END as hora_entrada,
                    CASE 
                        WHEN hora_salida IS NOT NULL THEN hora_salida
                        ELSE NULL
                    END as hora_salida,
                    CASE
                        WHEN hora_entrada IS NOT NULL AND hora_salida IS NOT NULL
                        THEN TIME_TO_SEC(TIMEDIFF(hora_salida, hora_entrada)) / 3600.0
                        ELSE 0
                    END AS horas_presentes
                FROM registro_asistencias 
                WHERE alumno_id = %s
            """

            params = [estudiante_id]

            if fecha_inicio and fecha_fin:
                query += " AND DATE(asistencia) BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            elif mes is not None and anio is not None:
                query += " AND MONTH(asistencia) = %s AND YEAR(asistencia) = %s"
                params.extend([mes, anio])
            elif mes is not None:
                query += " AND MONTH(asistencia) = %s AND YEAR(asistencia) = YEAR(CURDATE())"
                params.append(mes)
            elif anio is not None:
                query += " AND YEAR(asistencia) = %s"
                params.append(anio)

            query += " ORDER BY fecha DESC"

            print(f"Ejecutando consulta SQL con parámetros: {params}")
            self.cursor.execute(query, params)
            historial = self.cursor.fetchall()
            print(f"Historial obtenido ({type(historial)}): {historial}")

            historial_dicts = []
            horas_entrada = []
            horas_salida = []
            horas_semanales = {}
            horas_mensuales = {}
            total_horas_periodo = 0.0   # suma total de horas (ya topadas a 8)

            from datetime import datetime

            for reg in historial:
                try:
                    # Valores crudos
                    fecha_raw = reg[0]
                    hora_ent_raw = reg[1]
                    hora_sal_raw = reg[2]
                    horas_raw = reg[3]

                    # Formateo básico
                    fecha = '--/--/----'
                    hora_entrada = '--:--'
                    hora_salida = '--:--'

                    if fecha_raw:
                        if hasattr(fecha_raw, 'strftime'):
                            fecha = fecha_raw.strftime('%d/%m/%Y')
                        else:
                            fecha = str(fecha_raw)

                    if hora_ent_raw:
                        if hasattr(hora_ent_raw, 'strftime'):
                            hora_entrada = hora_ent_raw.strftime('%H:%M')
                        else:
                            hora_entrada = str(hora_ent_raw)

                    if hora_sal_raw:
                        if hasattr(hora_sal_raw, 'strftime'):
                            hora_salida = hora_sal_raw.strftime('%H:%M')
                        else:
                            hora_salida = str(hora_sal_raw)

                    # ====== TOPAR HORAS DIARIAS A 8.00 ======
                    horas_presentes = '0.00'
                    horas_val = 0.0
                    if horas_raw is not None:
                        try:
                            horas_val = float(horas_raw)
                        except (ValueError, TypeError):
                            horas_val = 0.0

                        # 🔴 AQUI SE LIMITA: máximo 8 horas por día
                        if horas_val > 8.0:
                            horas_val = 8.0

                        horas_presentes = f"{horas_val:.2f}"

                    # Registro para historial
                    historial_dicts.append({
                        'fecha': fecha,
                        'hora_entrada': hora_entrada,
                        'hora_salida': hora_salida,
                        'horas_presentes': horas_presentes
                    })

                    # Acumular totales
                    total_horas_periodo += horas_val

                    # Recolectar para horas frecuentes
                    if hora_entrada != '--:--':
                        horas_entrada.append(hora_entrada)
                    if hora_salida != '--:--':
                        horas_salida.append(hora_salida)

                    # Calcular semana y mes para promedios, usando la fecha real
                    if fecha_raw:
                        try:
                            # fecha_raw suele venir como date/datetime
                            if isinstance(fecha_raw, str):
                                # Por si acaso viene como cadena
                                try:
                                    fecha_dt = datetime.strptime(fecha_raw, '%Y-%m-%d')
                                except ValueError:
                                    fecha_dt = datetime.strptime(fecha_raw, '%Y-%m-%d %H:%M:%S')
                            else:
                                # date/datetime
                                if hasattr(fecha_raw, 'date'):
                                    fecha_dt = datetime.combine(fecha_raw, datetime.min.time()) \
                                        if not hasattr(fecha_raw, 'hour') else fecha_raw
                                else:
                                    # fallback
                                    fecha_dt = datetime.strptime(str(fecha_raw), '%Y-%m-%d')

                            semana = f"{fecha_dt.year}-W{fecha_dt.isocalendar()[1]}"
                            mes_clave = f"{fecha_dt.year}-{fecha_dt.month:02d}"

                            # usar horas topadas
                            horas_semanales[semana] = horas_semanales.get(semana, 0.0) + horas_val
                            horas_mensuales[mes_clave] = horas_mensuales.get(mes_clave, 0.0) + horas_val

                        except Exception as e:
                            print(f"Error al procesar fecha para semana/mes: {e}")
                            continue

                except Exception as e:
                    print(f"Error al procesar registro: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            # Calcular promedios (con horas ya topadas)
            promedio_semanal = sum(horas_semanales.values()) / len(horas_semanales) if horas_semanales else 0.0
            promedio_mensual = sum(horas_mensuales.values()) / len(horas_mensuales) if horas_mensuales else 0.0

            # Hora más frecuente
            def hora_mas_frecuente(lista_horas):
                if not lista_horas:
                    return '--:--'
                conteo = {}
                for h in lista_horas:
                    conteo[h] = conteo.get(h, 0) + 1
                return max(conteo.items(), key=lambda x: x[1])[0]

            hora_entrada_frec = hora_mas_frecuente(horas_entrada)
            hora_salida_frec = hora_mas_frecuente(horas_salida)

            return {
                'promedio_semanal': f"{promedio_semanal:.2f}",
                'promedio_mensual': f"{promedio_mensual:.2f}",
                'total_horas_periodo': f"{total_horas_periodo:.2f}",
                'total_horas_mes': f"{total_horas_periodo:.2f}",  # por compatibilidad con tus PDFs
                'hora_entrada_frecuente': hora_entrada_frec,
                'hora_salida_frecuente': hora_salida_frec,
                'historial': historial_dicts
            }

        except Exception as e:
            print(f"Error al obtener estadísticas del estudiante: {e}")
            import traceback
            traceback.print_exc()
            return {
                'promedio_semanal': '0.00',
                'promedio_mensual': '0.00',
                'total_horas_periodo': '0.00',
                'total_horas_mes': '0.00',
                'hora_entrada_frecuente': '--:--',
                'hora_salida_frecuente': '--:--',
                'historial': []
            }



    # ===== CATALOGO: GENERACIONES =====
    def obtener_generaciones(self) -> List[Dict[str, Union[int, str]]]:
        try:
            """Obtiene todas las generaciones"""
            self.cursor.execute("SELECT id, nombre FROM generaciones")
            return [{'id': row[0], 'nombre': row[1]} for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error al obtener generaciones: {e}")
            return []

    def crear_generacion(self, nombre: str) -> int:
        """Crea una nueva generación"""
        self.cursor.execute(
            "INSERT INTO generaciones (nombre) VALUES (%s)",
            (nombre,)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def actualizar_generacion(self, generacion_id: int, nombre: str) -> bool:
        """Actualiza una generación existente"""
        try:
            self.cursor.execute(
                "UPDATE generaciones SET nombre = %s WHERE id = %s",
                (nombre, generacion_id)
            )
            self.db.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            raise e

    def eliminar_generacion(self, generacion_id: int) -> bool:
        """Elimina una generación"""
        try:
            # Eliminamos la generación
            self.cursor.execute(
                "DELETE FROM generaciones WHERE id = %s",
                (generacion_id,)
            )
            self.db.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            raise e

    # ===== CATALOGO: ÁREAS DE CONOCIMIENTO =====
    def obtener_areas_conocimiento(self) -> List[Dict[str, Union[int, str]]]:
        try:
            """Obtiene todas las áreas de conocimiento"""
            self.cursor.execute("SELECT id, nombre FROM areas_conocimiento ORDER BY nombre")
            return [{'id': row[0], 'nombre': row[1]} for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Error al obtener áreas de conocimiento: {e}")
            return []

    def crear_area_conocimiento(self, nombre: str) -> int:
        """Crea una nueva área de conocimiento"""
        self.cursor.execute(
            "INSERT INTO areas_conocimiento (nombre) VALUES (%s)",
            (nombre,)
        )
        self.db.commit()
        return self.cursor.lastrowid

    def actualizar_area_conocimiento(self, area_id: int, nombre: str) -> bool:
        """Actualiza un área de conocimiento existente"""
        try:
            self.cursor.execute(
                "UPDATE areas_conocimiento SET nombre = %s WHERE id = %s",
                (nombre, area_id)
            )
            self.db.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            raise e

    def eliminar_area_conocimiento(self, area_id: int) -> bool:
        """Elimina un área de conocimiento"""
        try:
            # Eliminamos el área
            self.cursor.execute(
                "DELETE FROM areas_conocimiento WHERE id = %s",
                (area_id,)
            )
            self.db.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            self.db.rollback()
            raise e

    def obtener_informacion_asesores(self):
        try:
            query = "SELECT id, employee_number, name, phone, email FROM teachers ORDER BY id"
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()
            # Convertir tuplas a diccionarios manualmente
            asesores = []
            for row in resultados:
                asesor = {
                    'id': row[0],
                    'employee_number': row[1],
                    'name': row[2],
                    'phone': row[3],
                    'email': row[4]
                }
                asesores.append(asesor)
            
            return asesores
        except Exception as e:
            print(f"Error al obtener información de asesores: {str(e)}")
            return []

    def crear_asesor(self, datos_asesor):
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """INSERT INTO teachers (employee_number, name, phone, email, created_at) 
                    VALUES (%s, %s, %s, %s, %s)"""
            valores = (datos_asesor['employee_number'], datos_asesor['name'], 
                    datos_asesor['phone'], datos_asesor['email'], fecha_actual)
            self.cursor.execute(query, valores)
            self.db.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error al crear asesor: {str(e)}")
            return None

    def actualizar_asesor(self, asesor_id, datos_asesor):
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """UPDATE teachers SET employee_number = %s, name = %s, 
                phone = %s, email = %s, updated_at = %s WHERE id = %s"""
            valores = (datos_asesor['employee_number'], datos_asesor['name'],
                datos_asesor['phone'], datos_asesor['email'], fecha_actual, asesor_id)
            self.cursor.execute(query, valores)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar asesor: {str(e)}")
            return False
        

    def eliminar_asesor(self, asesor_id):
        query = "DELETE FROM teachers WHERE id = %s"
        try:
            self.cursor.execute(query, (asesor_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar asesor: {str(e)}")
            return False
 

    def obtener_estudiantes_por_generacion(self, nombre_generacion: str):
        """
        Devuelve [(id, email, matricula, nombre, ape_p, ape_m, generacion,
                asesor, area, carrera, asesor_email), ...]
        filtrando por el NOMBRE de la generación (ej. 'GTU2025').

        Soporta:
        - esquema actual: alumnos.generacion (VARCHAR) - campo directo
        - esquema futuro: alumnos.generacion_id + tabla generaciones (si se migra)
        """
        try:
            query = """
                SELECT 
                    a.id, 
                    a.email, 
                    a.matricula, 
                    a.nombre, 
                    a.apellido_paterno, 
                    a.apellido_materno,
                    a.generacion AS generacion, 
                    a.asesor, 
                    a.area_conocimiento AS area_conocimiento,
                    a.carrera AS carrera,
                    t.email AS asesor_email
                FROM alumnos a
                LEFT JOIN teachers t ON t.id = a.asesor_id
                WHERE a.generacion = %s
                ORDER BY a.apellido_paterno, a.apellido_materno, a.nombre;
            """
            self.cursor.execute(query, (nombre_generacion,))
            return self.cursor.fetchall()
        except Exception as e:
            print("Error al obtener estudiantes por generación:", e)
            import traceback
            traceback.print_exc()
            return []

   
    def obtener_generaciones_distintas_en_alumnos(self):
        try:
            q = """
                SELECT DISTINCT generacion
                FROM alumnos
                WHERE generacion IS NOT NULL AND TRIM(generacion) <> ''
                ORDER BY generacion
            """
            self.cursor.execute(q)
            # devuelve lista de strings
            return [r[0] for r in self.cursor.fetchall()]
        except Exception as e:
            print("Error obtener_generaciones_distintas_en_alumnos:", e)
            return []
        
    def existe_alumno_por_matricula(self, matricula: str) -> bool:
        self.cursor.execute("SELECT 1 FROM alumnos WHERE matricula=%s LIMIT 1", (matricula,))
        return self.cursor.fetchone() is not None
    
    #BUSCADOR 
    
    def buscar_estudiantes(self, query, limit=20):
        try:
            sql = """
                SELECT a.id, a.email, a.matricula, a.nombre, a.apellido_paterno, a.apellido_materno,
                    a.generacion,
                    COALESCE(t.name, a.asesor) AS asesor,
                    a.area_conocimiento,
                    a.carrera
                FROM alumnos a
                LEFT JOIN teachers t ON a.asesor_id = t.id
                WHERE a.nombre LIKE %s
                OR a.apellido_paterno LIKE %s
                OR a.apellido_materno LIKE %s
                OR CONCAT(a.nombre,' ',a.apellido_paterno,' ',a.apellido_materno) LIKE %s
                OR a.matricula LIKE %s
                OR a.email LIKE %s
                LIMIT %s
            """
            like = f"%{query}%"
            self.cursor.execute(sql, (like, like, like, like, like, like, limit))
            rows = self.cursor.fetchall()
            if not rows:
                return []
            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "email": row[1],
                    "matricula": row[2],
                    "nombre": row[3],
                    "apellido_p": row[4],
                    "apellido_m": row[5],
                    "generacion": row[6],
                    "asesor": row[7],
                    "area_conocimiento": row[8],
                    "carrera": row[9],
                })
            return result
        except Exception as e:
            print(f"Error al buscar estudiantes: {e}")
            return []


 