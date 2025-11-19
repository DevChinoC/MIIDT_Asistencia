class Controlador:
    def __init__(self, modelo, vista):
        self.modelo = modelo
        self.vista = vista
        # Conectar eventos de la vista con métodos del controlador
        self.vista.set_controlador(self)

    def registrar_estudiante(
    self, email, matricula, nombre, apellido_p, apellido_m,
    huella_digital, generacion, area_conocimiento, carrera,
    asesor, id_asesor
    ):
        """
        Registra un estudiante nuevo, validando duplicados y conservando ceros en la matrícula.
        """
        try:
            matricula = str(matricula).strip()  # conserva ceros a la izquierda

            # Verificar duplicado antes de insertar
            existe = self.modelo.existe_alumno_por_matricula(matricula)
            if existe:
                print(f"⚠️ Matrícula duplicada detectada: {matricula}")
                return "duplicado"

            resultado = self.modelo.registrar_estudiante(
                email, matricula, nombre, apellido_p, apellido_m,
                huella_digital, generacion, area_conocimiento, carrera,
                asesor, id_asesor
            )

            if resultado == "duplicado":
                print(f"⚠️ Matrícula duplicada detectada (modelo): {matricula}")
                return "duplicado"
            return resultado
        except Exception as e:
            print(f"Error en controlador.registrar_estudiante: {e}")
            return False

    def editar_estudiante(
    self, estudiante_id, email, matricula, nombre, apellido_p, apellido_m,
    huella_digital, generacion, area_conocimiento, carrera,
    asesor_nombre, id_asesor
    ):
        """
        Edita datos del estudiante conservando ceros en la matrícula.
        """
        try:
            matricula = str(matricula).strip()  # conserva ceros
            return self.modelo.editar_estudiante(
                estudiante_id, email, matricula, nombre, apellido_p, apellido_m,
                huella_digital, generacion, area_conocimiento, carrera,
                asesor_nombre, id_asesor
            )
        except Exception as e:
            print(f"Error en controlador.editar_estudiante: {e}")
            return False

    def eliminar_estudiante(self, estudiante_id):
        return self.modelo.eliminar_estudiante(estudiante_id)

    def obtener_huella_digital(self, id):
        huella_digital = self.modelo.get_huella_digital(id)
        return huella_digital

    def registrar_asistencia(self, estudiante_id):
        return self.modelo.registrar_asistencia(estudiante_id)

    def obtener_asesores(self):
        return self.modelo.obtener_asesores()

    def obtener_asistencias_hoy(self):
        return self.modelo.obtener_asistencias_hoy()
        
    def registrar_salida(self, registro_id):
        return self.modelo.registrar_salida(registro_id)
        
    def obtener_estudiante_por_registro(self, registro_id):
        """Obtiene el ID del estudiante asociado a un registro de asistencia"""
        return self.modelo.obtener_estudiante_por_registro(registro_id)
        
    def obtener_huella_estudiante(self, estudiante_id):
        """Obtiene la plantilla de huella del estudiante"""
        return self.modelo.obtener_huella_estudiante(estudiante_id)
        
    def verificar_asistencia_existente(self, estudiante_id):
        """
        Verifica si un estudiante ya tiene un registro de asistencia para el día actual
        
        Args:
            estudiante_id (int): ID del estudiante a verificar
            
        Returns:
            bool: True si ya existe un registro de asistencia para hoy, False en caso contrario
        """
        return self.modelo.verificar_asistencia_existente(estudiante_id)
        
    def obtener_asistencia_por_id(self, registro_id):
        """Obtiene los detalles de una asistencia por su ID"""
        return self.modelo.obtener_asistencia_por_id(registro_id)
        
    def obtener_estudiantes_para_asistencia(self, mostrar_en_vista=True):
        """
        Obtiene la lista de todos los estudiantes
        Args:
            mostrar_en_vista (bool): Si es True, actualiza la vista con los estudiantes
        Returns:
            list: Lista de estudiantes
        """
        estudiantes = self.modelo.obtener_todos_los_estudiantes()
        # if mostrar_en_vista:
        #     self.vista.mostrar_estudiantes(estudiantes)
        return estudiantes

    def obtener_estudiantes_registrados(self):
        """
        Obtiene la lista de todos los estudiantes
        Returns:
            list: Lista de estudiantes
        """
        estudiantes = self.modelo.obtener_estudiantes_registrados()
        return estudiantes

    def obtener_estudiantes_reportes(self, mostrar_en_vista=True):
        """
        Obtiene la lista de todos los estudiantes para la pestaña de reportes
        Args:
            mostrar_en_vista (bool): Si es True, actualiza la vista con los estudiantes
        Returns:
            list: Lista de estudiantes
        """
        estudiantes = self.modelo.obtener_todos_los_estudiantes_reportes()
        if mostrar_en_vista and hasattr(self.vista, 'mostrar_estudiantes_reportes'):
            self.vista.mostrar_estudiantes_reportes(estudiantes)
        return estudiantes

        
    def obtener_estadisticas_estudiante(self, estudiante_id, mes=None, anio=None, fecha_inicio=None, fecha_fin=None):
        """
        Obtiene las estadísticas de un estudiante
        
        Args:
            estudiante_id (int): ID del estudiante
            mes (int, optional): Mes para filtrar (1-12)
            anio (int, optional): Año para filtrar (ej. 2023)
            
        Returns:
            dict: Diccionario con las estadísticas del estudiante
        """
        try:
            return self.modelo.obtener_estadisticas_estudiante(estudiante_id, mes, anio, fecha_inicio, fecha_fin)
        except Exception as e:
            print(f"Error en el controlador al obtener estadísticas: {e}")
            return {
                'promedio_semanal': '0.00',
                'promedio_mensual': '0.00',
                'hora_entrada_frecuente': '--:--',
                'hora_salida_frecuente': '--:--',
                'historial': []
            }

    def obtener_asistencias_hoy_completo(self):
        return self.modelo.obtener_asistencias_hoy_completo()

    # ===== MÉTODOS PARA GESTIÓN DE CATÁLOGO =====
    
    # Generaciones
    def obtener_generaciones(self) -> list:
        """Obtiene todas las generaciones"""
        return sorted(self.modelo.obtener_generaciones(), key=lambda x: -x['id'])
        
    def crear_generacion(self, nombre: str) -> int:
        """Crea una nueva generación"""
        return self.modelo.crear_generacion(nombre)
        
    def actualizar_generacion(self, generacion_id: int, nombre: str) -> bool:
        """Actualiza una generación existente"""
        return self.modelo.actualizar_generacion(generacion_id, nombre)
        
    def eliminar_generacion(self, generacion_id: int) -> bool:
        """Elimina una generación"""
        return self.modelo.eliminar_generacion(generacion_id)
    
    # Áreas de conocimiento
    def obtener_areas_conocimiento(self) -> list:
        """Obtiene todas las áreas de conocimiento"""
        return sorted(self.modelo.obtener_areas_conocimiento(), key=lambda x: -x['id'])
        
    def crear_area_conocimiento(self, nombre: str) -> int:
        """Crea una nueva área de conocimiento"""
        return self.modelo.crear_area_conocimiento(nombre)
        
    def actualizar_area_conocimiento(self, area_id: int, nombre: str) -> bool:
        """Actualiza un área de conocimiento existente"""
        return self.modelo.actualizar_area_conocimiento(area_id, nombre)
        
    def eliminar_area_conocimiento(self, area_id: int) -> bool:
        """Elimina un área de conocimiento"""
        return self.modelo.eliminar_area_conocimiento(area_id)
        
    # En tu controlador (controlador.py)
    def obtener_informacion_asesores(self):
        return self.modelo.obtener_informacion_asesores()
    
    def crear_asesor(self, datos_asesor):
        return self.modelo.crear_asesor(datos_asesor)
    
    def actualizar_asesor(self, asesor_id, datos_asesor):
        return self.modelo.actualizar_asesor(asesor_id, datos_asesor)
    
    def eliminar_asesor(self, asesor_id):
        return self.modelo.eliminar_asesor(asesor_id)
   
    def obtener_generaciones_seguras(self):
        """
        Intenta sacar generaciones del catálogo; si está vacío,
        usa DISTINCT generacion desde alumnos.
        Devuelve lista de strings.
        """
        gens = self.obtener_generaciones() or []
        nombres = []
        for g in gens:
            if isinstance(g, dict) and "nombre" in g:
                nombres.append(g["nombre"])
            elif isinstance(g, (list, tuple)) and len(g) >= 2:
                nombres.append(g[1])
            elif isinstance(g, str):
                nombres.append(g)
        if not nombres:
            nombres = self.modelo.obtener_generaciones_distintas_en_alumnos() or []
        return nombres

    def obtener_estudiantes_por_generacion(self,generacion_id):
        return self.modelo.obtener_estudiantes_por_generacion(generacion_id)
    def buscar_estudiantes(self, q, limit=20):
        return self.modelo.buscar_estudiantes(q, limit)

