import mysql.connector
import os
import sys
from dotenv import load_dotenv

# ===========================================================
# 1. Detección del directorio raíz del proyecto
#    → Modo normal (python main.py)
#    → Modo PyInstaller (.exe)
# ===========================================================

def get_base_dir():
    # Si está congelado en un .exe de PyInstaller:
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS       # Carpeta temporal donde PyInstaller extrae los archivos
    else:
        # Estamos ejecutando el proyecto como código fuente
        # __file__ = MIIDT_ASISTENCIA/config/conexionBD.py
        # subimos 1 nivel -> config/
        # subimos 1 nivel -> MIIDT_ASISTENCIA/
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_dir()

# ===========================================================
# 2. Construir la ruta CORRECTA del .env
# ===========================================================
ENV_PATH = os.path.join(BASE_DIR, "config", ".env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"[ADVERTENCIA] No se encontró el archivo .env en: {ENV_PATH}")

# ===========================================================
# 3. Función para obtener conexión MySQL
# ===========================================================

def obtenerConexion():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("HOST", "localhost"),
            port=int(os.getenv("PORT", "3306")),
            user=os.getenv("USER", ""),
            password=os.getenv("PASSWORD", ""),
            database=os.getenv("DB_NAME", "asistencia_biometrica"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            use_pure=True
        )

        if conexion.is_connected():
            print("Conexión exitosa a la base de datos")

        return conexion

    except mysql.connector.Error as err:
        print(f"[ERROR] Error de conexión MySQL: {err}")
        return None

    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return None
