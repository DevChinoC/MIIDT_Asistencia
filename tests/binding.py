import ctypes

# Ruta completa a la DLL
dll_path = "C:\\Windows\\System32\\dpHFtrEx.dll"

# Cargar la DLL
dpHFtrEx = ctypes.WinDLL(dll_path)

# Llamar a la función FX_init
res = dpHFtrEx.FX_init()
print("Resultado de FX_init:", res)
