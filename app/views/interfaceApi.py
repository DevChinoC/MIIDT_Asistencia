import ctypes
from ctypes import wintypes
from typing import Optional, Callable
from .types import DataBlobPointer, DATA_BLOB


class InterfaceApi:
    """Clase principal para manejar las interfaces biométricas"""
    
    # Constantes
    DP_ENROLLMENT_ADD = 0
    DP_ENROLLMENT_DELETE = 1
    
    def __init__(self, dll_path: str = "C:\\Windows\\System32\\DPFPUI.dll"):
        """
        Inicializa el sistema biométrico
        :param dll_path: Ruta a la DLL de la interfaz de usuario
        """
        self._load_dll(dll_path)
        self._setup_callbacks()
        self._configure_functions()
        

    def _load_dll(self, dll_path: str):
        """Carga la DLL y verifica su disponibilidad"""
        try:
            self.dpfpui = ctypes.WinDLL(dll_path)    # Interfaz de usuario
            self.dpfpapi = ctypes.WinDLL("C:\\Windows\\System32\\DPFPApi.dll")  # API principal
            self.dphmatch = ctypes.WinDLL("C:\\Windows\\System32\\dpHMatch.dll")  # Comparación
        except OSError as e:
            raise RuntimeError(f"No se pudo cargar la DLL: {e}") from e


    def _init_matching(self):
        """Inicializa el módulo de comparación de huellas"""
        self.dpfpapi.DPFPInit()
        self.dphmatch.MC_init()
        
        # Crear contexto de comparación
        self.mc_context = ctypes.c_void_p()
        self.dphmatch.MC_createContext(ctypes.byref(self.mc_context))
        
        # Configurar nivel de seguridad (FAR - False Accept Rate)
        target_far = ctypes.c_double(0.001)  # 0.1% de tasa de falsos aceptados
        self.dphmatch.MC_setSecurityLevel(self.mc_context, target_far)


    def _setup_callbacks(self):
        """Configura los callbacks como métodos de instancia"""
        self._enrollment_callback = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, 
            wintypes.HWND, 
            ctypes.c_int, 
            ctypes.c_uint, 
            ctypes.POINTER(DATA_BLOB), 
            ctypes.c_void_p
        )(self._handle_enrollment)
        
        self._verification_callback = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, 
            wintypes.HWND, 
            ctypes.POINTER(DATA_BLOB), 
            ctypes.c_void_p
        )(self._handle_verification)


    def _configure_functions(self):
        """Configura las funciones de la DLL con sus tipos de argumentos"""
        # Configuración de DPEnrollUI
        self.dpfpui.DPEnrollUI.restype = ctypes.HRESULT
        self.dpfpui.DPEnrollUI.argtypes = [
            wintypes.HWND,
            ctypes.c_ushort,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.c_void_p,
            ctypes.c_void_p
        ]
        # Configuración de DPVerifyUI
        self.dpfpui.DPVerifyUI.restype = ctypes.HRESULT
        self.dpfpui.DPVerifyUI.argtypes = [
            wintypes.HWND,
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            wintypes.HBITMAP,
            ctypes.c_void_p
        ]


    def register_fingerprint(self, 
                           max_fingers: int = 10,
                           on_enroll: Optional[Callable] = None,
                           on_delete: Optional[Callable] = None) -> bool:
        """
        Muestra la interfaz de registro de huellas
        :param max_fingers: Máximo número de dedos a registrar
        :param on_enroll: Callback cuando se registra una huella
        :param on_delete: Callback cuando se elimina una huella
        :return: True si la operación fue exitosa
        """
        self.on_enroll_callback = on_enroll
        self.on_delete_callback = on_delete
        
        enrolled_mask = ctypes.c_ulong(0)
        result = self.dpfpui.DPEnrollUI(
            None,
            max_fingers,
            ctypes.byref(enrolled_mask),
            self._enrollment_callback,
            None
        ) 
        return result == 0  # S_OK


    def verificar_huella_salida(self, huella_template):
        """
        Muestra la interfaz de verificación de huellas
        :param huella_template: Template de huella a verificar en formato base64
        :return: True si la verificación fue exitosa, False en caso contrario
        """
        self.attempts = 0
        self.max_attempts = 3
        verification_result = False
        # Inicializar el sistema de coincidencia si no está inicializado
        if not hasattr(self, 'mc_context'):
            self._init_matching()

        def on_verify(feature_data: bytes) -> bool:
            nonlocal verification_result
            try:
                # Decodificar el template de la base de datos
                # template_data = base64.b64decode(huella_template)
                
                # Comparar los features con el template
                if self._compare_features_with_template(feature_data, huella_template):
                    verification_result = True
                     # Éxito - Mostrar UI personalizada
                    if hasattr(self, 'on_success'):
                        self.on_success()
                    return True  # Coincidencia encontrada
                else:
                    self.attempts += 1
                    if self.attempts >= self.max_attempts:
                        # Máximo de intentos alcanzado
                        if hasattr(self, 'on_max_attempts'):
                            self.on_max_attempts()
                        return False  # Esto cerrará la ventana de verificación
                    else:
                        # Mostrar mensaje de reintento
                        if hasattr(self, 'on_retry'):
                            remaining = self.max_attempts - self.attempts
                            self.on_retry(remaining)
                        return False  # No hubo coincidencias
            except Exception as e:
                print(f"Error en verificación de huella: {e}")
                import traceback
                traceback.print_exc()
                return False
        # Configurar el callback de verificación
        self.on_verify_callback = on_verify

        try:
            # Llamar a la interfaz de verificación
            result = self.dpfpui.DPVerifyUI(
                None,  # hWnd padre
                self._verification_callback,  # Callback
                "Verificación de Huella",  # Título
                "Coloque su dedo en el lector",  # Instrucción
                None,  # hBitmap (opcional)
                None   # User data (no se usa aquí, usamos el callback de instancia)
            )
            if result == 0x800704C7:  # El usuario canceló la operación
                print("Operación cancelada por el usuario")
                return False
            return verification_result if result == 0 else False
        except OSError as e:
            if e.winerror == -2147023673:  # Usuario canceló la operación
                print("Operación cancelada por el usuario")
                return False
            print(f"Error al iniciar la verificación: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"Error inesperado durante la verificación: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_fingerprint(self, estudiantes):
        """
        Verifica una huella contra estudiantes (acepta dicts o tuplas)
        Devuelve el estudiante encontrado como dict o None.
        """
        self.attempts = 0
        self.max_attempts = 3
        matching_student = None

        # Inicializar Matching si no está listo
        if not hasattr(self, 'mc_context'):
            self._init_matching()

        def normalizar(est):
            """Convierte tuplas a diccionarios y deja dicts intactos."""
            if isinstance(est, dict):
                return est

            if isinstance(est, (tuple, list)) and len(est) >= 2:
                # La huella SIEMPRE se toma del último elemento de la tupla
                return {
                    "id": est[0],
                    "matricula": est[1] if len(est) > 1 else "",
                    "nombre": est[2] if len(est) > 2 else "",
                    "apellido_p": est[3] if len(est) > 3 else "",
                    "apellido_m": est[4] if len(est) > 4 else "",
                    "huella_digital": est[-1],   # ← IMPORTANTE
                }

            return None

        def on_verify(feature_data: bytes) -> bool:
            nonlocal matching_student
            try:
                print(f"[DEBUG] Huella capturada, tamaño={len(feature_data)} bytes")

                for est in estudiantes:
                    est_dict = normalizar(est)
                    if not est_dict:
                        continue

                    huella = est_dict.get("huella_digital")
                    if not huella:
                        continue

                    print(f"[DEBUG] Comparando con alumno ID={est_dict['id']}")

                    if self._compare_features_with_template(feature_data, huella):
                        matching_student = est_dict
                        print(f"[DEBUG] Coincidencia encontrada con ID={est_dict['id']}")

                        if hasattr(self, 'on_success'):
                            self.on_success()

                        return True

                # No hubo coincidencia
                self.attempts += 1

                if self.attempts >= self.max_attempts:
                    print("[DEBUG] No hubo coincidencia tras 3 intentos.")
                    if hasattr(self, 'on_max_attempts'):
                        self.on_max_attempts()
                    return False

                else:
                    remaining = self.max_attempts - self.attempts
                    print(f"[DEBUG] Reintentando... intentos restantes: {remaining}")

                    if hasattr(self, 'on_retry'):
                        self.on_retry(remaining)

                    return False

            except Exception as e:
                print(f"Error en verificación de huella: {e}")
                import traceback
                traceback.print_exc()
                return False

        # Asignar callback
        self.on_verify_callback = on_verify

        try:
            result = self.dpfpui.DPVerifyUI(
                None,
                self._verification_callback,
                "Verificación de Huella",
                "Coloque su dedo en el lector",
                None,
                None
            )

            print(f"[DEBUG] Resultado DPVerifyUI: {hex(result)}")

            # Resultado exitoso = 0
            if result == 0:
                return matching_student

            # Cualquier otro código = no match o cancelado
            print("[DEBUG] Verificación finalizada sin coincidencia.")
            return None

        except OSError as e:
            if e.winerror == -2147023673:
                print("[DEBUG] Usuario cerró la ventana del lector.")
                return None

            print(f"Error al iniciar la verificación: {e}")
            import traceback
            traceback.print_exc()
            return None

        except Exception as e:
            print(f"Error inesperado durante la verificación: {e}")
            import traceback
            traceback.print_exc()
            return None


    def _handle_enrollment(self, 
                         hWnd: int, 
                         action: int, 
                         finger_index: int, 
                         p_template: DataBlobPointer,  # Usamos el nuevo tipo 
                         user_data: int) -> int:
        """Manejador interno para eventos de registro"""
        if action == self.DP_ENROLLMENT_ADD and p_template:
            template_data = bytes(p_template.contents.pbData[:p_template.contents.cbData])
            if self.on_enroll_callback:
                self.on_enroll_callback(finger_index, template_data) 
        elif action == self.DP_ENROLLMENT_DELETE:
            if self.on_delete_callback:
                self.on_delete_callback(finger_index)
        return 0  # S_OK


    def _handle_verification(self, hWnd: int, p_feature_set: ctypes.POINTER(DATA_BLOB), 
                           user_data: int) -> int:
        """Manejador interno para eventos de verificación"""
        if p_feature_set and hasattr(self, 'on_verify_callback') and callable(self.on_verify_callback):
            try:
                feature_data = bytes(p_feature_set.contents.pbData[:p_feature_set.contents.cbData])
                is_valid = self.on_verify_callback(feature_data)
                return 0 if is_valid else 0x800704c7  # S_OK o error
            except Exception as e:
                print(f"Error en el callback de verificación: {e}")
                return 0x800704c7  # Error por defecto
        return 0x800704c7  # Error por defecto


    def _compare_features_with_template(self, feature_data: bytes, template_data: bytes) -> bool:
        """Compara los features capturados con un template almacenado"""
        # Convertir los datos a buffers compatibles con el SDK
        feature_buffer = (ctypes.c_ubyte * len(feature_data))(*feature_data)
        template_buffer = (ctypes.c_ubyte * len(template_data))(*template_data)
        
        feature_ptr = ctypes.cast(feature_buffer, ctypes.POINTER(ctypes.c_ubyte))
        template_ptr = ctypes.cast(template_buffer, ctypes.POINTER(ctypes.c_ubyte))
        
        # Variables para resultados
        achieved_far = ctypes.c_double()
        is_match = ctypes.c_int()
        
        # Llamar a la función de comparación del SDK
        result = self.dphmatch.MC_verifyFeaturesEx(
            self.mc_context,
            len(template_data),
            template_ptr,
            len(feature_data),
            feature_ptr,
            0,  # reserved
            None,  # reserved
            None,  # reserved
            None,  # reserved
            ctypes.byref(achieved_far),
            ctypes.byref(is_match)
        )
        
        if result != 0:  # Si no es FT_OK
            print(f"Error en comparación: {result}")
            return False
        print(is_match.value)
        return bool(is_match.value)
