import ctypes
from ctypes import wintypes

# 1. Cargar la DLL de la interfaz de usuario
dpfpui = ctypes.WinDLL("C:\\Windows\\System32\\DPFPUI.dll")  # Asegúrate que esté en el PATH

# 2. Definir estructuras y tipos necesarios
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), 
                ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

# 3. Definir constantes
DP_ENROLLMENT_ADD = 0
DP_ENROLLMENT_DELETE = 1

# 4. Configurar los callbacks (funciones de retorno)
@ctypes.WINFUNCTYPE(ctypes.HRESULT, wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.POINTER(DATA_BLOB), ctypes.c_void_p)
def enrollment_callback(hWnd, action, finger_index, p_template, user_data):
    if action == DP_ENROLLMENT_ADD:
        template_data = bytes(p_template.contents.pbData[:p_template.contents.cbData])
        print(f"✅ Huella {finger_index} registrada. Tamaño:", len(template_data))
        print("Datos de la huella:", type(template_data), template_data)
        # Aquí guardarías en tu base de datos
    elif action == DP_ENROLLMENT_DELETE:
        print(f"❌ Huella {finger_index} eliminada")
    return 0  # S_OK

@ctypes.WINFUNCTYPE(ctypes.HRESULT, wintypes.HWND, ctypes.POINTER(DATA_BLOB), ctypes.c_void_p)
def verification_callback(hWnd, p_feature_set, user_data):
    feature_data = bytes(p_feature_set.contents.pbData[:p_feature_set.contents.cbData])
    print("🔒 Huella recibida para verificación")
    # Aquí compararías con tus registros
    return 0  # S_OK si coincide, otro valor si no

# 5. Configurar las funciones de la UI
dpfpui.DPEnrollUI.restype = ctypes.HRESULT
dpfpui.DPEnrollUI.argtypes = [
    wintypes.HWND,          # Ventana padre (None para consola)
    ctypes.c_ushort,        # Máximo de dedos a registrar
    ctypes.POINTER(ctypes.c_ulong),  # Máscara de dedos registrados
    ctypes.c_void_p,        # Callback
    ctypes.c_void_p         # Datos de usuario
]

dpfpui.DPVerifyUI.restype = ctypes.HRESULT
dpfpui.DPVerifyUI.argtypes = [
    wintypes.HWND,          # Ventana padre
    ctypes.c_void_p,        # Callback
    ctypes.c_wchar_p,       # Título
    ctypes.c_wchar_p,       # Texto descriptivo
    wintypes.HBITMAP,       # Imagen de banner (None)
    ctypes.c_void_p         # Datos de usuario
]

# 6. Función para mostrar la interfaz de registro
def registrar_huella():
    enrolled_mask = ctypes.c_ulong(0)
    print("🖐️ Mostrando interfaz de registro...")
    result = dpfpui.DPEnrollUI(
        None,               # Sin ventana padre
        10,                 # Máximo 10 dedos
        ctypes.byref(enrolled_mask),
        enrollment_callback, # Nuestra función
        None                # Sin datos extra
    )
    print("Resultado del registro:", result)

# 7. Función para mostrar la interfaz de verificación
def verificar_huella():
    print("🔍 Mostrando interfaz de verificación...")
    result = dpfpui.DPVerifyUI(
        None,               # Sin ventana padre
        verification_callback,
        "Verificación de Huella",  # Título
        "Coloque su dedo en el lector",  # Instrucciones
        None,               # Sin imagen
        None                # Sin datos extra
    )
    print("Resultado de verificación:", result)

# 8. Ejemplo de uso
if __name__ == "__main__":
    print("1. Registrar huella")
    print("2. Verificar huella")
    opcion = input("Seleccione una opción: ")
    
    if opcion == "1":
        registrar_huella()
    elif opcion == "2":
        verificar_huella()