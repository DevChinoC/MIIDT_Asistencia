from config.conexionBD import obtenerConexion
from app.models.modelo import Modelo
from app.views.vista import VentanaPrincipal
from app.controllers.controlador import Controlador
from app.views.interfaceApi import InterfaceApi

def main():
    db = obtenerConexion()
    if not db:
        print("No se pudo conectar a la base de datos.")
        return
    
    modelo = Modelo(db)
    ui_dp = InterfaceApi()
    vista = VentanaPrincipal(ui_dp)
    controlador = Controlador(modelo, vista)
    vista.mostrar()
    
    db.close()

    
if __name__ == "__main__":
    main()
    