import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")
# Función para obtener una conexión a la base de datos
def obtenerConexion():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("HOST","localhost"),
            port = int(os.getenv("PORT", "3306")),
            user=os.getenv("USER",""),
            password=os.getenv("PASSWORD",""),
            database=os.getenv("DB_NAME","asistencia_biometrica"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            use_pure=True
            # ssl_disabled=False  # Mejor sería configurar SSL correctamente
        )

        if conexion.is_connected():
            print("Conexión exitosa a la base de datos")
    
        return conexion
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None