import os,sys
import re
import unicodedata
from tkinter import simpledialog
from dotenv import load_dotenv
import bcrypt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import pandas as pd
from fpdf import FPDF
from pdf2image import convert_from_path
from PIL import Image
from fpdf.enums import AccessPermission  
import traceback, openpyxl, threading, locale
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from datetime import datetime
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import tempfile, os, shutil,time
import socket
import os, unicodedata, re
from datetime import datetime
import locale
import traceback
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, Protection
from openpyxl.utils import get_column_letter
from openpyxl.workbook.protection import WorkbookProtection

# ===========================================================
# Carga de .env y rutas de recursos (normal + PyInstaller)
# ===========================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    # __file__ = app/views/vista.py  -> subimos a la raíz del proyecto
    BASE_DIR = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.abspath(__file__)
                        )
                    )
                )

def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso (iconos, imágenes, etc.),
    funcionando tanto en modo script como en .exe (PyInstaller).
    """
    relative_path = relative_path.replace("/", os.sep)
    return os.path.join(BASE_DIR, relative_path)

ENV_PATH = os.path.join(BASE_DIR, "config", ".env")
load_dotenv(ENV_PATH)
# ===========================================================

try:
    from config.email import send_mail   # util para enviar email
except Exception:
    send_mail = None  # permite que la UI funcione aunque aún no configures email

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env")
load_dotenv(os.path.abspath(ENV_PATH))

class AutocompleteEntry(ttk.Entry):
    """Entry con lista emergente de sugerencias."""
    def __init__(self, master, fetch_callback, on_select, width=40, debounce_ms=200, **kw):
        super().__init__(master, width=width, **kw)
        self.fetch = fetch_callback
        self.on_select = on_select
        self.debounce_ms = debounce_ms
        self._after_id = None
        self._popup = None
        self._list = None
        self._items = []

        # Teclas que NO deben disparar un fetch al soltar (evita reabrir el popup)
        self._ignore_keys = {"Return", "KP_Enter", "Escape"}

        # Eventos principales
        self.bind("<KeyRelease>", self._on_key)      # recibe 'event'
        self.bind("<Down>", self._focus_list)
        self.bind("<Return>", self._enter_key)
        self.bind("<Configure>", lambda e: self._reposition_popup())
        self.bind("<Destroy>",  lambda e: self._destroy_popup())

    # --------- Entradas/teclas ----------
    def _enter_key(self, _):
        # Si hay una sola sugerencia, selecciónala; si no, simplemente cierra el popup.
        if len(self._items) == 1:
            self._choose(0)
        # En cualquier caso, oculta el popup para que no quede el recuadro
        self._hide()

    def _on_key(self, event):
        # No re-dispares fetch al soltar Enter/Escape
        if event and event.keysym in self._ignore_keys:
            return

        if self._after_id:
            self.after_cancel(self._after_id)

        text = (self.get() or "").strip()
        if not text:
            self._hide()
            return

        # Debounce del fetch
        self._after_id = self.after(self.debounce_ms, lambda: self._do_fetch(text))

    # --------- Datos / Popup ----------
    def _do_fetch(self, q):
        try:
            items = self.fetch(q) or []
            self._items = items
            if not items:
                self._hide()
                return
            self._show_list(items)
        except Exception:
            self._hide()

    def _ensure_popup(self):
        if self._popup and self._list:
            return
        self._popup = tk.Toplevel(self)
        self._popup.wm_overrideredirect(True)
        self._popup.attributes("-topmost", True)

        self._list = tk.Listbox(self._popup, height=8, activestyle="dotbox")
        self._list.pack(fill="both", expand=True)

        # Selección por teclado / click
        self._list.bind("<<ListboxSelect>>", self._on_select_list)
        self._list.bind("<Return>",            lambda e: self._choose(self._safe_index()))
        self._list.bind("<ButtonRelease-1>",   lambda e: self._choose(self._safe_index()))
        self._list.bind("<Escape>",            lambda e: self._hide())

    def _show_list(self, items):
        self._ensure_popup()
        self._reposition_popup()

        self._list.delete(0, "end")
        for it in items:
            # Mostrar nombre completo si viene; si no, armar con apellidos
            nombre = it.get('nombre', '') or ''
            ap_p   = it.get('apellido_p', it.get('apellido_paterno', '')) or ''
            ap_m   = it.get('apellido_m', it.get('apellido_materno', '')) or ''
            nombre_vista = (f"{nombre} {ap_p} {ap_m}").strip() or nombre

            id_vista = it.get('matricula') or it.get('email') or ''
            self._list.insert("end", f"{nombre_vista}  ·  {id_vista}")

        self._popup.deiconify()
        self._list.selection_clear(0, "end")
        if self._list.size() > 0:
            self._list.activate(0)

    def _reposition_popup(self):
        if not (self._popup and self._list):
            return
        try:
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self._popup.geometry(f"{self.winfo_width()}x180+{x}+{y}")
        except Exception:
            # Si el widget aún no tiene geometría válida
            pass

    # --------- Listbox helpers ----------
    def _focus_list(self, _):
        if self._popup and self._list and self._list.size() > 0:
            self._list.focus_set()
            self._list.selection_set(0)

    def _on_select_list(self, _):
        idx = self._safe_index()
        if idx is not None:
            self._choose(idx)

    def _safe_index(self):
        if not (self._list and self._list.curselection()):
            return None
        return self._list.curselection()[0]

    def _choose(self, idx):
        if idx is None or not (0 <= idx < len(self._items)):
            self._hide()
            return
        item = self._items[idx]
        # Autorellena el entry con el nombre visible
        nombre = item.get('nombre', '') or ''
        ap_p   = item.get('apellido_p', item.get('apellido_paterno', '')) or ''
        ap_m   = item.get('apellido_m', item.get('apellido_materno', '')) or ''
        self.delete(0, "end")
        self.insert(0, f"{nombre} {ap_p} {ap_m}".strip())
        # Oculta popup y vuelve el foco al Entry
        self._hide()
        self.focus_set()
        # Notifica a la vista
        if self.on_select:
            self.on_select(item)

    def _hide(self):
        if self._popup:
            try:
                self._popup.withdraw()
            except Exception:
                pass

    def close_popup(self):
        """Cierra manualmente el popup (para usar desde la vista)."""
        self._hide()

    def _destroy_popup(self):
        # Llamado cuando el Entry se destruye
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None
        self._list = None

class VentanaPrincipal:
    def __init__(self, interface_api):
        self.ventana = tk.Tk()
        self.ventana.title("Sistema de Asistencia - Huella Dactilar")
        self.ventana.geometry("1100x700")
        self.ventana.config(bg="lightblue")
        # self.ventana.iconbitmap("public/static/icons/huella-dactilar.ico")  # Cambia la ruta por tu archivo .ico
        
        # Inicializar atributos para manejar estudiantes
        self.lista_estudiantes = []
        self.estudiantes = []
        self.todos_estudiantes = []  # Lista de nombres completos para búsqueda
        
        self._crear_barra_navigation()
        self.interface_api = interface_api  # Guarda la instancia de la API de interfaz
        self.controlador = None  # Inicializa el atributo controlador
        self._admin_logged = False
        self._admin_user = (os.getenv("ADMIN_USER") or "").strip()
        self._admin_pass_hash = (os.getenv("ADMIN_PASS_HASH") or "").strip()
            
    def _get_tk_parent(self):
        """Devuelve el widget padre adecuado para Toplevel."""
        import tkinter as tk
        # Intenta atributos comunes que suelen tener la ventana raíz
        for attr in ("root", "master", "ventana", "window", "_root", "_master", "raiz"):
            if hasattr(self, attr):
                parent = getattr(self, attr)
                if parent is not None:
                    try:
                        # Verifica que sea un widget válido
                        parent.winfo_exists()
                        return parent
                    except Exception:
                        pass
        # Si no hay ninguno, usa el root global (si existe) o créalo
        return tk._get_default_root() or tk.Tk()

    def set_controlador(self, controlador):
        self.controlador = controlador
        # Cargar estudiantes después de configurar el controlador
        if hasattr(self, 'frame_estudiantes'):
            self._cargar_estudiantes_en_vista()
        
        # Si ya existe el frame de catálogo, actualizar sus datos
        if hasattr(self, 'frame4') and hasattr(self, 'notebook'):
            # Destruir el contenido anterior del frame4
            for widget in self.frame4.winfo_children():
                widget.destroy()
            # Volver a crear el contenido del catálogo
            self._contenido_catalogo(self.frame4)
        
    def _configurar_scroll_con_rueda(self, canvas, scrollable_frame):
        # Configurar función de scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
        # Bindear al canvas y al frame
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    
        # Bindear a todos los widgets hijos recursivamente
        def _bind_recursivo(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_recursivo(child)
    
        _bind_recursivo(scrollable_frame)
    
        # Asegurar foco
        canvas.bind("<Enter>", lambda e: canvas.focus_set())
    
        return _on_mousewheel

    def _cargar_icono(self, icon_path, size=(16, 16)):
        """Carga y redimensiona un ícono desde un archivo (soporta .exe y modo normal)"""
        try:
            # Si la ruta es relativa, pásala por resource_path
            if not os.path.isabs(icon_path):
                icon_path = resource_path(icon_path)

            img = Image.open(icon_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error al cargar el ícono {icon_path}: {e}")
            return None

    def _crear_barra_navigation(self):
        # Estilo para las pestañas
        style = ttk.Style()
        style.configure(
            'TNotebook.Tab',
            font=('Arial', 12, 'bold'),
            padding=[20, 8],
        )

        # Crear el Notebook principal
        self.notebook = ttk.Notebook(self.ventana, style='TNotebook')
        self.notebook.pack(pady=0, expand=True, fill='both')

        # Íconos
        icon_size = (24, 24)
        icon_asistencias = self._cargar_icono("public/static/icons/huella-dactilar.png", icon_size) or ""
        icon_admin = self._cargar_icono("public/static/icons/nueva-cuenta.png", icon_size) or ""

        # Crear los frames para cada pestaña
        self.frame_asistencias = tk.Frame(self.notebook, bg="lightblue")
        self.frame_admin = tk.Frame(self.notebook, bg="#f8fafc")

        # Añadir pestañas
        self.notebook.add(self.frame_asistencias, text=" Asistencias", image=icon_asistencias, compound=tk.LEFT)
        self.notebook.add(self.frame_admin, text=" Administración", image=icon_admin, compound=tk.LEFT)

        self.tab_icons = [icon_asistencias, icon_admin]

        # Contenido de Asistencias (ya lo tienes hecho)
        self._contenido_control_asistencias(self.frame_asistencias)

        # Evento al cambiar de pestaña
        self.notebook.bind('<<NotebookTabChanged>>', self._on_main_tab_changed)

        # Mostrar por defecto la pestaña de Asistencias
        self.notebook.select(self.frame_asistencias)


    def _on_main_tab_changed(self, event):
        """Si selecciona Administración, valida login y carga el panel ahí mismo."""
        sel = event.widget.select()
        if sel == str(self.frame_admin):  # pestaña de Administración
            # 1) Login si no hay sesión
            if not self._admin_logged:
                if not self._login_admin():
                    # Si falla el login, volver a Asistencias
                    self.notebook.select(self.frame_asistencias)
                    return

            # 2) Limpiar la pestaña
            for w in self.frame_admin.winfo_children():
                w.destroy()

            # 3) Cargar el panel de admin en la MISMA pestaña
            #    (tu _abrir_panel_administracion detecta frame_admin y renderiza ahí)
            self._abrir_panel_administracion()


   #---------Apartado de login----------#
   
    def _abrir_panel_admin_guardado(self):
        """Si no hay sesión admin, pide login. Si la hay, abre panel."""
        if not self._admin_logged:
            if not self._login_admin():
                return
        self._abrir_panel_administracion()
    def _login_admin(self) -> bool:
        """
        Pregunta si quieres iniciar sesión de administrador con HUELLADIGITAL
        o con USUARIO/CONTRASEÑA y llama al método correspondiente.
        """
        usar_huella = messagebox.askyesno(
            "Inicio de sesión - Administración",
            "¿Quieres iniciar sesión como administrador usando la huella digital?\n\n"
            "Sí = Huella del administrador\nNo = Usuario y contraseña"
        )

        if usar_huella:
            return self._login_admin_huella()
        else:
            return self._login_admin_user_pass()

    def _login_admin_user_pass(self) -> bool:
        """Pide usuario/contraseña y valida contra .env (bcrypt). Re-lee .env por si cambió."""
        try:
            # Releer .env en cada intento
            load_dotenv(os.path.abspath(ENV_PATH), override=True)
        except Exception:
            pass

        u_env = (os.getenv("ADMIN_USER") or "").strip().strip('"').strip("'")
        h_env = (os.getenv("ADMIN_PASS_HASH") or "").strip().strip('"').strip("'")

        if not u_env or not h_env:
            messagebox.showerror(
                "Error de configuración",
                f"No se cargaron ADMIN_USER/ADMIN_PASS_HASH desde:\n{os.path.abspath(ENV_PATH)}"
            )
            return False

        user = simpledialog.askstring("Administración", "Usuario:", parent=self.ventana)
        if user is None:
            return False
        pwd = simpledialog.askstring("Administración", "Contraseña:", parent=self.ventana, show="*")
        if pwd is None:
            return False

        ok_user = user.strip().lower() == u_env.lower()
        try:
            ok_pass = bcrypt.checkpw(pwd.encode(), h_env.encode())
        except Exception as e:
            messagebox.showerror("Error", f"No fue posible validar la contraseña:\n{e}")
            return False

        if ok_user and ok_pass:
            self._admin_user = u_env
            self._admin_pass_hash = h_env
            self._admin_logged = True
            return True

        if not ok_user:
            messagebox.showerror("Acceso denegado", "Usuario incorrecto.")
        else:
            messagebox.showerror("Acceso denegado", "Contraseña incorrecta.")
        return False
    
    def _login_admin_huella(self) -> bool:
        """
        Inicia sesión de administrador usando la huella registrada en admin_config.
        NO usa las huellas de alumnos.
        """
        try:
            template = self.controlador.obtener_huella_admin()
            if not template:
                messagebox.showwarning(
                    "Sin huella de admin",
                    "No hay una huella de administrador registrada.\n"
                    "Regístrala desde el Panel de Administración."
                )
                return False

            # Armamos una "persona" ficticia para reutilizar verify_fingerprint
            admin_persona = {
                "id": -1,
                "nombre": "Administrador",
                "apellido_paterno": "",
                "apellido_materno": "",
                "huella_digital": template,
            }
            personas = [admin_persona]

            matching = self.interface_api.verify_fingerprint(personas)

            if not matching:
                messagebox.showerror(
                    "Acceso denegado",
                    "Huella de administrador no reconocida."
                )
                return False

            # Si llega aquí, asumimos que la huella coincide
            self._admin_logged = True
            self._admin_user = "admin_huella"
            messagebox.showinfo(
                "Acceso concedido",
                "Sesión de administrador iniciada con huella digital."
            )
            return True

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(
                "Error",
                f"No fue posible iniciar sesión con huella de administrador:\n{e}"
            )
            return False

    def _cerrar_sesion_admin(self):
        """Cierra sesión y destruye el panel admin si está abierto. NO toca las credenciales."""
        self._admin_logged = False
        win = getattr(self, "_admin_win", None)
        if win and win.winfo_exists():
            try:
                win.destroy()
            except Exception:
                pass
        messagebox.showinfo("Administración", "Sesión de administrador cerrada.")

    def _abrir_panel_administracion(self):
        """Carga el panel de administración.
        - Si existe self.frame_admin (pestaña dentro del Notebook), se renderiza ahí mismo.
        - Si no existe, abre un Toplevel como fallback.
        """
        if not self._admin_logged:
            messagebox.showwarning("Administración", "Debes iniciar sesión como administrador.")
            return

        # --- Helper local para pintar el panel en cualquier contenedor (frame o toplevel) ---
        def _render(parent, on_close=None):
            # Header
            header = tk.Frame(parent, bg="white")
            header.pack(fill="x", padx=12, pady=8)

            tk.Label(header, text="Panel de Administración",
                    font=("Arial", 16, "bold"), bg="white").pack(side="left")

            def _cerrar_y_limpiar():
                # Cierra sesión
                self._cerrar_sesion_admin()
                # Si te lo llamaron desde pestaña, limpia el frame
                if isinstance(parent, tk.Frame):
                    for w in parent.winfo_children():
                        w.destroy()
                    # vuelve a Asistencias si hay notebook
                    if hasattr(self, "notebook") and hasattr(self, "frame_asistencias"):
                        try:
                            self.notebook.select(self.frame_asistencias)
                        except Exception:
                            pass
                # Si te lo llamaron desde un toplevel, ciérralo
                if callable(on_close):
                    try:
                        on_close()
                    except Exception:
                        pass
            tk.Button(
                header,
                text="Registrar huella admin",
                bg="#2563eb",
                fg="white",
                font=("Arial", 10, "bold"),
                relief="flat",
                cursor="hand2",
                command=self._solicitar_huella_admin_segura
            ).pack(side="right", padx=6)

            tk.Button(header, text="Cerrar sesión", bg="#ef4444", fg="white",
                    font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                    command=_cerrar_y_limpiar).pack(side="right", padx=6)

            # Notebook interno con tus apartados (mismo look)
            nb = ttk.Notebook(parent)
            nb.pack(fill="both", expand=True, padx=10, pady=10)

            frame_registro = tk.Frame(nb, bg="lightblue")
            frame_reportes = tk.Frame(nb, bg="lightblue")
            frame_catalogo = tk.Frame(nb, bg="lightblue")

            nb.add(frame_registro, text=" Registro")
            nb.add(frame_reportes, text=" Reportes")
            nb.add(frame_catalogo, text=" Catálogo")

            # Render original para conservar diseño
            try:
                self._contenido_gestion_estudiantes(frame_registro)
            except Exception as e:
                tk.Label(frame_registro, text=f"Error al cargar Registro: {e}",
                        bg="lightblue", fg="red").pack(pady=10)

            try:
                self._contenido_reportes(frame_reportes)
            except Exception as e:
                tk.Label(frame_reportes, text=f"Error al cargar Reportes: {e}",
                        bg="lightblue", fg="red").pack(pady=10)

            try:
                self._contenido_catalogo(frame_catalogo)
            except Exception as e:
                tk.Label(frame_catalogo, text=f"Error al cargar Catálogo: {e}",
                        bg="lightblue", fg="red").pack(pady=10)

        # --- 1) Preferencia: cargar DENTRO de la pestaña "Administración" si existe ---
        target = getattr(self, "frame_admin", None)
        if target and target.winfo_exists():
            # Limpiar y pintar en la pestaña
            for w in target.winfo_children():
                w.destroy()
            _render(target)
            return

        # --- 2) Fallback: abrir Toplevel si no hay pestaña "Administración" ---
        # Evita abrir 2 veces
        if getattr(self, "_admin_win", None) and self._admin_win.winfo_exists():
            try:
                self._admin_win.lift()
                return
            except Exception:
                pass

        top = tk.Toplevel(self.ventana)
        self._admin_win = top
        top.title("Panel de Administración")
        top.resizable(True, True)  # min/max OK

        # Render dentro del Toplevel y define cierre
        def _on_close():
            self._admin_logged = False
            try:
                top.destroy()
            except Exception:
                pass

        _render(top, on_close=_on_close)
        top.protocol("WM_DELETE_WINDOW", _on_close)
   
    def _validar_credenciales_admin_para_huella(self) -> bool:
        """
        Pide usuario y contraseña del administrador y valida contra .env
        antes de permitir registrar la huella de administrador.
        """
        try:
            # Releer .env por seguridad
            try:
                load_dotenv(os.path.abspath(ENV_PATH), override=True)
            except:
                pass

            user_env = (os.getenv("ADMIN_USER") or "").strip()
            pass_env = (os.getenv("ADMIN_PASS_HASH") or "").strip()

            if not user_env or not pass_env:
                messagebox.showerror(
                    "Error de configuración",
                    "ADMIN_USER o ADMIN_PASS_HASH no están configurados en .env"
                )
                return False

            user = simpledialog.askstring("Confirmación", "Usuario administrador:", parent=self.ventana)
            if user is None:
                return False

            pwd = simpledialog.askstring("Confirmación", "Contraseña:", parent=self.ventana, show="*")
            if pwd is None:
                return False

            if user.strip().lower() != user_env.lower():
                messagebox.showerror("Acceso denegado", "Usuario incorrecto.")
                return False

            try:
                valido = bcrypt.checkpw(pwd.encode(), pass_env.encode())
            except:
                messagebox.showerror("Error", "No se pudo validar la contraseña.")
                return False

            if not valido:
                messagebox.showerror("Acceso denegado", "Contraseña incorrecta.")
                return False

            return True

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo validar el acceso:\n{e}")
            return False
    
    def _abrir_modal_huella_admin(self):
            """
            Abre un modal para registrar (o reemplazar) la huella del administrador.
            Usa self.interface_api.register_fingerprint como con los estudiantes.
            """
            modal = tk.Toplevel(self.ventana)
            modal.title("Registrar huella del administrador")
            modal.geometry("500x300")
            modal.transient(self.ventana)
            modal.grab_set()

            # Centrar
            modal.update_idletasks()
            ancho, alto = 500, 300
            x = (modal.winfo_screenwidth() // 2) - (ancho // 2)
            y = (modal.winfo_screenheight() // 2) - (alto // 2)
            modal.geometry(f"{ancho}x{alto}+{x}+{y}")

            frame = tk.Frame(modal, bg="#f3f4f6")
            frame.pack(fill="both", expand=True, padx=20, pady=20)

            tk.Label(
                frame,
                text="Registrar / actualizar huella del administrador",
                bg="#f3f4f6",
                font=("Arial", 12, "bold")
            ).pack(pady=(0, 15))

            # Botón de escanear
            icono_huella = None
            try:
                img = Image.open(resource_path("public/static/icons/huella-dactilar.png"))
                img = img.resize((20, 20), Image.LANCZOS)
                icono_huella = ImageTk.PhotoImage(img)
            except Exception:
                pass

            btn_escanear = tk.Button(
                frame,
                text=" Escanear huella del administrador ",
                font=("Arial", 11, "bold"),
                relief="raised",
                image=icono_huella,
                compound="left" if icono_huella else None,
                padx=10, pady=5,
                cursor="hand2"
            )
            btn_escanear.image = icono_huella
            btn_escanear.pack(pady=(0, 10))

            lbl_estado = tk.Label(
                frame,
                text="Esperando huella...",
                bg="#f3f4f6",
                font=("Arial", 11),
                fg="blue"
            )
            lbl_estado.pack(pady=(0, 10))

            huella_admin = None

            def finalizar_escaneo():
                lbl_estado.config(text="Huella capturada", fg="green")
                btn_escanear.config(state="normal")

            def on_enroll(finger_idx, template):
                nonlocal huella_admin
                huella_admin = template
                finalizar_escaneo()
                print(f"[ADMIN] Huella {finger_idx} registrada. Tamaño: {len(template)} bytes")

            btn_escanear.config(
                command=lambda: self.interface_api.register_fingerprint(on_enroll=on_enroll)
            )

            # Botones Guardar / Cancelar
            btn_frame = tk.Frame(frame, bg="#f3f4f6")
            btn_frame.pack(pady=(20, 0))

            def guardar_huella_admin():
                if not huella_admin:
                    messagebox.showwarning(
                        "Sin huella",
                        "Primero escanea la huella del administrador."
                    )
                    return

                ok = self.controlador.guardar_huella_admin(huella_admin)
                if ok:
                    messagebox.showinfo(
                        "Huella guardada",
                        "La huella del administrador se ha registrado correctamente."
                    )
                    modal.destroy()
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo guardar la huella del administrador."
                    )

            tk.Button(
                btn_frame,
                text="Guardar",
                bg="#16a34a",
                fg="white",
                font=("Arial", 11, "bold"),
                relief="flat",
                cursor="hand2",
                command=guardar_huella_admin,
                width=12
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="Cancelar",
                bg="#ef4444",
                fg="white",
                font=("Arial", 11, "bold"),
                relief="flat",
                cursor="hand2",
                command=modal.destroy,
                width=12
            ).pack(side="left", padx=5)
    
    def _solicitar_huella_admin_segura(self):
        """
        Antes de abrir el modal de registrar huella admin,
        pide usuario y contraseña. Si no son correctos, no deja continuar.
        """
        if not self._validar_credenciales_admin_para_huella():
            return
        
        # Si el login fue exitoso → abrir modal para registrar huella
        self._abrir_modal_huella_admin()

  #---------------------------------------#

    def _inicializar_ui_estudiantes(self):
        """
        Inicializa la interfaz de usuario para la gestión de estudiantes
        """
        # Limpiar el frame de contenido si existe
        if hasattr(self, 'frame_contenido'):
            for widget in self.frame_contenido.winfo_children():
                widget.destroy()
        
        # Frame principal centrado
        frame_principal = tk.Frame(self.frame_contenido, bg="lightblue")
        frame_principal.pack(fill="both", expand=True)
        
        # Frame contenedor para centrar el contenido
        frame_contenedor = tk.Frame(frame_principal, bg="lightblue")
        frame_contenedor.pack(expand=True, fill="both", padx=40, pady=20)

        # Frame para el canvas y la barra de desplazamiento
        frame_canvas = tk.Frame(frame_contenedor, bg="lightblue")
        frame_canvas.pack(fill="both", expand=True)
        
        # Canvas para las tarjetas
        canvas = tk.Canvas(
            frame_canvas, 
            bg="lightblue",
            highlightthickness=0,
            bd=0,
            # width=1000  # Ancho fijo para el contenido
        )

        # Barra de desplazamiento
        scrollbar = ttk.Scrollbar(
            frame_canvas, 
            orient="vertical", 
            command=canvas.yview
        )
        
        # Configurar el canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        
        # Frame desplazable dentro del canvas
        scrollable_frame = tk.Frame(canvas, bg="lightblue")
        
        # Configurar el scroll
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Crear ventana en el canvas para el frame desplazable
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
    
        # Configurar el desplazamiento con la rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Vincular el evento de la rueda del mouse
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
        # Función para ajustar el ancho del frame desplazable cuando cambia el tamaño del canvas
        def _on_canvas_configure(event):
            canvas.itemconfig("all", width=event.width)
    
        canvas.bind("<Configure>", _on_canvas_configure)
    
        # Empaquetar el canvas y la barra de desplazamiento
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Guardar referencia al frame de estudiantes y al canvas para actualizaciones posteriores
        self.frame_estudiantes = scrollable_frame
        self.canvas_estudiantes = canvas
    
        return scrollable_frame

    def _contenido_gestion_estudiantes(self, parent):
        # Título
        tk.Label(parent, text="Gestión de Estudiantes", bg="lightblue", fg="#1a253c",
                font=('Arial', 24, 'bold')).place(x=30, y=30)
        
        # === BARRA DE BÚSQUEDA (como reportes, pero sin botón) ===
        frame_busqueda_reg = tk.Frame(parent, bg="lightblue")
        frame_busqueda_reg.place(relx=0.5, y=70, height=40, anchor="n")

        tk.Label(
            frame_busqueda_reg,
            text="Buscar estudiante:",
            bg="lightblue",
            fg="#1a253c",
            font=('Arial', 12)
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Función que consulta al controlador (igual que en reportes)
        def _fetch_estudiantes_reg(q):
            try:
                return self.controlador.buscar_estudiantes(q, limit=20)
            except Exception as e:
                print("Error buscando estudiantes en Registro:", e)
                return []

        # Qué hacer cuando el usuario selecciona un estudiante del listado
        def _on_select_est_reg(item):
            # Abre directamente la ventana de edición del estudiante
            self._mostrar_estudiante_en_registro(item)

        # Entry con autocompletado
        self.entry_estudiante_registro = AutocompleteEntry(
            frame_busqueda_reg,
            fetch_callback=_fetch_estudiantes_reg,
            on_select=_on_select_est_reg,
            width=40
        )
        self.entry_estudiante_registro.pack(side=tk.LEFT)

        # Placeholder opcional
        self.entry_estudiante_registro.insert(0, "Nombre, matrícula o correo...")
        self.entry_estudiante_registro.bind(
            "<FocusIn>",
            lambda e: self.entry_estudiante_registro.delete(0, "end")
            if self.entry_estudiante_registro.get().startswith("Nombre")
            else None
        )

        # Al presionar Enter -> buscar por texto (sin botón)
        self.entry_estudiante_registro.bind(
            "<Return>",
            lambda e: self.buscar_estudiante_registro()
        )

        # Botón "Nuevo Estudiante" con icono redimensionado y alineado a la izquierda del texto
        imagen_boton = Image.open(resource_path("public/static/icons/nueva-cuenta-white.png"))

        imagen_boton = imagen_boton.resize((24, 24), Image.LANCZOS)
        icono_boton = ImageTk.PhotoImage(imagen_boton)
        btn_nuevo = tk.Button(
            parent,
            text="  Nuevo Estudiante",
            bg="#2563eb",
            fg="white",
            font=('Arial', 12, 'bold'),
            cursor="hand2",
            relief="flat",
            image=icono_boton,
            compound="left",
            command=self._abrir_modal_estudiante
        )
        btn_nuevo.image = icono_boton
        btn_nuevo.place(relx=1.0, x=-40, y=40, width=200, height=40, anchor="ne")

        # Frame contenedor principal
        self.frame_principal = tk.Frame(parent, bg="lightblue")
        self.frame_principal.pack(fill="both", expand=True, padx=40, pady=(100, 20))
        
        # Frame para el contenido (se usará para mostrar el mensaje o la lista)
        self.frame_contenido = tk.Frame(self.frame_principal, bg="lightblue")
        self.frame_contenido.pack(fill="both", expand=True)
        
        # Inicializar la UI de estudiantes
        self._inicializar_ui_estudiantes()
        
        # Cargar estudiantes si el controlador está disponible
        if hasattr(self, 'controlador') and self.controlador:
            self._cargar_estudiantes_en_vista()
        else:
            # Mostrar mensaje de carga o estado inicial
            self._mostrar_mensaje_sin_estudiantes()

    def buscar_estudiante_registro(self):
            """
            Busca un estudiante desde la pestaña Registro y abre directamente
            la ventana de edición. Funciona solo con Enter (no hay botón Buscar).
            """
            try:
                # Cerrar popup del autocomplete si está abierto
                try:
                    if hasattr(self, "entry_estudiante_registro") and hasattr(self.entry_estudiante_registro, "close_popup"):
                        self.entry_estudiante_registro.close_popup()
                except Exception:
                    pass

                texto = (self.entry_estudiante_registro.get() or "").strip()
                if not texto or texto.lower().startswith("nombre"):
                    messagebox.showinfo(
                        "Atención",
                        "Escribe el nombre, matrícula o correo del estudiante."
                    )
                    return

                # Buscar en la base de datos
                resultados = self.controlador.buscar_estudiantes(texto, limit=10) or []

                if len(resultados) == 0:
                    messagebox.showinfo(
                        "Sin resultados",
                        f"No se encontró ningún estudiante para: “{texto}”."
                    )
                    return
                elif len(resultados) == 1:
                    seleccionado = resultados[0]
                else:
                    # Si hay varios, por simplicidad abrimos el primero.
                    # (Si luego quieres, se puede hacer un dialogo para elegir uno.)
                    seleccionado = resultados[0]

                # Abrir directamente el modal de edición del estudiante encontrado
                self._editar_estudiante(seleccionado)

            except Exception as e:
                print(f"Error al buscar estudiante en Registro: {e}")
                traceback.print_exc()
                messagebox.showerror("Error", f"No se pudo ejecutar la búsqueda:\n{e}")

    def _crear_tarjeta_estudiante(self, parent, estudiante, index):
        # Crear frame para la tarjeta
        tarjeta = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid",
            padx=20,
            pady=15,
            highlightbackground="#e0e0e0",
            highlightthickness=1
        )
        # Hacer que la tarjeta ocupe el ancho disponible pero centrada
        tarjeta.pack(fill="x", pady=5, ipadx=10, ipady=5)
        
        # Configurar grid para la tarjeta
        tarjeta.columnconfigure(0, weight=1)  # Columna para la información
        tarjeta.columnconfigure(1, weight=0)  # Columna para los botones
        
        # Frame para la información del estudiante
        frame_info = tk.Frame(tarjeta, bg="white")
        frame_info.grid(row=0, column=0, sticky="w")
        
        # Mostrar información del estudiante
         # Columna izquierda (datos principales)
        col1 = tk.Frame(frame_info, bg="white")
        col1.grid(row=0, column=0, sticky="w")
        
        # Nombre completo en negrita
        tk.Label(
            col1,
            text=f"{estudiante.get('nombre', '')} {estudiante.get('apellido_p', '')} {estudiante.get('apellido_m', '')}".strip(),
            bg="white",
            font=('Arial', 12, 'bold'),
            anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, 3))
        
        # Matrícula y email en primera columna
        tk.Label(
            col1,
            text=f"📝  Matrícula: {estudiante.get('matricula', '')}",
            bg="white",
            font=('Arial', 10),
            fg="#4b5563",
            anchor="w"
        ).grid(row=1, column=0, sticky="w")
        
        tk.Label(
            col1,
            text=f"📧  Email: {estudiante.get('email', '')}",
            bg="white",
            font=('Arial', 10),
            fg="#4b5563",
            anchor="w"
        ).grid(row=2, column=0, sticky="w")


        # Mostrar Generación
        tk.Label(
            col1,
            text=f"🎓  Generación: {estudiante.get('generacion', 'None')}",
            bg="white",
            font=('Arial', 10),
            fg="#4b5563",
            anchor="w"
        ).grid(row=3, column=0, sticky="w")
        
        # Columna derecha (datos adicionales)
        col2 = tk.Frame(frame_info, bg="white")
        col2.grid(row=0, column=1, sticky="w", padx=(15, 0))
        
        # Mostrar Asesor y area de conocimiento en segunda columna
        tk.Label(
            col2,
            text=f"👤  Asesor: {estudiante.get('asesor', 'None')}",
            bg="white",
            font=('Arial', 10),
            fg="#4b5563",
            anchor="w"
        ).grid(row=1, column=0, sticky="w")
        
        #tk.Label(
            #col2,
            #text=f"✉️  Correo del asesor: {estudiante.get('asesor_email', 'No registrado')}",
            #bg="white",
            #font=('Arial', 10),
            #fg="#4b5563",
            #Sanchor="w"
        #).grid(row=3, column=0, sticky="w")
                
        tk.Label(
            col2,
            text=f"📚  Área de Conocimiento: {estudiante.get('area_conocimiento', 'None')}",
            bg="white",
            font=('Arial', 10),
            fg="#4b5563",
            anchor="w"
        ).grid(row=2, column=0, sticky="w")
        
        # Frame para los botones
        frame_botones = tk.Frame(tarjeta, bg="white")
        frame_botones.grid(row=0, column=1, sticky="e")
        
        # Botón Editar
        btn_editar = tk.Button(
            frame_botones,
            text="Editar",
            bg="#3b82f6",
            fg="white",
            font=('Arial', 10, 'bold'),
            relief="flat",
            cursor="hand2",
            width=8,
            command=lambda e=estudiante: self._editar_estudiante(e)
        )
        btn_editar.pack(side="left", padx=(20, 5))
        
        # Botón Eliminar
        btn_eliminar = tk.Button(
            frame_botones,
            text="Eliminar",
            bg="#ef4444",
            fg="white",
            font=('Arial', 10, 'bold'),
            relief="flat",
            cursor="hand2",
            width=8,
            command=lambda e=estudiante: self._confirmar_eliminar_estudiante(e)
        )
        btn_eliminar.pack(side="left", padx=5)

    def _cargar_estudiantes_en_vista(self):
        """
        Carga los estudiantes desde el controlador y los muestra en la vista
        """
        try:
            # Verificar si el frame de estudiantes aún existe
            if not hasattr(self, 'frame_estudiantes') or not self.frame_estudiantes.winfo_exists():
                # Si no existe, recrear la interfaz
                if hasattr(self, 'frame_contenido'):
                    for widget in self.frame_contenido.winfo_children():
                        widget.destroy()
                    self._inicializar_ui_estudiantes()
                else:
                    return
            
            # Limpiar el frame actual
            for widget in self.frame_estudiantes.winfo_children():
                widget.destroy()
                
            # Obtener estudiantes del controlador
            estudiantes_data = self.controlador.obtener_estudiantes_registrados()
            
            if estudiantes_data:
                # Convertir a lista de diccionarios si es necesario
                self.lista_estudiantes = []
                for est in estudiantes_data:
                    if isinstance(est, dict):
                        # Ya está en formato diccionario
                        self.lista_estudiantes.append(est)
                    else:
                        # Convertir de tupla a diccionario
                        estudiante = {
                            'id': est[0],
                            'nombre': est[1],
                            'apellido_p': est[2] if len(est) > 2 else '',
                            'apellido_m': est[3] if len(est) > 3 else '',
                            'matricula': est[4] if len(est) > 4 else est[0],  # Usar ID como matrícula si no hay matrícula
                            'email': est[5] if len(est) > 5 else '',
                            'generacion': est[6] if len(est) > 6 else '',
                            'asesor': est[7] if len(est) > 7 else '',
                            'area_conocimiento': est[8] if len(est) > 8 else '',
                            'carrera': est[9] if len(est) > 9 else '',
                            'huella_digital': est[10] if len(est) > 10 else ''
                        }
                        self.lista_estudiantes.append(estudiante)
                
                # Mostrar los estudiantes
                for i, estudiante in enumerate(self.lista_estudiantes):
                    self._crear_tarjeta_estudiante(self.frame_estudiantes, estudiante, i)
            else:
                self._mostrar_mensaje_sin_estudiantes()
                
        except Exception as e:
            print(f"Error al cargar estudiantes: {e}")
            traceback.print_exc()
            self._mostrar_mensaje_sin_estudiantes()

    def _mostrar_estudiante_en_registro(self, estudiante):
        """
        Muestra en Gestión de Estudiantes SOLO la tarjeta del estudiante buscado.
        No abre el modal de edición.
        """
        try:
            if not hasattr(self, "frame_estudiantes"):
                return  # por si aún no se ha inicializado la UI

            # Limpiar las tarjetas actuales
            for widget in self.frame_estudiantes.winfo_children():
                widget.destroy()

            # Asegurarnos de tener un dict con los campos esperados
            data = estudiante

            # Actualizar la lista interna (por si luego quieres usarla)
            self.lista_estudiantes = [data]

            # Crear una única tarjeta (index 0)
            self._crear_tarjeta_estudiante(self.frame_estudiantes, data, 0)

            # Subir el scroll al inicio
            if hasattr(self, "canvas_estudiantes"):
                self.canvas_estudiantes.yview_moveto(0.0)

        except Exception as e:
            print(f"Error al mostrar estudiante en registro: {e}")
            traceback.print_exc()

    def _mostrar_mensaje_sin_estudiantes(self):
        # Limpiar el frame de contenido
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()
            
        # Crear un frame centrado para el mensaje
        frame_mensaje = tk.Frame(self.frame_contenido, bg="lightblue")
        frame_mensaje.pack(expand=True, pady=100)
        
        # Icono
        try:
            imagen = Image.open(resource_path("public/static/icons/usuarios.png"))
            imagen = imagen.resize((100, 100), Image.LANCZOS)
            icono_img = ImageTk.PhotoImage(imagen)
            icono = tk.Label(frame_mensaje, image=icono_img, bg="lightblue")
            icono.image = icono_img
            icono.pack(pady=(0, 20))
        except Exception as e:
            print(f"Error al cargar el ícono: {e}")
        
        # Título
        tk.Label(
            frame_mensaje, 
            text="No hay estudiantes registrados", 
            bg="lightblue", 
            fg="#4b5563",
            font=('Arial', 20, 'bold')
        ).pack(pady=(0, 10))
        
        # Subtítulo
        tk.Label(
            frame_mensaje, 
            text="Comienza agregando tu primer estudiante al sistema.", 
            bg="lightblue", 
            fg="#6b7280",
            font=('Arial', 14)
        ).pack()

    def _editar_estudiante(self, estudiante):
        # Crear ventana modal
        modal = tk.Toplevel(self.ventana)
        modal.title("Editar Estudiante")
        # ⬇⬇ ventana más cómoda ⬇⬇
        window_width = 900
        window_height = 520
        modal.geometry(f"{window_width}x{window_height}")
        modal.resizable(False, False)
        modal.grab_set()
        modal.configure(bg='#f3f4f6')

        # Centrar
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (window_width // 2)
        y = (modal.winfo_screenheight() // 2) - (window_height // 2)
        modal.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # Grid principal
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_rowconfigure(1, weight=1)

        # Título
        tk.Label(
            modal, text="Editar Estudiante", font=('Arial', 18, 'bold'),
            bg='#f3f4f6', pady=15
        ).grid(row=0, column=0, sticky="ew", padx=20)

        # Canvas + frame scrollable
        canvas = tk.Canvas(modal, bg='#f3f4f6', highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg='#f3f4f6', padx=20, pady=5)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.grid(row=1, column=0, sticky="nsew")

        # Variables
        vars_data = {
            'nombre': tk.StringVar(value=estudiante.get('nombre', '')),
            'apellido_p': tk.StringVar(value=estudiante.get('apellido_p', '')),
            'apellido_m': tk.StringVar(value=estudiante.get('apellido_m', '')),
            'matricula': tk.StringVar(value=str(estudiante.get('matricula', ''))),
            'email': tk.StringVar(value=estudiante.get('email', '')),
            'generacion': tk.StringVar(value=estudiante.get('generacion', '')),
            'asesor': tk.StringVar(value=estudiante.get('asesor', '')),
            'area_conocimiento': tk.StringVar(value=estudiante.get('area_conocimiento', '')),
            'carrera': tk.StringVar(value=estudiante.get('carrera', '')),
        }
        huella_digital = estudiante.get('huella_digital', '')

        # ================= FORMULARIO ALINEADO (4 columnas) =================
        form_frame = tk.Frame(scrollable_frame, bg='#f3f4f6')
        form_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Columna 1
        tk.Label(form_frame, text="Nombre(s):", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        entry_nombre = tk.Entry(form_frame, textvariable=vars_data['nombre'],
                                font=('Arial', 10), relief='solid', bd=1, bg='white', width=28)
        entry_nombre.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Apellido Paterno:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        entry_apellido_p = tk.Entry(form_frame, textvariable=vars_data['apellido_p'],
                                    font=('Arial', 10), relief='solid', bd=1, bg='white', width=28)
        entry_apellido_p.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Apellido Materno:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="e", padx=5, pady=5)
        entry_apellido_m = tk.Entry(form_frame, textvariable=vars_data['apellido_m'],
                                    font=('Arial', 10), relief='solid', bd=1, bg='white', width=28)
        entry_apellido_m.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Matrícula:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky="e", padx=5, pady=5)
        entry_matricula = tk.Entry(form_frame, textvariable=vars_data['matricula'],
                                font=('Arial', 10), relief='solid', bd=1, bg='white', width=28)
        entry_matricula.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Correo:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky="e", padx=5, pady=5)
        entry_correo = tk.Entry(form_frame, textvariable=vars_data['email'],
                                font=('Arial', 10), relief='solid', bd=1, bg='white', width=28)
        entry_correo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Columna 2
        tk.Label(form_frame, text="Generación:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        generaciones = self.controlador.obtener_generaciones()
        combo_generacion = ttk.Combobox(
            form_frame,
            textvariable=vars_data['generacion'],
            font=('Arial', 10),
            values=[g['nombre'] for g in generaciones],
            width=26,
            state="readonly"
        )
        combo_generacion.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Asesor:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky="e", padx=5, pady=5)
        asesores = self.controlador.obtener_asesores()
        combo_asesor = ttk.Combobox(
            form_frame,
            textvariable=vars_data['asesor'],
            font=('Arial', 10),
            values=[a['name'] for a in asesores],
            width=26,
            state="readonly"
        )
        combo_asesor.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.asesores_data = {a['name']: a['id'] for a in asesores}

        tk.Label(form_frame, text="Área:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=2, column=2, sticky="e", padx=5, pady=5)
        areas = self.controlador.obtener_areas_conocimiento()
        combo_area = ttk.Combobox(
            form_frame,
            textvariable=vars_data['area_conocimiento'],
            font=('Arial', 10),
            values=[ar['nombre'] for ar in areas],
            width=26,
            state="readonly"
        )
        combo_area.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # ---------- CARRERA: COMBO + OTROS ----------
        tk.Label(form_frame, text="Carrera:", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=3, column=2, sticky="e", padx=5, pady=5)

        opciones_carrera = [
            "Maestría en Ingeniería para la Innovación y Desarrollo Tecnológico",
            "Doctorado en Ingeniería para la Innovación y Desarrollo Tecnológico",
            "Otros",
        ]

        combo_carrera = ttk.Combobox(
            form_frame,
            font=('Arial', 10),
            values=opciones_carrera,
            width=26,
            state="readonly"
        )
        combo_carrera.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        tk.Label(form_frame, text="Especifique carrera (si eligió 'Otros'):", bg='#f3f4f6',
                font=('Arial', 10, 'bold')).grid(row=4, column=2, sticky="e", padx=5, pady=5)
        entry_carrera_otro = tk.Entry(
            form_frame,
            font=('Arial', 10),
            relief='solid', bd=1, bg='white', width=28
        )
        entry_carrera_otro.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        # ⬇⬇ Igual que en "nuevo estudiante": deshabilitado y vacío al inicio ⬇⬇
        entry_carrera_otro.config(state="disabled")

        def _on_carrera_change(event=None):
            opcion = combo_carrera.get().strip()
            if opcion == "Otros":
                entry_carrera_otro.config(state="normal")
                entry_carrera_otro.focus_set()
            else:
                entry_carrera_otro.delete(0, tk.END)
                entry_carrera_otro.config(state="disabled")

        combo_carrera.bind("<<ComboboxSelected>>", _on_carrera_change)

        # Pre-seleccionar solo en el COMBO (sin tocar el entry)
        carrera_actual = vars_data['carrera'].get().strip()
        if carrera_actual in opciones_carrera[:2]:
            combo_carrera.set(carrera_actual)
        elif carrera_actual:
            # Carrera distinta → dejamos "Otros" seleccionado,
            # pero el campo de texto sigue vacío y deshabilitado
            combo_carrera.set("Otros")
        else:
            combo_carrera.set(opciones_carrera[0])

        # Opcional: que las columnas se vean bien distribuidas
        for col in range(4):
            form_frame.grid_columnconfigure(col, weight=1)

        # ======================= SECCIÓN HUELLA =======================
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)

        frame_huella = tk.LabelFrame(
            scrollable_frame, text=" Lector de Huella Dactilar ",
            bg='#f3f4f6', font=('Arial', 9, 'bold'),
            padx=10, pady=5, relief="groove"
        )
        frame_huella.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 5))

        tk.Label(frame_huella, text="Inicialice el lector:", bg='#f3f4f6',
                font=('Arial', 9)).pack(pady=(0, 5))

        icono_huella = None
        try:
            img = Image.open(resource_path("public/static/icons/huella-dactilar.png"))
            img = img.resize((18, 18), Image.LANCZOS)
            icono_huella = ImageTk.PhotoImage(img)
        except Exception:
            pass

        btn_escanear = tk.Button(
            frame_huella, text=" ESCANEAR NUEVA HUELLA ",
            font=('Arial', 12, 'bold'), relief="solid",
            image=icono_huella, compound="left" if icono_huella else None,
            padx=10, pady=5, cursor="hand2"
        )
        btn_escanear.image = icono_huella
        btn_escanear.pack(pady=(0, 10))

        lbl_estado = tk.Label(frame_huella, text="Esperando huella...", font=('Arial', 14), fg="blue")
        lbl_estado.pack(pady=(5, 10))

        def finalizar_escaneo():
            lbl_estado.config(text="Escaneo finalizado", fg="green")
            btn_escanear.config(state="normal")

        def on_enroll(finger_idx, template):
            nonlocal huella_digital
            finalizar_escaneo()
            huella_digital = template
            print(f"Huella {finger_idx} registrada. Tamaño: {len(template)} bytes")

        btn_escanear.config(command=lambda: self.interface_api.register_fingerprint(on_enroll=on_enroll))

        # ======================= GUARDAR / CANCELAR =======================
        def guardar_cambios():
            from tkinter import messagebox

            # Carrera según selección
            opcion = combo_carrera.get().strip()
            if opcion == "Otros":
                carrera = entry_carrera_otro.get().strip()
            else:
                carrera = opcion

            try:
                ok = self.controlador.editar_estudiante(
                    estudiante_id=estudiante.get('id'),
                    email=vars_data['email'].get(),
                    matricula=vars_data['matricula'].get(),
                    nombre=vars_data['nombre'].get(),
                    apellido_p=vars_data['apellido_p'].get(),
                    apellido_m=vars_data['apellido_m'].get(),
                    huella_digital=huella_digital,
                    generacion=vars_data['generacion'].get(),
                    area_conocimiento=vars_data['area_conocimiento'].get(),
                    carrera=carrera,
                    asesor_nombre=vars_data['asesor'].get(),
                    id_asesor=self.asesores_data.get(vars_data['asesor'].get()),
                )
                if ok:
                    messagebox.showinfo("Éxito", "Datos actualizados")
                    modal.destroy()
                    self._cargar_estudiantes_en_vista()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {str(e)}")

        btn_frame = tk.Frame(modal, bg='#f3f4f6', pady=10)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        tk.Button(
            btn_frame, text="Cancelar", bg="#f44336", fg="white",
            font=('Arial', 10), relief="flat", cursor="hand2",
            command=modal.destroy
        ).pack(side="right", padx=5, pady=5)

        tk.Button(
            btn_frame, text="Guardar", bg="#4CAF50", fg="white",
            font=('Arial', 10), relief="flat", cursor="hand2",
            command=guardar_cambios
        ).pack(side="right", padx=(5, 25), pady=5)

        def _on_canvas_configure(event):
            canvas.itemconfig("all", width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)



    def _confirmar_eliminar_estudiante(self, estudiante):
        respuesta = messagebox.askquestion(
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar a {estudiante.get('nombre', '')}? \n\nEsto borrará todas las asistencias del estudiante"
        )
        print('Respuesta: ', respuesta)
        if respuesta == 'yes':
            self._eliminar_estudiante(estudiante)

    def _eliminar_estudiante(self, estudiante):
        try:
            # Aquí implementarás la lógica para eliminar el estudiante de la base de datos
            print(f"Eliminando estudiante: {estudiante}")
            
            if self.controlador.eliminar_estudiante(estudiante.get('id', '')):
                messagebox.showinfo("Éxito", "Estudiante eliminado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo eliminar el estudiante")
            # Recargar la lista de estudiantes
            self._cargar_estudiantes_en_vista()
            
        except Exception as e:
            print(f"Error al eliminar estudiante: {e}")
            messagebox.showerror("Error", "No se pudo eliminar el estudiante")


    def _abrir_modal_estudiante(self):
        modal = tk.Toplevel(self.ventana)
        modal.title("Registrar Nuevo Estudiante")

        # ⬇⬇ NUEVO TAMAÑO ⬇⬇
        ancho = 900
        alto = 520
        modal.geometry(f"{ancho}x{alto}")
        modal.transient(self.ventana)
        modal.grab_set()

        # Centrar el modal en la pantalla
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (modal.winfo_screenheight() // 2) - (alto // 2)
        modal.geometry(f"{ancho}x{alto}+{x}+{y}")

        # Configurar el grid principal
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_columnconfigure(1, weight=1)
        modal.grid_rowconfigure(0, weight=0)  # formulario
        modal.grid_rowconfigure(1, weight=0)  # huella
        modal.grid_rowconfigure(2, weight=0)  # botón

        # Estilos
        estilo_label = {'font': ('Arial', 11), 'anchor': 'w', 'padx': 5, 'pady': 2}
        estilo_entry = {'font': ('Arial', 11), 'width': 25}
        estilo_combobox = {'font': ('Arial', 11), 'width': 27}

        # Frame principal del formulario
        form_frame = tk.Frame(modal, padx=20, pady=10)
        form_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Que las 4 columnas internas se repartan bien
        for c in range(4):
            form_frame.grid_columnconfigure(c, weight=1)

        # Título
        tk.Label(
            form_frame,
            text="Registrar Nuevo Estudiante",
            font=('Arial', 16, 'bold'),
            pady=10
        ).grid(row=0, column=0, columnspan=4)

        # Helper para crear campos
        def crear_campo(frame, label_text, row, column, widget_type='entry', options=None):
            tk.Label(frame, text=label_text, **estilo_label).grid(
                row=row, column=column*2, sticky='ew')
            if widget_type == 'entry':
                entry = tk.Entry(frame, **estilo_entry)
                entry.grid(row=row, column=column*2+1, sticky='ew', pady=3)
                return entry
            elif widget_type == 'combobox':
                combo = ttk.Combobox(frame, **estilo_combobox)
                if options:
                    combo['values'] = options
                combo.grid(row=row, column=column*2+1, sticky='ew', pady=3)
                return combo

        # --------------------------
        # Campos del formulario
        # --------------------------

        # Columna izquierda
        entry_email = crear_campo(form_frame, "Email:", 1, 0)
        entry_nombre = crear_campo(form_frame, "Nombre(s):", 2, 0)
        entry_apellido_p = crear_campo(form_frame, "Apellido paterno:", 3, 0)
        entry_apellido_m = crear_campo(form_frame, "Apellido materno:", 4, 0)
        entry_matricula = crear_campo(form_frame, "Matrícula:", 5, 0)

        # Columna derecha
        generaciones = self.controlador.obtener_generaciones()
        self.combo_generacion = crear_campo(
            form_frame, "Generación:", 1, 1, 'combobox',
            [generacion['nombre'] for generacion in generaciones]
        )

        asesores = self.controlador.obtener_asesores()
        combo_asesor = crear_campo(
            form_frame, "Asesor:", 2, 1, 'combobox',
            [asesor['name'] for asesor in asesores]
        )

        self.asesores_data = {asesor['name']: asesor['id'] for asesor in asesores}

        areas = self.controlador.obtener_areas_conocimiento()
        combo_area = crear_campo(
            form_frame, "Área de Conocimiento:", 4, 1, 'combobox',
            [area['nombre'] for area in areas]
        )

        # --------- CARRERA: COMBO + "OTROS" ---------
        opciones_carrera = [
            "Maestría en Ingeniería para la Innovación y Desarrollo Tecnológico",
            "Doctorado en Ingeniería para la Innovación y Desarrollo Tecnológico",
            "Otros",
        ]

        combo_carrera = crear_campo(
            form_frame, "Carrera:", 5, 1, 'combobox', opciones_carrera
        )
        combo_carrera.state(["readonly"])

        entry_carrera_otro = crear_campo(
            form_frame,
            "Especifique carrera (si eligió 'Otros'):",
            6, 1,
            'entry'
        )
        entry_carrera_otro.config(state="disabled")

        def _on_carrera_change(event=None):
            opcion = combo_carrera.get().strip()
            if opcion == "Otros":
                entry_carrera_otro.config(state="normal")
                entry_carrera_otro.focus_set()
            else:
                entry_carrera_otro.delete(0, "end")
                entry_carrera_otro.config(state="disabled")

        combo_carrera.bind("<<ComboboxSelected>>", _on_carrera_change)

        # --------------------------
        # Sección de huella digital
        # --------------------------
        frame_huella = tk.LabelFrame(
            modal,
            text="Lector de Huella Dactilar",
            padx=10,
            pady=5,
            font=('Arial', 11, 'bold')
        )
        frame_huella.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 5))

        inner_frame = tk.Frame(frame_huella, padx=10, pady=5)
        inner_frame.pack(fill="x")

        tk.Label(inner_frame, text="Inicialice el lector:", font=('Arial', 12)).pack(pady=(5, 5))

        btn_escanear = tk.Button(
            inner_frame,
            text="ESCANEAR HUELLA",
            font=('Arial', 11, 'bold'),
            relief="solid",
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_escanear.pack(pady=(0, 5))

        lbl_estado = tk.Label(inner_frame, text="Esperando huella...", font=('Arial', 11), fg="blue")
        lbl_estado.pack(pady=(0, 5))

        def finalizar_escaneo():
            lbl_estado.config(text="Escaneo finalizado", fg="green")
            btn_escanear.config(state="normal")

        huella_digital = None

        def on_enroll(finger_idx, template):
            nonlocal huella_digital
            finalizar_escaneo()
            huella_digital = template
            print(f"Huella {finger_idx} registrada. Tamaño: {len(template)} bytes")

        btn_escanear.config(command=lambda: self.interface_api.register_fingerprint(on_enroll=on_enroll))

        # --------------------------
        # Función guardar
        # --------------------------
        def guardar():
            from tkinter import messagebox

            email = entry_email.get().strip()
            nombre = entry_nombre.get().strip()
            apellido_p = entry_apellido_p.get().strip()
            apellido_m = entry_apellido_m.get().strip()
            matricula = entry_matricula.get().strip()
            generacion = self.combo_generacion.get().strip()
            nombre_asesor = combo_asesor.get().strip()
            id_asesor = self.asesores_data.get(nombre_asesor)
            area_conocimiento = combo_area.get().strip()

            opcion_carrera = combo_carrera.get().strip()
            carrera_otro = entry_carrera_otro.get().strip()
            carrera = carrera_otro if opcion_carrera == "Otros" else opcion_carrera

            if not all([
                email, matricula, nombre, apellido_p, apellido_m,
                generacion, nombre_asesor, id_asesor, area_conocimiento, carrera
            ]):
                messagebox.showwarning("Campos vacíos", "Por favor, completa todos los campos.")
                return

            if not matricula.isdigit():
                messagebox.showerror("Error", "La matrícula debe contener solo números.")
                return

            patron_correo = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(patron_correo, email):
                messagebox.showerror(
                    "Correo inválido",
                    "El correo no tiene un formato válido.\nEjemplo: usuario@dominio.com"
                )
                entry_email.focus_set()
                return

            res = self.controlador.registrar_estudiante(
                email, matricula, nombre, apellido_p, apellido_m,
                huella_digital, generacion, area_conocimiento,
                carrera, nombre_asesor, id_asesor
            )

            if res in ("duplicado_matricula", "duplicado"):
                messagebox.showwarning(
                    "Matrícula duplicada",
                    f"La matrícula {matricula} ya está registrada."
                )
                entry_matricula.focus_set()
                return
            elif res == "duplicado_email":
                messagebox.showwarning(
                    "Correo ya registrado",
                    f"El correo {email} ya está registrado para otro estudiante."
                )
                entry_email.focus_set()
                return
            elif res == "duplicado_huella":
                messagebox.showwarning(
                    "Huella ya registrada",
                    "La huella capturada ya está asociada a otro estudiante."
                )
                return
            elif res is True:
                messagebox.showinfo(
                    "Estudiante registrado",
                    f"Email: {email}\n"
                    f"Nombre: {nombre} {apellido_p} {apellido_m}\n"
                    f"Matrícula: {matricula}\n"
                    f"Generación: {generacion}\n"
                    f"Asesor: {nombre_asesor}\n"
                    f"Área: {area_conocimiento}\n"
                    f"Carrera: {carrera}"
                )
                self._cargar_estudiantes_en_vista()
                modal.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    "Ocurrió un error al registrar al estudiante."
                )

        # --------------------------
        # Botón registrar
        # --------------------------
        btn_frame = tk.Frame(modal, pady=10)
        btn_frame.grid(row=2, column=0, columnspan=2)

        tk.Button(
            btn_frame,
            text="Registrar",
            bg="#2563eb",
            fg="white",
            font=('Arial', 12, 'bold'),
            command=guardar
        ).pack()


# ---------------------------------------- Contenido de la pestaña de asistencias ----------------------------------------
            
    def _on_tab_changed(self, event):
        """Se llama cuando se cambia de pestaña"""
        try:
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            if current_tab == "Asistencias":
                # Forzar la recarga de estudiantes
                if hasattr(self, 'controlador') and self.controlador:
                    # Cargar estudiantes sin mostrarlos en la vista (ya que lo haremos manualmente)
                    estudiantes = self.controlador.obtener_estudiantes_para_asistencia(mostrar_en_vista=False)
                    if estudiantes is not None:
                        self.mostrar_estudiantes(estudiantes)    
                # Actualizar la tabla de asistencias
                self._actualizar_asistencias_hoy()
            elif current_tab == "Reportes":
                # Forzar la recarga de estudiantes en el combobox de reportes
                if hasattr(self, 'controlador') and self.controlador:
                    # Cargar estudiantes en el combobox de reportes
                    self.cargar_estudiantes_reportes()
        except Exception as e:
            print(f"Error al cambiar de pestaña: {e}")
            traceback.print_exc()
    

    def _contenido_control_asistencias(self, parent):
        # Título principal
        tk.Label(parent, text="Control de Asistencias", bg="lightblue", fg="#1a253c",
                 font=('Arial', 24, 'bold')).pack(anchor="nw", padx=30, pady=30)

        main_frame = tk.Frame(parent, bg="lightblue")
        main_frame.pack(fill="both", expand=True, padx=10, pady=0)

        # Panel izquierdo: Lector de Huella Digital
        panel_lector = tk.Frame(main_frame, height=350, width=400, bg="white", bd=2, relief="groove")
        panel_lector.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        panel_lector.pack_propagate(False)  # Esto evita que el frame se ajuste a su contenido
        tk.Label(panel_lector, text="🖐 Lector de Huella Digital", font=("Arial", 14, "bold"), bg="white", fg="#1565c0").pack(anchor="w", padx=10, pady=10)

        # Icono huella
        try:
            img = Image.open(resource_path("public/static/icons/huella-dactilar.png"))
            img = img.resize((100, 100), Image.LANCZOS)
            icono_huella = ImageTk.PhotoImage(img)
            tk.Label(panel_lector, image=icono_huella, bg="white").pack(pady=10)
            panel_lector.icono_huella = icono_huella
        except Exception:
            tk.Label(panel_lector, text="🖐", font=("Arial", 48), bg="white").pack(pady=10)


        # Método para manejar el resultado de la verificación
        def manejar_verificacion_huella():
            try:
                # 1) Obtener estudiantes con huella desde el controlador
                estudiantes = self.controlador.obtener_estudiantes_para_asistencia()
                if not estudiantes:
                    messagebox.showwarning("Advertencia", "No hay estudiantes con huella registrada.")
                    return

                # 2) Verificar huella usando la interfaz biométrica
                matching_student = self.interface_api.verify_fingerprint(estudiantes)

                if not matching_student:
                    self.mostrar_notificacion_rapida(
                        "Huella no reconocida",
                        color_fondo="#dc2626"
                    )
                    return

                estudiante = matching_student
                estudiante_id = estudiante["id"]

                # 3) Ver qué tiene hoy el estudiante
                ultima = self.controlador.modelo.obtener_ultima_asistencia_hoy(estudiante_id)

                from datetime import datetime, timedelta, time
                ahora = datetime.now()

                #
                # === CASO A: NO TIENE ENTRADA HOY ===
                #
                if not ultima or not ultima.get("hora_entrada"):
                    if self.controlador.verificar_asistencia_existente(estudiante_id):
                        self.mostrar_notificacion_rapida(
                            "Ya registraste tu asistencia hoy.",
                            color_fondo="#f97316"
                        )
                        return

                    if self.controlador.registrar_asistencia(estudiante_id):
                        self._actualizar_asistencias_hoy()
                        self.mostrar_notificacion_rapida("Ingreso exitoso", "#16a34a")
                    else:
                        self.mostrar_notificacion_rapida("Error al registrar ingreso", "#dc2626")
                    return

                #
                # === CASO B: YA TIENE ENTRADA Y SALIDA ===
                #
                if ultima.get("hora_salida"):
                    self.mostrar_notificacion_rapida(
                        "Ya registraste entrada y salida hoy.",
                        color_fondo="#f97316"
                    )
                    return

                #
                # === CASO C: TIENE ENTRADA PERO NO SALIDA ===
                #
                fecha_reg = ultima["asistencia"]
                hora_ent = ultima["hora_entrada"]

                # Normalizar la fecha
                if hasattr(fecha_reg, "date"):
                    fecha_reg = fecha_reg.date()

                # Normalizar la hora (puede ser time, timedelta o str)
                if isinstance(hora_ent, time):
                    hora_ent_time = hora_ent
                elif isinstance(hora_ent, timedelta):
                    hora_ent_time = (datetime.min + hora_ent).time()
                else:
                    # Intento de convertir cadena HH:MM(:SS)
                    try:
                        hora_ent_time = datetime.strptime(str(hora_ent), "%H:%M:%S").time()
                    except:
                        hora_ent_time = datetime.strptime(str(hora_ent), "%H:%M").time()

                dt_entrada = datetime.combine(fecha_reg, hora_ent_time)

                # Reglas del minuto mínimo
                if ahora - dt_entrada < timedelta(hours=4):
                    self.mostrar_notificacion_rapida(
                        "Debes esperar al menos 4 horas desde tu entrada para marcar salida.",
                        color_fondo="#dc2626"
                    )
                    return

                # Registrar salida
                if self.controlador.registrar_salida(ultima["id"]):
                    self._actualizar_asistencias_hoy()
                    self.mostrar_notificacion_rapida("Salida exitosa", "#0ea5e9")
                else:
                    self.mostrar_notificacion_rapida("Error al registrar salida", "#dc2626")

            except Exception as e:
                print(f"Error en manejo de verificación de huella: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", "Ocurrió un error al procesar la huella.")


        # Botón escanear huella
        btn_escanear = tk.Button(panel_lector, text="Escanear Huella", font=("Arial", 12, "bold"),
                                bg="#2563eb", fg="white", relief="flat", height=2, cursor="hand2",
                                command=manejar_verificacion_huella)
        btn_escanear.pack(fill="x", padx=10, pady=10)
        
         # NUEVO: Botón Incidencias (debajo del lector)
        btn_incidencias = tk.Button(
            panel_lector,
            text="Incidencias",
            font=("Arial", 11, "bold"),
            bg="#f97316",
            fg="white",
            relief="flat",
            height=1,
            cursor="hand2",
            command=self._abrir_modal_incidencias   # función que abre el modal
        )
        btn_incidencias.pack(fill="x", padx=10, pady=(0, 10))

        # Panel derecho: Asistencias de Hoy
        self.panel_asistencias = tk.Frame(main_frame, bg="white", bd=2, relief="groove")
        self.panel_asistencias.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Configurar el grid para que el panel sea responsivo
        self.panel_asistencias.grid_columnconfigure(0, weight=1)
        # self.panel_asistencias.grid_columnconfigure(1, minsize=640)
        self.panel_asistencias.grid_rowconfigure(1, weight=1)
        
        # Título y botón de actualizar
        frame_titulo = tk.Frame(self.panel_asistencias, bg="white")
        frame_titulo.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        tk.Label(frame_titulo, text="⏰ Asistencias de Hoy", 
                font=("Arial", 14, "bold"), 
                bg="white", fg="#1a253c").pack(side="left")
                
        btn_actualizar = tk.Button(frame_titulo, text="🔄", font=("Arial", 10),
                                 command=self._actualizar_asistencias_hoy,
                                 bd=0, bg="white", cursor="hand2")
        btn_actualizar.pack(side="right", padx=5)
        
        # Crear el Treeview con scrollbar
        frame_tabla = tk.Frame(self.panel_asistencias, bg="white")
        frame_tabla.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configurar scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")
        
        # Crear el Treeview con las columnas necesarias
        self.tree_asistencias = ttk.Treeview(
            frame_tabla, 
            columns=("id", "nombre", "hora_entrada", "hora_salida"), 
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )

        
        # Configurar las columnas
        columnas = [
            ("id", "ID", 0, "w"),  # Columna oculta para el ID
            ("nombre", "Estudiante", 130, "w"),
            ("hora_entrada", "Hora de Entrada", 30, "center"),
            ("hora_salida", "Hora de Salida", 30, "center")
        ]
        
        for col_id, heading, width, anchor in columnas:
            self.tree_asistencias.heading(col_id, text=heading, anchor=anchor)
            self.tree_asistencias.column(
                col_id, 
                width=width, 
                anchor=anchor, 
                stretch=tk.NO if col_id == "id" else tk.YES
            )
        
        
        
        self.tree_asistencias.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.tree_asistencias.yview)
        
        # Cargar las asistencias iniciales
        self._actualizar_asistencias_hoy()

        # Configurar el grid principal
        main_frame.grid_columnconfigure(0, minsize=400)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, minsize=300)
        main_frame.grid_rowconfigure(0, weight=1)

    def _abrir_modal_incidencias(self):
        """
        1) Pide huella de la persona.
        2) Muestra sus asistencias con entrada pero sin salida.
        3) Permite registrar salida manual + motivo de incidencia.
        """
        from tkinter import ttk
        import datetime

        # 1. Verificar huella de la persona
        try:
            # Usa el mismo método que asistencia para obtener personas con huella
            personas = self.controlador.obtener_estudiantes_para_asistencia()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener las huellas:\n{e}")
            return

        if not personas:
            messagebox.showwarning("Sin datos", "No hay personas con huella registrada.")
            return

        try:
            matching = self.interface_api.verify_fingerprint(personas)
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar la huella:\n{e}")
            return

        if not matching:
            messagebox.showerror("Acceso denegado", "Huella no reconocida.")
            return

        # Ajusta la clave según tu dict (id, alumno_id, etc.)
        alumno_id = matching.get("id") or matching.get("alumno_id")

        if not alumno_id:
            messagebox.showerror("Error", "No se pudo identificar al alumno asociado a la huella.")
            return

        # 2. Obtener asistencias sin salida
        asistencias = self.controlador.obtener_asistencias_sin_salida_por_alumno(alumno_id)
        if not asistencias:
            messagebox.showinfo(
                "Incidencias",
                "Esta persona no tiene asistencias con entrada sin salida registrada."
            )
            return

        # 3. Crear modal
        modal = tk.Toplevel(self.ventana)
        modal.title("Incidencias - Salida manual")
        modal.geometry("650x400")
        modal.transient(self.ventana)
        modal.grab_set()

        # Centrar
        modal.update_idletasks()
        ancho, alto = 650, 400
        x = (modal.winfo_screenwidth() // 2) - (ancho // 2)
        y = (modal.winfo_screenheight() // 2) - (alto // 2)
        modal.geometry(f"{ancho}x{alto}+{x}+{y}")

        frame = tk.Frame(modal, bg="#f3f4f6")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            frame,
            text="Asistencias con entrada sin salida",
            bg="#f3f4f6",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Treeview con asistencias
        cols = ("id", "fecha", "hora_entrada", "hora_salida", "motivo_incidencia")
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        tv.heading("id", text="ID")
        tv.heading("fecha", text="Fecha")
        tv.heading("hora_entrada", text="Hora entrada")
        tv.heading("hora_salida", text="Hora salida")
        tv.heading("motivo_incidencia", text="Motivo incidencia")

        tv.column("id", width=50, anchor="center")
        tv.column("fecha", width=90, anchor="center")
        tv.column("hora_entrada", width=90, anchor="center")
        tv.column("hora_salida", width=90, anchor="center")
        tv.column("motivo_incidencia", width=200, anchor="w")

        tv.pack(fill="x", padx=5)

        # Cargar datos
        def cargar_asistencias():
            tv.delete(*tv.get_children())
            for a in asistencias:
                tv.insert(
                    "",
                    "end",
                    values=(
                        a["id"],
                        a["fecha"],
                        a.get("hora_entrada") or "",
                        a.get("hora_salida") or "",
                        a.get("motivo_incidencia") or "",
                    )
                )

        cargar_asistencias()

        # Área de edición salida + motivo
        edit_frame = tk.Frame(frame, bg="#f3f4f6")
        edit_frame.pack(fill="x", pady=(15, 0))

        tk.Label(
            edit_frame,
            text="Hora de salida manual:",
            bg="#f3f4f6",
            font=("Arial", 10)
        ).grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)

        entry_hora_salida = tk.Entry(edit_frame, width=10, font=("Arial", 10))
        entry_hora_salida.grid(row=0, column=1, sticky="w", pady=2)

        # Por defecto, hora actual
        ahora = datetime.datetime.now().strftime("%H:%M:%S")
        entry_hora_salida.insert(0, ahora)

        tk.Label(
            edit_frame,
            text="Motivo de incidencia:",
            bg="#f3f4f6",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)

        motivos = [
            "Vista de campo (obra)",
            "Coordinación cerrada",
            "Clases en línea",
        ]
        combo_motivo = ttk.Combobox(
            edit_frame,
            values=motivos,
            state="readonly",
            width=30
        )
        combo_motivo.grid(row=1, column=1, sticky="w", pady=2)

        # Solo una opción seleccionable (readonly ya lo garantiza)

        def guardar_salida_manual():
            sel = tv.selection()
            if not sel:
                messagebox.showwarning(
                    "Selecciona una asistencia",
                    "Primero selecciona una asistencia de la lista."
                )
                return

            item = tv.item(sel[0])
            asistencia_id = item["values"][0]

            hora_salida = entry_hora_salida.get().strip()
            if not hora_salida:
                messagebox.showwarning(
                    "Hora de salida",
                    "Debes ingresar la hora de salida."
                )
                return

            motivo = combo_motivo.get().strip()
            if not motivo:
                messagebox.showwarning(
                    "Motivo de incidencia",
                    "Debes seleccionar un motivo de incidencia."
                )
                return

            ok = self.controlador.registrar_salida_manual_con_incidencia(
                asistencia_id,
                hora_salida,
                motivo
            )
            if ok:
                messagebox.showinfo(
                    "Salida registrada",
                    "La salida manual y el motivo de incidencia se han guardado correctamente."
                )
                # actualizar lista local y volver a cargar
                for a in asistencias:
                    if a["id"] == asistencia_id:
                        a["hora_salida"] = hora_salida
                        a["motivo_incidencia"] = motivo
                cargar_asistencias()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar la salida manual con incidencia."
                )

        btn_guardar = tk.Button(
            frame,
            text="Guardar salida manual",
            bg="#16a34a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            command=guardar_salida_manual
        )
        btn_guardar.pack(pady=(15, 0))

    def _registrar_salida(self, registro_id, item_id):
        """
        Maneja el evento de clic en el botón de registrar salida.
        Se puede usar tanto para registrar una nueva salida como para actualizar una existente.
        """
        # Obtener la información del estudiante desde el Treeview
        values = self.tree_asistencias.item(item_id, 'values')
        if not values or len(values) < 2:  # Asegurarse de que hay al menos ID y nombre
            messagebox.showerror("Error", "No se pudo obtener la información del estudiante")
            return
            
        nombre_estudiante = values[1]  # El nombre está en la segunda columna
        
        # Mostrar diálogo de confirmación
        confirmar = messagebox.askyesno(
            "Confirmar salida",
            f"¿Desea registrar la salida de {nombre_estudiante}?\n\n"
            "Se requerirá la verificación de huella digital para continuar.",
            icon='question'
        )
        
        if not confirmar:
            return
            
        # Obtener el ID del estudiante del registro de asistencia
        if not hasattr(self, 'controlador') or not self.controlador:
            messagebox.showerror("Error", "No se puede acceder al controlador")
            return
            
        # Obtener el ID del estudiante desde el registro de asistencia
        asistencia_info = self.controlador.obtener_asistencia_por_id(registro_id)
        if not asistencia_info or len(asistencia_info) < 6:  # Asegurarse de que tenemos suficiente información
            messagebox.showerror("Error", "No se pudo obtener la información de la asistencia")
            return
            
        estudiante_id = asistencia_info[1]  # El ID del estudiante debería estar en la segunda posición
        
        # Obtener la plantilla de huella del estudiante
        huella_template = self.controlador.obtener_huella_estudiante(estudiante_id)
        if not huella_template:
            messagebox.showerror("Error", "El estudiante no tiene una huella registrada")
            return
            
        # Verificar la huella
        if not hasattr(self, 'interface_api') or not self.interface_api:
            messagebox.showerror("Error", "No se puede acceder al lector de huellas")
            return
            
        if not self.verificar_huella_salida(huella_template):
            messagebox.showwarning("Verificación fallida", "No se pudo verificar la huella digital")
            return
            
        # Registrar la salida
        if self.controlador.registrar_salida(registro_id):
            messagebox.showinfo("Éxito", f"Hora de salida registrada correctamente para {nombre_estudiante}")
            self._actualizar_asistencias_hoy()
        else:
            messagebox.showerror("Error", "No se pudo registrar la hora de salida")
    

    def _on_motion(self, event):
        """Maneja los efectos hover sobre los elementos clickeables"""
        # Resetear el estilo de todos los ítems
        for item in self.tree_asistencias.get_children():
            tags = self.tree_asistencias.item(item, 'tags')
            if 'hover' in tags:
                self.tree_asistencias.item(item, tags=('clickable',) if 'clickable' in tags else ())
        
        # Verificar si estamos sobre una celda de acción
        region = self.tree_asistencias.identify_region(event.x, event.y)
        column = self.tree_asistencias.identify_column(event.x)
        item = self.tree_asistencias.identify_row(event.y)
        
        # Verificar si estamos sobre una celda clickeable (columna de acción)
        if region == "cell" and column == "#5" and item:
            values = self.tree_asistencias.item(item, 'values')
            if values and len(values) > 4 and "REGISTRAR SALIDA" in values[4]:
                self.tree_asistencias.config(cursor="hand2")
                # Aplicar estilo hover
                self.tree_asistencias.item(item, tags=('clickable', 'hover'))
                return
        
        # Si no está sobre un elemento clickeable, restaurar el cursor por defecto
        self.tree_asistencias.config(cursor="")


    def verificar_huella_salida(self, huella_template):
        """Verifica la huella digital del estudiante"""
        try:
            if not hasattr(self, 'interface_api') or not self.interface_api:
                return False
            
            # Esperar un momento para que se muestre el mensaje
            self.ventana.update()
            
            # Realizar la verificación
            return self.interface_api.verificar_huella_salida(huella_template)
        except Exception as e:
            print(f"Error en verificación de huella: {e}")
            return False
            

    def _on_button_click(self, event):
        """Maneja el clic en el texto de registrar salida"""
        # Identificar la región, columna y ítem clickeado
        region = self.tree_asistencias.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree_asistencias.identify_column(event.x)
        if column != "#5":  # Si no es la columna de acción (columna 5)
            return
            
        item = self.tree_asistencias.identify_row(event.y)
        if not item:
            return
            
        # Obtener los valores del ítem
        values = self.tree_asistencias.item(item, 'values')
        if not values or len(values) < 5:
            return
            
        # Obtener el ID del registro y la acción
        registro_id = values[0]  # El ID está en la primera columna (oculta)
        accion = values[4] if len(values) > 4 else ""
        
        # Verificar que estamos haciendo clic en el botón de registrar salida
        if not accion.strip() or "REGISTRAR SALIDA" not in accion:
            return
            
        # Aplicar estilo de botón presionado
        self.tree_asistencias.item(item, tags=('clickable', 'active'))
        
        # Restaurar el estilo hover después de un breve retraso
        self.ventana.after(150, lambda: self.tree_asistencias.item(item, tags=('clickable', 'hover')))
        
        # Registrar o actualizar la salida
        self._registrar_salida(registro_id, item)
    
    
    def _actualizar_asistencias_hoy(self):
        """
        Actualiza la tabla de asistencias del día con los registros más recientes.
        """
        if not hasattr(self, 'tree_asistencias'):
            print("Error: tree_asistencias no está definido")
            return

        # Limpiar tabla
        for item in self.tree_asistencias.get_children():
            self.tree_asistencias.delete(item)

        # Validar controlador
        if not hasattr(self, 'controlador') or not self.controlador:
            print("Error: Controlador no disponible")
            self.tree_asistencias.insert("", "end", values=("Error: Controlador no disponible", "", "", ""))
            return

        try:
            # Obtener asistencias del día
            asistencias = self.controlador.obtener_asistencias_hoy()

            if not asistencias:
                self.tree_asistencias.insert("", "end",
                    values=("No hay asistencias registradas hoy", "", "", ""))
                return

            # Procesar asistencias
            for asistencia in asistencias:
                try:
                    registro_id = asistencia[0]
                    nombre = asistencia[1] if len(asistencia) > 1 else ""
                    apellido_p = asistencia[2] if len(asistencia) > 2 else ""
                    apellido_m = asistencia[3] if len(asistencia) > 3 else ""
                    hora_entrada = asistencia[4] if len(asistencia) > 4 else ""
                    hora_salida = asistencia[5] if len(asistencia) > 5 else ""

                    nombre_completo = f"{nombre} {apellido_p} {apellido_m}".strip()

                    # Formateo de horas
                    def formatear_hora(hora):
                        if not hora:
                            return ""
                        if isinstance(hora, str):
                            return hora.split()[-1][:8] if " " in hora else hora[:8]
                        if hasattr(hora, "strftime"):
                            return hora.strftime("%H:%M:%S")
                        return str(hora)

                    hora_entrada_fmt = formatear_hora(hora_entrada)
                    hora_salida_fmt = formatear_hora(hora_salida)

                    # Insertar fila sin columna de acción
                    self.tree_asistencias.insert(
                        "",
                        "end",
                        values=(
                            registro_id,
                            nombre_completo,
                            hora_entrada_fmt,
                            hora_salida_fmt
                        )
                    )

                except Exception as e:
                    print(f"Error al procesar asistencia: {e}")
                    traceback.print_exc()
                    continue

        except Exception as e:
            print(f"Error al actualizar asistencias: {e}")
            traceback.print_exc()
            self.tree_asistencias.insert("", "end",
                values=(f"Error: {str(e)}", "", "", ""))


    def mostrar_notificacion_rapida(self, texto, color_fondo="#16a34a"):
        """
        Muestra un recuadro pequeño durante 1 segundo (tipo 'toast').
        """
        import tkinter as tk  # por si no está al inicio

        win = tk.Toplevel(self.ventana)
        win.overrideredirect(True)        # sin bordes
        win.configure(bg=color_fondo)

        label = tk.Label(
            win,
            text=texto,
            bg=color_fondo,
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10
        )
        label.pack()

        # Posición: centrado arriba de la ventana principal
        self.ventana.update_idletasks()
        x = self.ventana.winfo_rootx() + (self.ventana.winfo_width() - win.winfo_reqwidth()) // 2
        y = self.ventana.winfo_rooty() + 80
        win.geometry(f"+{x}+{y}")

        # Cerrar solo
        win.after(2000, win.destroy)


# ---------------------------------------- Contenido de la pestaña reportes ----------------------------------------

    def _actualizar_filtros(self):
        """Actualiza la interfaz según el tipo de filtro seleccionado"""
        if self.tipo_filtro.get() == "mes":
            # Mostrar controles de mes/año y ocultar rango personalizado
            self.frame_mes_anio.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.frame_rango.pack_forget()
            
            # Habilitar controles de mes/año
            self.combo_mes['state'] = 'readonly'
            self.combo_anio['state'] = 'readonly'
        else:  # rango personalizado
            # Mostrar controles de rango personalizado y ocultar mes/año
            self.frame_mes_anio.pack_forget()
            self.frame_rango.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Deshabilitar controles de mes/año
            self.combo_mes['state'] = 'disabled'
            self.combo_anio['state'] = 'disabled'
    
    def _contenido_reportes(self, parent):
        # Título
        tk.Label(parent, text="Reportes", bg="lightblue", fg="#1a253c",
                font=('Arial', 24, 'bold')).place(x=30, y=30)

        # Frame para los controles de búsqueda
        frame_busqueda = tk.Frame(parent, bg="lightblue", width=1040)
        frame_busqueda.place(x=30, y=90, height=120)

        # Frame para los filtros
        frame_filtros = tk.Frame(frame_busqueda, bg="lightblue")
        frame_filtros.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # Variable para el tipo de filtro
        self.tipo_filtro = tk.StringVar(value="mes")

        # Radio button para mes/año
        rb_mes = tk.Radiobutton(
            frame_filtros,
            text="Filtrar por mes/año:",
            variable=self.tipo_filtro,
            value="mes",
            bg="lightblue",
            command=self._actualizar_filtros
        )
        rb_mes.pack(side=tk.LEFT, padx=(0, 10))

        # Radio button para rango personalizado
        rb_rango = tk.Radiobutton(
            frame_filtros,
            text="Rango personalizado:",
            variable=self.tipo_filtro,
            value="rango",
            bg="lightblue",
            relief="flat",
            command=self._actualizar_filtros
        )
        rb_rango.pack(side=tk.LEFT, padx=(20, 10))

        # Frame para los controles de mes/año
        self.frame_mes_anio = tk.Frame(frame_filtros, bg="lightblue")
        self.frame_mes_anio.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Selector de mes
        self.meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        self.combo_mes = ttk.Combobox(
            self.frame_mes_anio,
            values=self.meses,
            font=('Arial', 10),
            state="readonly",
            width=12
        )
        self.combo_mes.current(datetime.now().month - 1)  # Mes actual
        self.combo_mes.pack(side=tk.LEFT, padx=(0, 10))

        # Selector de año
        self.anios = [str(year) for year in range(datetime.now().year - 2, datetime.now().year + 6)]
        self.combo_anio = ttk.Combobox(
            self.frame_mes_anio,
            values=self.anios,
            font=('Arial', 10),
            state="readonly",
            width=6
        )
        self.combo_anio.set(str(datetime.now().year))  # Año actual
        self.combo_anio.pack(side=tk.LEFT)

        # Frame para los selectores de fecha
        self.frame_rango = tk.Frame(frame_filtros, bg="lightblue")
        self.frame_rango.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Fecha de inicio
        tk.Label(self.frame_rango, text="Desde:", bg="lightblue").pack(side=tk.LEFT, padx=(0, 5))
        self.fecha_inicio = ttk.Entry(self.frame_rango, width=12, font=('Arial', 10))
        self.fecha_inicio.pack(side=tk.LEFT)
        self.fecha_inicio.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Fecha de fin
        tk.Label(self.frame_rango, text="Hasta:", bg="lightblue").pack(side=tk.LEFT, padx=(10, 5))
        self.fecha_fin = ttk.Entry(self.frame_rango, width=12, font=('Arial', 10))
        self.fecha_fin.pack(side=tk.LEFT)
        self.fecha_fin.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Deshabilitar inicialmente el frame de rango
        self.frame_rango.pack_forget()

        # Frame para la búsqueda de estudiante
        frame_busqueda_est = tk.Frame(frame_busqueda, bg="lightblue")
        frame_busqueda_est.pack(side=tk.TOP, fill=tk.X)

        # Etiqueta del campo
        tk.Label(frame_busqueda_est, text="Selecciona un estudiante:",
                bg="lightblue", fg="#1a253c",
                font=('Arial', 12)).pack(side=tk.LEFT, padx=(0, 10))

        # -------- AUTOCOMPLETADO (reemplaza al Combobox) --------
        def _fetch_estudiantes(q):
            # Busca por nombre, apellidos, nombre completo, matrícula o email
            try:
                return self.controlador.buscar_estudiantes(q, limit=20)
            except Exception as e:
                print("Error buscando estudiantes:", e)
                return []

        def _on_select_est(item):
            # Guarda el estudiante seleccionado para usarlo en “Buscar” y reportes
            self._estudiante_sel = item  # {'id','nombre','matricula','email'}

        self.entry_estudiante = AutocompleteEntry(
            frame_busqueda_est,
            fetch_callback=_fetch_estudiantes,
            on_select=_on_select_est,
            width=40
        )
        self.entry_estudiante.insert(0, "Buscar estudiante...")
        self.entry_estudiante.bind(
            "<FocusIn>",
            lambda e: self.entry_estudiante.delete(0, "end")
            if self.entry_estudiante.get().startswith("Buscar")
            else None
        )
        self.entry_estudiante.pack(side=tk.LEFT, padx=(0, 0))
        # Ejecutar búsqueda al presionar Enter
        self.entry_estudiante.bind("<Return>", lambda e: self.buscar_estudiante_reportes())
        # --------------------------------------------------------

        # Botón de buscar (usa el mismo flujo que Enter)
        btn_buscar = tk.Button(
            frame_busqueda_est,
            text="Buscar",
            bg="#2563eb",
            fg="white",
            font=('Arial', 12, 'bold'),
            cursor="hand2",
            relief="flat",
            width=10,
            command=self.buscar_estudiante_reportes
        )
        btn_buscar.pack(side=tk.LEFT, padx=(10, 5))

        # Botón de Reporte General
        btn_reporte_general = tk.Button(
            frame_busqueda_est,
            text="Reporte General",
            bg="#059669",
            fg="white",
            font=('Arial', 12, 'bold'),
            cursor="hand2",
            relief="flat",
            command=self.mostrar_reporte_general
        )
        btn_reporte_general.pack(side=tk.LEFT, padx=5)

        # Atributo para rastrear la vista actual
        self.vista_actual = "inicio"  # Puede ser 'inicio', 'estudiante' o 'general'

        # Frame para los botones de acción
        frame_acciones = tk.Frame(frame_busqueda_est, bg="lightblue")
        frame_acciones.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Botón de exportar PDF/XLS
        #self.btn_exportar = tk.Button(
            #frame_acciones,
            #text="Exportar",
            #bg="#7c3aed",
            #fg="white",
            #font=('Arial', 12, 'bold'),
            #cursor="hand2",
            #relief="flat",
            #command=self._manejar_exportacion
        #)
        #self.btn_exportar.pack(side=tk.LEFT, padx=(0, 5))
        #self.btn_exportar.config(state=tk.DISABLED)  # Deshabilitado inicialmente
        
        # Botón de aistencia del dia 
        btn_ver_dia = tk.Button(
            frame_acciones,
            text="Ver Asistencias del Día",
            bg="#f59e0b",
            fg="white",
            font=('Arial', 12, 'bold'),
            cursor="hand2",
            relief="flat",
            width=20,
            command=self.abrir_ventana_asistencias_dia
        )
        btn_ver_dia.pack(side=tk.LEFT, padx=(10, 0))

        # Botón por generación
        btn_por_generacion = tk.Button(
            frame_acciones,
            text="Generaciones",
            bg="#10b981",
            fg="white",
            font=('Arial', 12, 'bold'),
            cursor="hand2",
            relief="flat",
            width=16,
            command=self._abrir_reporte_generacion
        )
        btn_por_generacion.pack(side=tk.LEFT, padx=(10, 0))

        # Área de mensaje central (se muestra cuando no hay estudiante seleccionado)
        self.frame_mensaje_central = tk.Frame(parent, bg="lightblue")
        self.frame_mensaje_central.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)

        # Cargar y mostrar el ícono
        try:
            imagen = Image.open(resource_path("public/static/icons/informe.png"))
            imagen = imagen.resize((100, 100), Image.LANCZOS)
            self.icono_reporte = ImageTk.PhotoImage(imagen)
            icono_label = tk.Label(self.frame_mensaje_central, image=self.icono_reporte, bg="lightblue")
            icono_label.pack(pady=(0, 20))
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            tk.Label(self.frame_mensaje_central, text="📊", bg="lightblue", font=('Arial', 60)).pack(pady=(0, 20))

        # Mensaje central
        tk.Label(
            self.frame_mensaje_central,
            text="No hay ningún estudiante seleccionado",
            bg="lightblue",
            fg="#6b7280",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 10))

        # Subtítulo
        tk.Label(
            self.frame_mensaje_central,
            text="Selecciona un estudiante para ver su reporte detallado",
            bg="lightblue",
            fg="#6b7280",
            font=('Arial', 12)
        ).pack()

        # Frame para el reporte (inicialmente oculto)
        self.frame_reporte = tk.Frame(parent, bg="white", bd=1, relief="solid")
        self.frame_reporte.pack(fill="both", expand=True, padx=30, pady=(170, 30), anchor="nw")
        self.frame_reporte.pack_forget()  # Ocultar inicialmente

        # Configurar el grid para ser responsivo
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        self.frame_reporte.grid_rowconfigure(0, weight=1)
        self.frame_reporte.grid_columnconfigure(0, weight=1)
        
    
    def _buscar_estudiante_autocomplete(self):
        """Genera el reporte del estudiante seleccionado o, si no hay selección,
        busca por el texto escrito y resuelve automáticamente, y MUESTRA el panel."""
        sel = getattr(self, "_estudiante_sel", None)
        texto = (self.entry_estudiante.get() or "").strip()

        if not sel:
            if not texto:
                messagebox.showinfo("Atención", "Escribe el nombre, matrícula o correo del estudiante.")
                return
            try:
                resultados = self.controlador.buscar_estudiantes(texto, limit=10) or []
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo buscar estudiantes:\n{e}")
                return

            if len(resultados) == 0:
                messagebox.showinfo("Sin resultados", f"No se encontró ningún estudiante para: “{texto}”.")
                return
            elif len(resultados) == 1:
                sel = resultados[0]
                self._estudiante_sel = sel
            else:
                # Si quieres un diálogo para elegir uno, aquí.
                sel = resultados[0]
                self._estudiante_sel = sel

        try:
            # === DIFERENCIA CLAVE: asegúrate de mostrar el frame del reporte ===
            self.vista_actual = 'estudiante'
            #self.btn_exportar.config(state=tk.NORMAL, text="Exportar Reporte")

            # Oculta el mensaje central si está visible
            if hasattr(self, 'frame_mensaje_central') and self.frame_mensaje_central.winfo_ismapped():
                self.frame_mensaje_central.place_forget()

            # Limpia y (re)empaqueta el contenedor del reporte
            if hasattr(self, 'frame_reporte'):
                for w in self.frame_reporte.winfo_children():
                    w.destroy()
            else:
                self.frame_reporte = tk.Frame(self.ventana, bg="white")
            # SIEMPRE volver a empacar (estaba oculto con pack_forget)
            self.frame_reporte.pack(fill="both", expand=True, padx=30, pady=(170, 30), anchor="nw")

            # Filtros de fecha
            mes  = self.combo_mes.current() + 1 if self.tipo_filtro.get() == "mes" else None
            anio = int(self.combo_anio.get()) if self.tipo_filtro.get() == "mes" else None
            fi   = self.fecha_inicio.get() if self.tipo_filtro.get() == "rango" else None
            ff   = self.fecha_fin.get() if self.tipo_filtro.get() == "rango" else None

            # Pinta la cabecera e indicadores
            self._mostrar_informacion_estudiante(sel)
            self._mostrar_estadisticas(
                sel['id'],
                mes=mes, anio=anio,
                fecha_inicio=fi, fecha_fin=ff
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")

 
    def _mostrar_informacion_estudiante(self, estudiante):
        """Muestra la información del estudiante en el reporte, con botones fijos PDF/Excel a la derecha"""
        
        # Obtener los datos del estudiante según el formato
        if isinstance(estudiante, dict):
            nombre = estudiante.get('nombre', '')
            apellido_p = estudiante.get('apellido_p', estudiante.get('apellido_paterno', ''))
            apellido_m = estudiante.get('apellido_m', estudiante.get('apellido_materno', ''))
            matricula = estudiante.get('matricula', 'N/A')
            email = estudiante.get('email', 'N/A')
            generacion = estudiante.get('generacion', 'N/A')
            asesor = estudiante.get('asesor', 'N/A')
            area_conocimiento = estudiante.get('area_conocimiento', 'N/A')
            carrera = estudiante.get('carrera', 'N/A')
        
        # Limpiar y formatear los datos
        nombre_completo = f"{nombre} {apellido_p} {apellido_m}".strip()
        matricula = str(matricula) if matricula and matricula != 'N/A' else 'N/A'
        email = email if email and email != 'N/A' else 'No disponible'
        generacion = generacion if generacion is not None else 'N/A'
        asesor = asesor if asesor is not None else 'N/A'
        area_conocimiento = area_conocimiento if area_conocimiento is not None else 'N/A'
        carrera = carrera if carrera is not None else 'N/A'
        
        # ----- CONTENEDOR SUPERIOR: info alumno + botones de exportación -----
        header_frame = tk.Frame(self.frame_reporte, bg="white")
        header_frame.pack(fill="x", padx=20, pady=10, anchor="w")
        
        # Frame con la información del estudiante (izquierda)
        info_frame = tk.Frame(header_frame, bg="white")
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Nombre
        tk.Label(
            info_frame, text=nombre_completo,
            font=('Arial', 18, 'bold'), bg="white"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 10))
        
        # Configurar grid para las dos columnas
        info_frame.columnconfigure(0, weight=1, pad=10)
        info_frame.columnconfigure(1, weight=1, pad=10)

        # Columna izquierda (datos básicos)
        tk.Label(
            info_frame, text=f"Matrícula: {matricula}",
            font=('Arial', 12), bg="white"
        ).grid(row=1, column=0, sticky="w", pady=2)

        tk.Label(
            info_frame, text=f"Email: {email}",
            font=('Arial', 12), bg="white"
        ).grid(row=2, column=0, sticky="w", pady=2)

        tk.Label(
            info_frame, text=f"Generación: {generacion}",
            font=('Arial', 12), bg="white"
        ).grid(row=3, column=0, sticky="w", pady=2)

        # Columna derecha (datos académicos)
        tk.Label(
            info_frame, text=f"Asesor: {asesor}",
            font=('Arial', 12), bg="white"
        ).grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(
            info_frame, text=f"Área: {area_conocimiento}",
            font=('Arial', 12), bg="white"
        ).grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(
            info_frame, text=f"Carrera: {carrera}",
            font=('Arial', 12), bg="white"
        ).grid(row=3, column=1, sticky="w", pady=2)

        # ----- BOTONES FIJOS A LA DERECHA (en el espacio rojo de tu captura) -----
                # ----- BOTONES FIJOS A LA DERECHA (en el espacio rojo de tu captura) -----
        botones_frame = tk.Frame(header_frame, bg="white")
        botones_frame.pack(side="right", padx=10, pady=10)

        # Texto arriba de los botones
        tk.Label(
            botones_frame,
            text="¿En qué formato deseas exportar?",
            bg="white",
            fg="#111827",
            font=('Arial', 10, 'bold')
        ).pack(pady=(0, 8))

        # Fila para los dos botones (PDF a la izquierda, Excel a la derecha)
        fila_botones = tk.Frame(botones_frame, bg="white")
        fila_botones.pack()

        btn_pdf = tk.Button(
            fila_botones,
            text="PDF",
            bg="#2563eb",
            fg="white",
            font=('Arial', 11, 'bold'),
            width=10,
            relief="flat",
            cursor="hand2",
            command=self._exportar_pdf_usuario
        )
        btn_pdf.pack(side="left", padx=(0, 5))

        btn_excel = tk.Button(
            fila_botones,
            text="Excel",
            bg="#059669",
            fg="white",
            font=('Arial', 11, 'bold'),
            width=10,
            relief="flat",
            cursor="hand2",
            command=self._exportar_excel_usuario
        )
        btn_excel.pack(side="left", padx=(5, 0))


        # Línea divisoria debajo del bloque superior
        ttk.Separator(self.frame_reporte, orient='horizontal').pack(fill='x', padx=20, pady=10)

    
    def _mostrar_estadisticas(self, estudiante_id, mes=None, anio=None, fecha_inicio=None, fecha_fin=None):
        """
        Muestra las estadísticas del estudiante
        
        Args:
            estudiante_id: ID del estudiante
            mes: Mes para filtrar (opcional, excluyente con fecha_inicio/fin)
            anio: Año para filtrar (opcional, excluyente con fecha_inicio/fin)
            fecha_inicio: Fecha de inicio para el rango personalizado (formato YYYY-MM-DD)
            fecha_fin: Fecha de fin para el rango personalizado (formato YYYY-MM-DD)
        """
        try:
            # Obtener estadísticas del controlador con los filtros apropiados
            if fecha_inicio and fecha_fin:
                # Validar formato de fechas
                try:
                    datetime.strptime(fecha_inicio, "%Y-%m-%d")
                    datetime.strptime(fecha_fin, "%Y-%m-%d")
                    if fecha_fin < fecha_inicio:
                        messagebox.showerror("Error", "La fecha de fin no puede ser anterior a la fecha de inicio")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
                    return
                    
                estadisticas = self.controlador.obtener_estadisticas_estudiante(
                    estudiante_id=estudiante_id,
                    # fecha_inicio=fecha_inicio,
                    # fecha_fin=fecha_fin
                )
            else:
                # Usar filtro por mes/año
                if not mes or not anio:
                    # Si no hay filtros, usar el mes y año actual
                    mes = mes or datetime.now().month
                    anio = anio or datetime.now().year
                    
                estadisticas = self.controlador.obtener_estadisticas_estudiante(
                    estudiante_id=estudiante_id,
                    mes=mes,
                    anio=anio
                )
            
            if not estadisticas:
                raise Exception("No se pudieron obtener las estadísticas del estudiante")
            
            # Crear frame para las estadísticas
            stats_frame = tk.Frame(self.frame_reporte, bg="#f8f9fa")
            stats_frame.pack(fill="both", expand=True, padx=20, pady=10, ipadx=10, ipady=10)
            
            # Título de estadísticas
            # Configurar la localización en español
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para Linux/Unix
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Para Windows
                except locale.Error:
                    print("No se pudo configurar la localización en español")
                    
            # Obtener nombre del mes
            nombre_mes = datetime.strptime(f"{mes}", "%m").strftime("%B").capitalize() if mes else ""
            titulo = f"Estadísticas de Asistencias - {nombre_mes} {anio}" if mes and anio else "Estadísticas de Asistencias"
            tk.Label(stats_frame, text=titulo, 
                    font=('Arial', 14, 'bold'), bg="#f8f9fa").pack(anchor="w", pady=(0, 10))
            
            # Frame para las tarjetas de estadísticas
            cards_frame = tk.Frame(stats_frame, bg="#f8f9fa")
            cards_frame.pack(fill="x", pady=10)
            
            # Tarjeta 1: Promedio semanal
            self._crear_tarjeta_estadistica(
                cards_frame, 
                "Promedio semanal", 
                f"{estadisticas.get('promedio_semanal', '0')} hrs",
                "#4f46e5"
            )
            
            # Tarjeta 2: Promedio mensual
            self._crear_tarjeta_estadistica(
                cards_frame, 
                "Promedio mensual", 
                f"{estadisticas.get('promedio_mensual', '0')} hrs",
                "#10b981"
            )
            
            # Tarjeta 3: Hora más frecuente de entrada
            self._crear_tarjeta_estadistica(
                cards_frame, 
                "Hora más frecuente de entrada", 
                estadisticas.get('hora_entrada_frecuente', '--:--'),
                "#f59e0b"
            )
            
            # Tarjeta 4: Hora más frecuente de salida
            self._crear_tarjeta_estadistica(
                cards_frame, 
                "Hora más frecuente de salida", 
                estadisticas.get('hora_salida_frecuente', '--:--'),
                "#ef4444"
            )
            
            # Historial de asistencias
            self._mostrar_historial_asistencias(stats_frame, estadisticas.get('historial', []))
            
        except Exception as e:
            print(f"Error al obtener estadísticas: {e}")
            traceback.print_exc()


    
    def _crear_tarjeta_estadistica(self, parent, titulo, valor, color):
        """Crea una tarjeta de estadística"""
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.pack(side="left", fill="both", expand=True, padx=5, pady=5, ipadx=10, ipady=10)
        
        # Título
        tk.Label(card, text=titulo, font=('Arial', 10), 
                fg="#6b7280", bg="white").pack(anchor="w")
        
        # Valor
        tk.Label(card, text=valor, font=('Arial', 18, 'bold'), 
                fg=color, bg="white").pack(anchor="w", pady=(5, 0))
    
    def _mostrar_historial_asistencias(self, parent, historial):
        """Muestra el historial de asistencias en una tabla"""
        # Título de la sección
        tk.Label(parent, text="Historial de Asistencias", 
                font=('Arial', 14, 'bold'), bg="#f8f9fa").pack(anchor="w", pady=(20, 10))
        
        # Crear frame para la tabla
        table_frame = tk.Frame(parent, bg="white", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Crear scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Crear tabla
        columns = ("#1", "#2", "#3", "#4")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                          yscrollcommand=scrollbar.set)
        
        # Configurar columnas
        tree.heading("#1", text="Fecha")
        tree.heading("#2", text="Hora de Entrada")
        tree.heading("#3", text="Hora de Salida")
        tree.heading("#4", text="Horas Presentes")
        
        tree.column("#1", width=150, anchor="center")
        tree.column("#2", width=150, anchor="center")
        tree.column("#3", width=150, anchor="center")
        tree.column("#4", width=150, anchor="center")
        
        # Agregar datos al historial
        for registro in historial:
            tree.insert("", "end", values=(
                registro.get('fecha', '--/--/----'),
                registro.get('hora_entrada', '--:--'),
                registro.get('hora_salida', '--:--'),
                registro.get('horas_presentes', '--:--')
            ))
        
        # Configurar scrollbar
        scrollbar.config(command=tree.yview)
        
        # Empaquetar tabla
        tree.pack(fill="both", expand=True)

    def buscar_estudiante_reportes(self):
        """Maneja el clic en el botón 'Buscar' o la tecla Enter en la pestaña de reportes."""
        try:
            # Cerrar el popup del autocompletado si está visible
            try:
                if hasattr(self, "entry_estudiante") and hasattr(self.entry_estudiante, "close_popup"):
                    self.entry_estudiante.close_popup()
            except Exception:
                pass

            texto = (self.entry_estudiante.get() or "").strip()
            if not texto or texto.lower().startswith("buscar"):
                messagebox.showinfo("Atención", "Escribe el nombre, matrícula o correo del estudiante.")
                return

            # Reusar la lógica del autocompletado (si ya hay selección, la usa; si no, busca por texto)
            self._buscar_estudiante_autocomplete()

        except Exception as e:
            print(f"Error al buscar estudiante: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"No se pudo ejecutar la búsqueda:\n{e}")


    
    def _abrir_reporte_generacion(self):
        try:
            parent = self._get_tk_parent()
            top = tk.Toplevel(parent)
            top.title("Reporte por generación")
            top.configure(bg="white")
            top.geometry("900x540")
            #top.grab_set()

            tk.Label(top, text="Reporte por generación", bg="white",
                    font=('Arial', 16, 'bold')).pack(pady=(12, 6))

            bar = tk.Frame(top, bg="white"); bar.pack(fill="x", padx=14, pady=6)
            tk.Label(bar, text="Generación:", bg="white", font=('Arial', 11)).pack(side="left")

            # === NUEVO: cargar id+nombre y mapa nombre->id ===
            # Espera que el controlador exponga obtener_generaciones() -> [(id, nombre)] o [{'id':..,'nombre':..}, ...]
            generaciones_raw = self.controlador.obtener_generaciones() or []
            # Normaliza a lista de dicts {'id':..., 'nombre':...}
            generaciones = []
            for g in generaciones_raw:
                if isinstance(g, dict):
                    generaciones.append({'id': g.get('id'), 'nombre': g.get('nombre')})
                elif isinstance(g, (list, tuple)) and len(g) >= 2:
                    generaciones.append({'id': g[0], 'nombre': g[1]})
            gen_nombres = [g['nombre'] for g in generaciones]

            self._combo_gen = ttk.Combobox(bar, values=gen_nombres, state="readonly", width=28)
            if gen_nombres:
                self._combo_gen.set(gen_nombres[0])
            self._combo_gen.pack(side="left", padx=(8, 12))

            # Mapa nombre → id para usarlo al cargar la tabla
            self._map_gen_name_to_id = {g['nombre']: g['id'] for g in generaciones}

            tk.Button(bar, text="Mostrar", bg="#2563eb", fg="white", relief="flat",
                    font=('Arial', 11, 'bold'),
                    command=lambda: self._cargar_tabla_generacion(top)).pack(side="left")

            actions = tk.Frame(top, bg="white"); actions.pack(fill="x", padx=14, pady=(6,8))
            tk.Button(actions, text="Exportar", bg="#7c3aed", fg="white", relief="flat",
                    font=('Arial', 11, 'bold'),
                    command=lambda: self._exportar_reporte_generacion(top)).pack(side="left")

            try:
                from config.email import send_mail  # habilita botón si existe
                tk.Button(actions, text="Enviar por correo", bg="#059669", fg="white", relief="flat",
                        font=('Arial', 11, 'bold'),
                        command=lambda: self._enviar_reporte_generacion_por_correo(top)).pack(side="left", padx=(10,0))
            except Exception:
                pass  # sin emailer no mostramos botón

            cols = ("matricula","nombre","generacion","asesor","area","carrera","tot_hrs","prom_sem","prom_mes")
            tv = ttk.Treeview(top, columns=cols, show="headings", height=16)
            self._tv_gen = tv
            for c, w in [("matricula",100),("nombre",220),("generacion",100),("asesor",120),
                        ("area",140),("carrera",140),("tot_hrs",85),("prom_sem",90),("prom_mes",90)]:
                tv.heading(c, text=c.upper()); tv.column(c, width=w, anchor="center")
            tv.pack(fill="both", expand=True, padx=14, pady=(2,12))

            self._label_gen_status = tk.Label(top, text="", bg="white", fg="#6b7280", font=('Arial', 10))
            self._label_gen_status.pack(padx=14, pady=(0,12))

            # Mensaje si no hay generaciones
            if not gen_nombres:
                messagebox.showinfo(
                    "Sin generaciones",
                    "No hay generaciones en el catálogo. Carga generaciones o asigna el campo en los alumnos."
                )
            else:
                self._cargar_tabla_generacion(top)

        except Exception:
            messagebox.showerror("Error", traceback.format_exc())


    def _cargar_tabla_generacion(self, top):
        """Rellena la tabla por generación usando el nombre de la generación y respetando el filtro de mes/año o rango."""
        if not hasattr(self, "_tv_gen"):
            return

        # 1) Obtener el nombre seleccionado
        gen_nombre = (self._combo_gen.get() or "").strip()
        if not gen_nombre:
            messagebox.showwarning("Aviso", "Selecciona una generación válida.")
            return

        # 2) Consultar filas por nombre de generación (el modelo filtra por a.generacion)
        rows = self.controlador.obtener_estudiantes_por_generacion(gen_nombre) or []

        # 3) Limpiar la tabla
        for r in self._tv_gen.get_children():
            self._tv_gen.delete(r)

        # 4) Parámetros de fecha (mismo criterio que usas en el reporte individual/general)
        mes = self.combo_mes.current() + 1 if self.tipo_filtro.get() == "mes" else None
        anio = int(self.combo_anio.get()) if self.tipo_filtro.get() == "mes" else None
        fecha_inicio = self.fecha_inicio.get() if self.tipo_filtro.get() == "rango" else None
        fecha_fin = self.fecha_fin.get() if self.tipo_filtro.get() == "rango" else None

        # 5) Meta por fila
        self._gen_row_meta = {}
        total = 0

        # rows esperado:
        # (id, email, matricula, nombre, ape_p, ape_m, generacion, asesor, area, carrera, asesor_email)
        for est in rows:
            est_id = est[0]
            est_email = (est[1] or "").strip()
            matricula = est[2]
            nombre = f"{est[3]} {est[4] or ''} {est[5] or ''}".strip()
            generacion = est[6] or ""
            asesor = est[7] or ""
            area = est[8] or ""
            carrera = est[9] or ""
            asesor_email = (est[10] or "").strip()

            # Estadísticas con filtros
            estad = self.controlador.obtener_estadisticas_estudiante(
                est_id, mes=mes, anio=anio, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            ) or {}

            tot_hrs = f'{estad.get("total_horas_mes","0.00")}'
            prom_sem = f'{estad.get("promedio_semanal","0.00")}'
            prom_mes = f'{estad.get("promedio_mensual","0.00")}'

            iid = self._tv_gen.insert(
                "", "end",
                values=(matricula, nombre, generacion, asesor, area, carrera, tot_hrs, prom_sem, prom_mes)
            )

            # Guardar meta por fila (para exportar/enviar correo)
            self._gen_row_meta[iid] = {
                "id": est_id,
                "email": est_email,
                "asesor_email": asesor_email,
                "nombre": nombre,
                "matricula": matricula,
                "generacion": generacion,
                "asesor": asesor,
                "area": area,
                "carrera": carrera,
                "estad": estad,
                "filtros": {"mes": mes, "anio": anio, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            }
            total += 1

        # 6) Actualizar pie de ventana con el nombre visible
        self._label_gen_status.config(text=f"Generación: {gen_nombre} — {total} estudiante(s)")


    def _exportar_reporte_generacion(self, top):
        # --- 1) ¿Hay selección? -> exportación individual ---
        seleccion = list(self._tv_gen.selection()) if hasattr(self, "_tv_gen") else []
        if seleccion:
            if not hasattr(self, "_gen_row_meta"):
                messagebox.showerror("Error", "No se encontraron metadatos de filas. Recarga la lista.")
                return

            # a) 1 seleccionado -> Save As (PDF o Excel individual)
            if len(seleccion) == 1:
                iid = seleccion[0]
                meta = self._gen_row_meta.get(iid, {})
                if not meta:
                    messagebox.showerror("Error", "No se encontró la información del alumno seleccionado.")
                    return

                # ------------------ OBTENER MES Y AÑO ------------------
                mes_idx = self.combo_mes.current()
                if mes_idx < 0:
                    messagebox.showwarning("Aviso", "Selecciona un mes válido.")
                    return
                mes = mes_idx + 1

                anio_str = self.combo_anio.get()
                if not anio_str:
                    messagebox.showwarning("Aviso", "Selecciona un año.")
                    return
                try:
                    anio = int(anio_str)
                except ValueError:
                    messagebox.showerror("Error", f"Año inválido: {anio_str!r}")
                    return

                # ------------------ ESTADÍSTICAS E HISTORIAL ------------------
                estudiante_id = meta.get("id")
                if not estudiante_id:
                    messagebox.showerror("Error", "El estudiante no tiene un ID válido.")
                    return

                estadisticas = self.controlador.obtener_estadisticas_estudiante(
                    estudiante_id, mes, anio
                ) or {}
                historial = estadisticas.get("historial", []) or []

                # nombre sugerido base (sin extensión fija)
                nombre_base = f"reporte_{meta.get('matricula','')}_{meta.get('nombre','')}".replace(" ", "_")

                file_path = filedialog.asksaveasfilename(
                    title="Guardar reporte individual...",
                    defaultextension=".pdf",
                    filetypes=[("PDF", "*.pdf"), ("Excel", "*.xlsx")],
                    initialfile=nombre_base
                )
                if not file_path:
                    return

                # ------------------ EXPORTAR SEGÚN EXTENSIÓN ------------------
                try:
                    if file_path.lower().endswith(".pdf"):
                        # PDF individual (meta enriquecido con estadísticas)
                        meta_con_estad = dict(meta)
                        meta_con_estad["estad"] = estadisticas
                        self._generar_pdf_alumno(meta_con_estad, dest_path=file_path)
                        messagebox.showinfo("Exportación individual", f"PDF generado:\n{file_path}")

                    elif file_path.lower().endswith(".xlsx"):
                        # ====== EXPORTAR REPORTE DETALLADO DE ALUMNO A EXCEL ======
                        import openpyxl
                        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
                        from openpyxl.utils import get_column_letter

                        wb = openpyxl.Workbook()
                        ws = wb.active
                        ws.title = "Reporte de Asistencia"

                        # Estilos
                        header_font = Font(bold=True, color="FFFFFF", size=12)
                        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                        subheader_font = Font(bold=True, color="000000", size=11)
                        subheader_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
                        border = Border(
                            left=Side(style="thin"), right=Side(style="thin"),
                            top=Side(style="thin"), bottom=Side(style="thin")
                        )
                        alignment = Alignment(horizontal="left", vertical="center")

                        # 1. Título
                        ws.merge_cells("A1:B1")
                        ws["A1"] = "REPORTE DE ASISTENCIA"
                        ws["A1"].font = Font(bold=True, size=14, color="1F497D")
                        ws["A1"].alignment = Alignment(horizontal="center")

                        # 2. Información del estudiante
                        ws.merge_cells("A2:B2")
                        ws["A2"] = "INFORMACIÓN DEL ESTUDIANTE"
                        ws["A2"].font = header_font
                        ws["A2"].alignment = Alignment(horizontal="center")
                        ws["A2"].fill = header_fill
                        ws["A2"].border = border
                        ws["B2"].border = border

                        datos_estudiante = [
                            ["Nombre:", meta.get("nombre", "N/A")],
                            ["Matrícula:", meta.get("matricula", "N/A")],
                            ["Email:", meta.get("email", "N/A")],
                            ["Generación:", meta.get("generacion", "N/A")],
                            ["Asesor:", meta.get("asesor", "N/A")],
                            ["Área:", meta.get("area_conocimiento", meta.get("area", "N/A"))],
                            ["Carrera:", meta.get("carrera", "N/A")]
                        ]

                        for row in datos_estudiante:
                            ws.append(row)

                        # Formato de info estudiante
                        for row_idx in range(3, 10):
                            ws[f"A{row_idx}"].font = subheader_font
                            ws[f"A{row_idx}"].fill = subheader_fill
                            ws[f"A{row_idx}"].border = border
                            ws[f"B{row_idx}"].border = border
                            ws[f"A{row_idx}"].alignment = alignment
                            ws[f"B{row_idx}"].alignment = alignment

                        # 3. Estadísticas (todas como texto HH:MM:SS)
                        ws.append([])  # espacio
                        stats_title_row = 11
                        ws.merge_cells(f"A{stats_title_row}:B{stats_title_row}")
                        ws[f"A{stats_title_row}"] = "ESTADÍSTICAS DE ASISTENCIA"
                        ws[f"A{stats_title_row}"].font = header_font
                        ws[f"A{stats_title_row}"].alignment = Alignment(horizontal="center")
                        ws[f"A{stats_title_row}"].fill = header_fill
                        ws[f"A{stats_title_row}"].border = border
                        ws[f"B{stats_title_row}"].border = border

                        estadisticas_data = [
                            ["Promedio semanal (hrs):",   estadisticas.get("promedio_semanal", "00:00:00")],
                            ["Promedio mensual (hrs):",   estadisticas.get("promedio_mensual", "00:00:00")],
                            ["Hora más frecuente de entrada:", estadisticas.get("hora_entrada_frecuente", "--:--:--")],
                            ["Hora más frecuente de salida:",  estadisticas.get("hora_salida_frecuente", "--:--:--")],
                        ]

                        start_row = stats_title_row + 1
                        for i, row_data in enumerate(estadisticas_data):
                            row_idx = start_row + i
                            ws.append(row_data)
                            ws[f"A{row_idx}"].font = subheader_font
                            ws[f"A{row_idx}"].fill = subheader_fill
                            ws[f"A{row_idx}"].border = border
                            ws[f"B{row_idx}"].border = border
                            ws[f"A{row_idx}"].alignment = alignment
                            ws[f"B{row_idx}"].alignment = alignment
                            # ya NO aplicamos number_format, vienen como texto HH:MM:SS

                        # 4. Historial detallado (CON INCIDENCIAS)
                        ws.append([])
                        titulo_historial_row = ws.max_row + 1
                        # historial usa 5 columnas (A..E)
                        ws.merge_cells(
                            start_row=titulo_historial_row,
                            start_column=1,
                            end_row=titulo_historial_row,
                            end_column=5
                        )
                        cell_titulo = ws.cell(row=titulo_historial_row, column=1)
                        cell_titulo.value = "HISTORIAL DETALLADO DE ASISTENCIA"
                        cell_titulo.font = header_font
                        cell_titulo.fill = header_fill
                        cell_titulo.alignment = Alignment(horizontal="center")
                        for col in range(1, 6):
                            ws.cell(row=titulo_historial_row, column=col).border = border

                        encabezados = ["Fecha", "Hora de Entrada", "Hora de Salida", "Horas Presentes", "Incidencia"]
                        header_row = ws.max_row + 1
                        ws.append(encabezados)

                        for col, header in enumerate(encabezados, start=1):
                            cell = ws.cell(row=header_row, column=col)
                            cell.font = subheader_font
                            cell.fill = subheader_fill
                            cell.border = border
                            cell.alignment = Alignment(horizontal="center")

                        if historial and isinstance(historial, list) and (
                            len(historial) == 0 or isinstance(historial[0], dict)
                        ):
                            for reg in historial:
                                row = [
                                    reg.get("fecha", "--/--/----"),
                                    reg.get("hora_entrada", "--:--:--"),
                                    reg.get("hora_salida", "--:--:--"),
                                    reg.get("horas_presentes", "00:00:00"),  # ya viene HH:MM:SS
                                    reg.get("motivo_incidencia", ""),        # motivo seleccionado en incidencias
                                ]
                                ws.append(row)
                        else:
                            ws.append(["--/--/----", "--:--:--", "--:--:--", "00:00:00", ""])

                        # Bordes + formato + color en salidas manuales
                        from openpyxl.styles import PatternFill

                        for row_idx in range(header_row + 1, ws.max_row + 1):
                            for col_idx in range(1, 6):
                                cell = ws.cell(row=row_idx, column=col_idx)
                                cell.border = border
                                cell.alignment = alignment

                            # Columna 5 = Incidencia → si tiene texto, pintamos SOLO la celda de Hora de salida (col 3)
                            cell_inc = ws.cell(row=row_idx, column=5)
                            if isinstance(cell_inc.value, str) and cell_inc.value.strip():
                                cell_salida = ws.cell(row=row_idx, column=3)  # Hora de salida
                                cell_salida.fill = PatternFill(
                                    start_color="FFF59D",  # amarillo suave
                                    end_color="FFF59D",
                                    fill_type="solid"
                                )

                        # 5. Leyenda de motivos de incidencias
                        leyenda_row = ws.max_row + 2
                        ws.merge_cells(
                            start_row=leyenda_row,
                            start_column=1,
                            end_row=leyenda_row,
                            end_column=5
                        )
                        cell_leyenda = ws.cell(row=leyenda_row, column=1)
                        cell_leyenda.value = (
                            "Motivo de incidencias (solo cuando aplique): "
                            "Vista de campo (obra), Coordinación cerrada, Clases en línea."
                        )
                        cell_leyenda.font = Font(italic=True, size=10)
                        cell_leyenda.alignment = Alignment(horizontal="left")

                        # Ajustar anchos
                        for col in ws.columns:
                            max_length = 0
                            column = get_column_letter(col[0].column)
                            for cell in col:
                                try:
                                    if cell.value:
                                        max_length = max(max_length, len(str(cell.value)))
                                except (ValueError, TypeError):
                                    pass
                            ws.column_dimensions[column].width = max_length + 2

                        ws.freeze_panes = "A2"

                        wb.save(file_path)
                        messagebox.showinfo("Exportación individual", f"Excel generado:\n{file_path}")

                    else:
                        messagebox.showwarning("Aviso", "Extensión de archivo no soportada.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar el reporte:\n{e}")

                return

            # b) Varios seleccionados -> seleccionar carpeta (un PDF por alumno)
            carpeta = filedialog.askdirectory(title="Selecciona carpeta para guardar los PDF individuales")
            if not carpeta:
                return

            generados = 0
            errores = 0
            for iid in seleccion:
                meta = self._gen_row_meta.get(iid, {})
                if not meta:
                    errores += 1
                    continue
                try:
                    self._generar_pdf_alumno(meta, carpeta_salida=carpeta)
                    generados += 1
                except Exception:
                    errores += 1

            messagebox.showinfo("Exportación individual", f"Se generaron {generados} PDF(s). Errores: {errores}.")
            return  # Importante: no seguir al flujo general

        # --- 2) SIN selección -> exportación GENERAL (tu lógica existente) ---
        gen = self._combo_gen.get().strip()
        if not gen:
            messagebox.showwarning("Aviso", "Selecciona una generación.")
            return

        data = [self._tv_gen.item(i, "values") for i in self._tv_gen.get_children()]
        if not data:
            messagebox.showwarning("Aviso", "No hay datos para exportar.")
            return

        mes_nombre = self.combo_mes.get()
        anio = self.combo_anio.get()

        file_types = [('Excel', '*.xlsx'), ('PDF', '*.pdf')]
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=file_types,
            title="Guardar reporte por generación...",
            initialfile=f"reporte-{gen.lower().replace(' ','_')}-{mes_nombre.lower()}-{anio}"
        )
        if not file_path:
            return

        headers = ["MATRÍCULA","NOMBRE","GENERACIÓN","ASESOR","ÁREA","CARRERA","TOT HRS","PROM SEM","PROM MES"]

        if file_path.endswith(".xlsx"):
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side
            wb = Workbook()
            ws = wb.active
            ws.title = f"Gen {gen}"
            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

            ws.merge_cells('A1:I1')
            ws["A1"] = f"REPORTE DE ASISTENCIAS — Generación {gen} — {mes_nombre} {anio}"
            ws["A1"].font = Font(bold=True, size=14)

            for j, h in enumerate(headers, start=1):
                c = ws.cell(row=2, column=j, value=h)
                c.font = header_font
                c.fill = header_fill
                c.border = border

            r = 3
            for row in data:
                for j, v in enumerate(row, start=1):
                    c = ws.cell(row=r, column=j, value=v)
                    c.border = border
                r += 1

            for col in range(1, 10):
                ws.column_dimensions[chr(64+col)].width = 18

            wb.save(file_path)
            messagebox.showinfo("Éxito", f"Reporte exportado:\n{file_path}")

        elif file_path.endswith(".pdf"):
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"REPORTE — Gen {gen} — {mes_nombre} {anio}", ln=True, align="C")
            pdf.ln(5)
            pdf.set_font("Arial", "B", 10)
            for h in headers:
                pdf.cell(22 if h == "MATRÍCULA" else 40, 8, h, border=1, align="C")
            pdf.ln(8)
            pdf.set_font("Arial", "", 9)
            for row in data:
                widths = [22, 40, 25, 35, 35, 35, 18, 20, 20]
                for val, w in zip(row, widths):
                    pdf.cell(w, 8, str(val), border=1)
                pdf.ln(8)
            pdf.output(file_path)
            messagebox.showinfo("Éxito", f"Reporte exportado:\n{file_path}")

        # Guarda la última ruta (flujo general)
        self._ultimo_reporte_gen_path = file_path
        self._ultimo_reporte_gen_name = gen



    def _generar_pdf_alumno(self, meta: dict, carpeta_salida: str = None, dest_path: str = None) -> str:
        """
        Genera un PDF individual para el alumno usando el diseño de fondo.
        Incluye columna de Incidencias y leyenda de motivos.
        """

        def slugify(s):
            s = "" if s is None else str(s)
            s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
            s = re.sub(r"[^\w\-. ]+", "", s, flags=re.UNICODE)
            return s.strip().replace(" ", "_")

        # construir nombre si no se pasó dest_path
        if dest_path is None:
            if not carpeta_salida:
                raise ValueError("Debe especificarse dest_path o carpeta_salida")
            nombre_archivo = f"reporte_{slugify(meta.get('matricula',''))}_{slugify(meta.get('nombre',''))}.pdf"
            dest_path = os.path.join(carpeta_salida, nombre_archivo)

        # ------- datos de filtros / periodo -------
        filtros = meta.get("filtros", {}) if isinstance(meta, dict) else {}
        mes = filtros.get("mes")
        anio = filtros.get("anio")
        fi = filtros.get("fecha_inicio")
        ff = filtros.get("fecha_fin")

        try:
            mes_nombre = self.combo_mes.get()
        except Exception:
            mes_nombre = str(mes) if mes else ""

        encabezado_rango = ""
        if mes and anio:
            encabezado_rango = f"Mes {mes_nombre} {anio}"
        elif fi and ff:
            encabezado_rango = f"Del {fi} al {ff}"

        # ------- estadísticas -------
        estad = meta.get("estad", {}) or {}
        tot_hrs = str(estad.get("total_horas_mes", estad.get("total_horas_periodo", "0.00")))
        prom_sem = str(estad.get("promedio_semanal", "0.00"))
        prom_mes = str(estad.get("promedio_mensual", "0.00"))
        hora_ent = estad.get("hora_entrada_frecuente", "--:--")
        hora_sal = estad.get("hora_salida_frecuente", "--:--")
        historial = estad.get("historial", []) or []

        # ------- datos del alumno -------
        nombre_alumno = (meta.get("nombre", "") or "").strip()
        matricula = str(meta.get("matricula", "") or "")
        generacion = meta.get("generacion", "") or ""
        asesor = meta.get("asesor", "") or ""
        area = meta.get("area", meta.get("area_conocimiento", "")) or ""
        carrera = meta.get("carrera", "") or ""

        # ------- PDF -------
        pdf = FPDF()
        pdf.add_page()

        # Tamaño de página
        page_w = pdf.w
        page_h = pdf.h

        # Límites dinámicos
        Y_MAX_CONTENIDO = page_h - 40
        Y_MAX_TABLA = page_h - 55

        # Fondo
        posibles_rutas = [
            resource_path(os.path.join("public", "static", "images", "diseno.png")),
            resource_path(os.path.join("public", "static", "images", "diseño.png")),
        ]
        try:
            for ruta_img in posibles_rutas:
                if os.path.exists(ruta_img):
                    pdf.image(ruta_img, x=0, y=0, w=page_w, h=page_h)
                    break
        except Exception as e:
            print(f"Error al cargar membrete PDF: {e}")
            pass

        # Título
        pdf.set_font("Arial", "B", 20)
        pdf.set_xy(0, 40)
        pdf.cell(0, 10, "REPORTE DE ASISTENCIAS", ln=True, align="C")

        # Mes / periodo
        pdf.set_font("Arial", "", 14)
        if encabezado_rango:
            pdf.cell(0, 8, encabezado_rango, ln=True, align="C")
        pdf.ln(10)

        # ============================================================
        #     🟦 DATOS DEL ALUMNO (con MULTI_CELL para Carrera)
        # ============================================================
        pdf.set_font("Arial", "", 12)
        line_h = 7

        left_x = 15
        right_x = 120
        margin_r = 15

        left_w = right_x - left_x - 5
        right_w = page_w - right_x - margin_r

        y = pdf.get_y()

        # 1️⃣ Alumno / Matrícula
        pdf.set_xy(left_x, y)
        pdf.cell(left_w, line_h, f"Estudiante: {nombre_alumno}", ln=0)

        pdf.set_xy(right_x, y)
        pdf.multi_cell(right_w, line_h, f"Matrícula: {matricula}")
        y = max(y + line_h, pdf.get_y())

        # 2️⃣ Generación / Asesor
        pdf.set_xy(left_x, y)
        pdf.cell(left_w, line_h, f"Generación: {generacion}", ln=0)

        pdf.set_xy(right_x, y)
        pdf.multi_cell(right_w, line_h, f"Asesor: {asesor}")
        y = max(y + line_h, pdf.get_y())

        # 3️⃣ Área / Carrera
        pdf.set_xy(left_x, y)
        pdf.cell(left_w, line_h, f"Área: {area}", ln=0)

        pdf.set_xy(right_x, y)
        pdf.multi_cell(right_w, line_h, f"Carrera: {carrera}")
        y = max(y + line_h, pdf.get_y())

        pdf.set_y(y + 5)
        # ============================================================

        # Resumen
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, line_h, "Resumen:", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, line_h, f"Total de horas en el periodo: {tot_hrs}", ln=True)
        pdf.cell(0, line_h, f"Promedio semanal: {prom_sem}", ln=True)
        pdf.cell(0, line_h, f"Promedio mensual: {prom_mes}", ln=True)
        pdf.cell(0, line_h, f"Hora más frecuente de entrada: {hora_ent}", ln=True)
        pdf.cell(0, line_h, f"Hora más frecuente de salida: {hora_sal}", ln=True)

        pdf.ln(10)

        # Historial
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, line_h, "Historial de Asistencias", ln=True)
        pdf.ln(2)

        # ------------------------------------------------------------
        # Tabla con columna extra "Incidencia"
        # ------------------------------------------------------------
        pdf.set_font("Arial", "B", 10)
        col_w = [35, 35, 35, 35, 50]
        headers = ["Fecha", "Hora Entrada", "Hora Salida", "Horas Presentes", "Incidencia"]
        ALTURA_FILA = 7

        for w, h in zip(col_w, headers):
            pdf.cell(w, 8, h, border=1, align="C")
        pdf.ln(8)

        pdf.set_font("Arial", "", 9)
        for reg in historial:
            if pdf.get_y() + ALTURA_FILA > Y_MAX_TABLA:
                pdf.add_page()
                page_w = pdf.w
                page_h = pdf.h
                Y_MAX_CONTENIDO = page_h - 40
                Y_MAX_TABLA = page_h - 55

                try:
                    for ruta_img in posibles_rutas:
                        if os.path.exists(ruta_img):
                            pdf.image(ruta_img, x=0, y=0, w=page_w, h=page_h)
                            break
                except:
                    pass

                pdf.set_y(50)
                pdf.set_font("Arial", "B", 10)
                for w, h in zip(col_w, headers):
                    pdf.cell(w, 8, h, border=1, align="C")
                pdf.ln(8)
                pdf.set_font("Arial", "", 9)

            fecha_txt  = str(reg.get("fecha", ""))
            ent_txt    = str(reg.get("hora_entrada", ""))
            sal_txt    = str(reg.get("hora_salida", ""))
            horas_txt  = str(reg.get("horas_presentes", ""))
            motivo     = str(reg.get("motivo_incidencia", "") or "")
            hay_incid  = bool(motivo)

            # Fecha
            pdf.cell(col_w[0], ALTURA_FILA, fecha_txt, border=1, align="C")
            # Hora entrada
            pdf.cell(col_w[1], ALTURA_FILA, ent_txt, border=1, align="C")

            # 🟡 Hora salida (solo esta celda se pinta cuando fue manual)
            if hay_incid:
                pdf.set_fill_color(255, 230, 153)  # amarillo claro
                pdf.cell(col_w[2], ALTURA_FILA, sal_txt, border=1, align="C", fill=True)
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.cell(col_w[2], ALTURA_FILA, sal_txt, border=1, align="C")

            # Horas presentes
            pdf.cell(col_w[3], ALTURA_FILA, horas_txt, border=1, align="C")
            # Incidencia (solo texto, sin color)
            pdf.cell(col_w[4], ALTURA_FILA, motivo, border=1, align="C")

            pdf.ln(ALTURA_FILA)
        # ------------------------------------------------------------
        # Leyenda de motivos de incidencias
        # ------------------------------------------------------------
        pdf.ln(5)
        pdf.set_font("Arial", "I", 9)
        pdf.multi_cell(
            0,
            5,
            "Motivo de incidencias (solo cuando aplique): "
            "Vista de campo (obra), Coordinación cerrada, Clases en línea."
        )

        # Firma
        FIRMA_ALTURA = 22

        if pdf.get_y() + FIRMA_ALTURA > Y_MAX_CONTENIDO:
            pdf.add_page()
            page_w = pdf.w
            page_h = pdf.h
            Y_MAX_CONTENIDO = page_h - 40
            Y_MAX_TABLA = page_h - 55

            try:
                for ruta_img in posibles_rutas:
                    if os.path.exists(ruta_img):
                        pdf.image(ruta_img, x=0, y=0, w=page_w, h=page_h)
                        break
            except:
                pass

        y_firma = max(pdf.get_y() + 10, Y_MAX_CONTENIDO - FIRMA_ALTURA)
        pdf.set_y(y_firma)

        pdf.set_font("Arial", "", 11)
        pdf.ln(4)
        pdf.cell(0, 6, "______________________________", ln=True, align="C")

        texto_asesor = f"Asesor: {asesor}" if asesor else "Asesor"
        pdf.ln(2)
        pdf.cell(0, 6, texto_asesor, ln=True, align="C")

        # Protección
        if hasattr(pdf, "set_encryption"):
            try:
                pdf.set_encryption(
                    owner_password="12345",
                    user_password=None,
                    permissions=(
                        AccessPermission.PRINT_LOW_RES |
                        AccessPermission.PRINT_HIGH_RES
                    )
                )
            except:
                pass

        pdf.output(dest_path)
        return dest_path

        

    def _enviar_reporte_generacion_por_correo(self, top):
        """
        Genera y envía por correo un PDF individual a cada alumno (seleccionados o todos).
        Se ejecuta en un hilo secundario para no congelar la interfaz.
        """
        #import threading
        #import tempfile, shutil, time
        #from tkinter import messagebox

        # Aviso rápido (no bloqueante) de que empezó el envío
        if hasattr(self, "mostrar_notificacion_rapida"):
            self.mostrar_notificacion_rapida("Enviando reportes por correo...", "#2563eb")

        def worker():
            # Todo el trabajo pesado va aquí, en otro hilo
            try:
                # Mailer
                try:
                    from config.email import send_mail
                except Exception:
                    send_mail = None

                if send_mail is None:
                    # Mostrar error en el hilo principal
                    self.ventana.after(
                        0,
                        lambda: messagebox.showerror(
                            "Correo no disponible",
                            "No se encontró config.emailer.send_mail."
                            "Configura config/.env y config/emailer.py."
                        )
                    )
                    return
                # --------- COMPROBAR CONEXIÓN A INTERNET ---------
                def hay_internet(host="8.8.8.8", port=53, timeout=3):
                    try:
                        socket.setdefaulttimeout(timeout)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((host, port))
                        s.close()
                        return True
                    except OSError:
                        return False

                if not hay_internet():
                    self.ventana.after(
                        0,
                        lambda: messagebox.showerror(
                            "Sin conexión a la red",
                            "No hay conexión a Internet.\n"
                            "Verifica tu red y vuelve a intentar enviar los reportes."
                        )
                    )
                    return
                # Validación de datos cargados
                if not hasattr(self, "_tv_gen") or not hasattr(self, "_gen_row_meta"):
                    self.ventana.after(
                        0,
                        lambda: messagebox.showerror(
                            "Error",
                            "No hay datos cargados. Usa 'Mostrar' antes de enviar."
                        )
                    )
                    return

                # Selección vs todos
                seleccion = list(self._tv_gen.selection())
                if seleccion:
                    metas = [self._gen_row_meta[i] for i in seleccion if i in self._gen_row_meta]
                else:
                    metas = [self._gen_row_meta[i] for i in self._tv_gen.get_children() if i in self._gen_row_meta]

                if not metas:
                    self.ventana.after(
                        0,
                        lambda: messagebox.showinfo("Sin destinatarios", "No hay alumnos para enviar.")
                    )
                    return

                # Helper para el texto del periodo (mes/año o rango)
                def _texto_periodo_local(meta: dict) -> str:
                    f = meta.get("filtros", {}) if isinstance(meta, dict) else {}
                    mes = f.get("mes"); anio = f.get("anio")
                    fi = f.get("fecha_inicio"); ff = f.get("fecha_fin")
                    try:
                        mes_nombre = self.combo_mes.get()
                    except Exception:
                        mes_nombre = str(mes) if mes else ""
                    if mes and anio:
                        return f"{mes_nombre} {anio}"
                    if fi and ff:
                        return f"del {fi} al {ff}"
                    return "del periodo seleccionado"

                tmpdir = tempfile.mkdtemp(prefix="reportes_ind_")
                enviados, sin_correo, errores = 0, 0, 0
                errores_detalle = []

                try:
                    for meta in metas:
                        correo_alumno = (meta.get("email") or "").strip()
                        if not correo_alumno:
                            sin_correo += 1
                            continue

                        try:
                            # Genera PDF individual en carpeta temporal
                            pdf_path = self._generar_pdf_alumno(meta, carpeta_salida=tmpdir)

                            periodo_txt = _texto_periodo_local(meta)
                            alumno_nombre = meta.get("nombre", "")
                            alumno_matricula = str(meta.get("matricula", "") or "")
                            asesor_email = (meta.get("asesor_email") or "").strip()
                            asesor_nombre = (meta.get("asesor") or "").strip()

                            # ----- Correo al ALUMNO -----
                            cuerpo_alumno = (
                                f"Hola {alumno_nombre},\n\n"
                                f"Adjunto encontrarás tu reporte de asistencias {periodo_txt}.\n\n"
                                "Saludos."
                            )
                            send_mail(
                                subject=f"Reporte de asistencias — {alumno_nombre} — {periodo_txt}",
                                body=cuerpo_alumno,
                                to_list=[correo_alumno],
                                attachments=[pdf_path]
                            )
                            enviados += 1

                            # ----- Correo al ASESOR (si hay) -----
                            if asesor_email:
                                saludo = f"Hola {asesor_nombre}," if asesor_nombre else "Hola,"
                                cuerpo_asesor = (
                                    f"{saludo}\n\n"
                                    f"Adjunto el reporte mensual de asistencias del alumno "
                                    f"{alumno_nombre} ({alumno_matricula}) correspondiente a {periodo_txt}.\n\n"
                                    "Quedo atento(a) a cualquier comentario.\n\nSaludos."
                                )
                                send_mail(
                                    subject=f"Reporte del alumno {alumno_nombre} — {periodo_txt}",
                                    body=cuerpo_asesor,
                                    to_list=[asesor_email],
                                    attachments=[pdf_path]
                                )

                            # Pausa corta para evitar throttling del servidor SMTP
                            time.sleep(0.4)

                        except Exception as e:
                            errores += 1
                            errores_detalle.append(f"{correo_alumno}: {e}")

                finally:
                    # Limpieza de temporales
                    try:
                        shutil.rmtree(tmpdir, ignore_errors=True)
                    except Exception:
                        pass

                # Mostrar resumen en el hilo principal
                def mostrar_resumen():
                    msg = f"Enviados: {enviados}\nSin correo: {sin_correo}\nErrores: {errores}"
                    if errores_detalle:
                        msg += "\n\nDetalles de errores:\n" + "\n".join(errores_detalle[:5])
                        if len(errores_detalle) > 5:
                            msg += f"\n(+ {len(errores_detalle) - 5} más...)"
                    messagebox.showinfo("Envío de reportes", msg)

                    # Si quieres cerrar la ventana 'top' al terminar:
                    try:
                        if top is not None and top.winfo_exists():
                            top.destroy()
                    except Exception:
                        pass

                self.ventana.after(0, mostrar_resumen)

            except Exception as e:
                # Cualquier fallo inesperado lo reportamos también en el hilo principal
                def mostrar_error_final():
                    messagebox.showerror("Error", f"Ocurrió un error durante el envío de correos:\n{e}")
                self.ventana.after(0, mostrar_error_final)

        # Lanzar el hilo en segundo plano
        threading.Thread(target=worker, daemon=True).start()

    def _exportar_pdf_usuario(self):
        self.exportar_reporte_usuario(formato="pdf")

    def _exportar_excel_usuario(self):
        self.exportar_reporte_usuario(formato="excel")


    def exportar_reporte_usuario(self, formato=None):
        try:
            print("DEBUG -> Entró en exportar_reporte_usuario")

            # ==========================
            # 1) OBTENER ESTUDIANTE SELECCIONADO
            # ==========================
            estudiante = getattr(self, "_estudiante_sel", None)
            if not estudiante:
                messagebox.showwarning(
                    "Advertencia",
                    "Primero selecciona y genera el reporte de un estudiante (botón Buscar)."
                )
                return

            # Nombre completo
            nombre = estudiante.get('nombre', '')
            apellido_p = estudiante.get('apellido_p', estudiante.get('apellido_paterno', ''))
            apellido_m = estudiante.get('apellido_m', estudiante.get('apellido_materno', ''))
            seleccion = f"{nombre} {apellido_p} {apellido_m}".strip()

            # ==========================
            # 2) OBTENER MES Y AÑO DE LOS COMBOS
            # ==========================
            mes_idx = self.combo_mes.current()
            if mes_idx < 0:
                messagebox.showwarning("Advertencia", "Selecciona un mes válido.")
                return
            mes = mes_idx + 1

            anio_str = self.combo_anio.get()
            if not anio_str:
                messagebox.showwarning("Advertencia", "Selecciona un año.")
                return
            try:
                anio = int(anio_str)
            except ValueError:
                messagebox.showerror("Error", f"Año inválido: {anio_str!r}")
                return

            # ==========================
            # 3) OBTENER ESTADÍSTICAS E HISTORIAL
            # ==========================
            estudiante_id = estudiante.get('id')
            if not estudiante_id:
                messagebox.showerror("Error", "El estudiante no tiene un ID válido.")
                return

            estadisticas = self.controlador.obtener_estadisticas_estudiante(
                estudiante_id, mes, anio
            ) or {}
            historial = estadisticas.get('historial', []) or []

            # ==========================
            # 3.1 Helpers internos: PDF y Excel
            # ==========================
            def _exportar_pdf_core():
                nombre_sugerido = f"reporte_{estudiante.get('matricula','')}_{seleccion}.pdf".replace(" ", "_")
                ruta_pdf = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    title="Guardar como PDF",
                    initialfile=nombre_sugerido
                )
                if not ruta_pdf:
                    return

                meta = {
                    "id": estudiante_id,
                    "email": estudiante.get('email', ''),
                    "matricula": estudiante.get('matricula', ''),
                    "nombre": seleccion,
                    "generacion": estudiante.get('generacion', ''),
                    "asesor": estudiante.get('asesor', ''),
                    "area": estudiante.get('area_conocimiento', ''),
                    "carrera": estudiante.get('carrera', ''),
                    "estad": estadisticas,
                    "filtros": {
                        "mes": mes,
                        "anio": anio,
                        "fecha_inicio": None,
                        "fecha_fin": None
                    }
                }
                if isinstance(meta["estad"], dict) and "historial" not in meta["estad"]:
                    meta["estad"]["historial"] = historial

                try:
                    self._generar_pdf_alumno(meta, dest_path=ruta_pdf)
                    messagebox.showinfo("Exportación completada", "El reporte se exportó correctamente en PDF.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

            def _exportar_excel_core():
                
              

                nombre_sugerido = f"reporte_{estudiante.get('matricula','nombre')}_{seleccion}.xlsx".replace(" ", "_")
                ruta_xls = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    title="Guardar como Excel",
                    initialfile=nombre_sugerido
                )
                if not ruta_xls:
                    return

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Reporte de Asistencia"

                # Estilos
                header_font = Font(bold=True, color="FFFFFF", size=12)
                header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                subheader_font = Font(bold=True, color="000000", size=11)
                subheader_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
                border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                alignment = Alignment(horizontal="left", vertical="center")

                # 1. ENCABEZADO
                ws.merge_cells('A1:B1')
                ws['A1'] = "REPORTE DE ASISTENCIA"
                ws['A1'].font = Font(bold=True, size=14, color="1F497D")
                ws['A1'].alignment = Alignment(horizontal="center")

                # 2. INFORMACIÓN DEL ESTUDIANTE
                ws.merge_cells('A2:B2')
                ws['A2'] = "INFORMACIÓN DEL ESTUDIANTE"
                ws['A2'].font = header_font
                ws['A2'].alignment = Alignment(horizontal="center")
                ws['A2'].fill = header_fill
                ws['A2'].border = border
                ws['B2'].border = border

                datos_estudiante = [
                    ["Nombre:", seleccion],
                    ["Matrícula:", estudiante.get('matricula', 'N/A')],
                    ["Email:", estudiante.get('email', 'N/A')],
                    ["Generación:", estudiante.get('generacion', 'N/A')],
                    ["Asesor:", estudiante.get('asesor', 'N/A')],
                    ["Área:", estudiante.get('area_conocimiento', 'N/A')],
                    ["Carrera:", estudiante.get('carrera', 'N/A')]
                ]

                for row in datos_estudiante:
                    ws.append(row)

                for row in range(3, 10):
                    ws[f'A{row}'].font = subheader_font
                    ws[f'A{row}'].fill = subheader_fill
                    ws[f'A{row}'].border = border
                    ws[f'B{row}'].border = border
                    ws[f'A{row}'].alignment = alignment
                    ws[f'B{row}'].alignment = alignment

                # 3. ESTADÍSTICAS (HH:MM:SS como texto)
                ws.append([])
                ws.merge_cells('A11:B11')
                ws['A11'] = "ESTADÍSTICAS DE ASISTENCIA"
                ws['A11'].font = header_font
                ws['A11'].alignment = Alignment(horizontal="center")
                ws['A11'].fill = header_fill
                ws['A11'].border = border
                ws['B11'].border = border

                estadisticas_data = [
                    ["Promedio semanal (hrs):",   estadisticas.get('promedio_semanal', "00:00:00")],
                    ["Promedio mensual (hrs):",   estadisticas.get('promedio_mensual', "00:00:00")],
                    ["Hora más frecuente de entrada:", estadisticas.get('hora_entrada_frecuente', '--:--:--')],
                    ["Hora más frecuente de salida:",  estadisticas.get('hora_salida_frecuente', '--:--:--')]
                ]

                start_row = ws.max_row + 1
                for i, row_data in enumerate(estadisticas_data):
                    row_idx = start_row + i
                    ws.append(row_data)
                    ws[f'A{row_idx}'].font = subheader_font
                    ws[f'A{row_idx}'].fill = subheader_fill
                    ws[f'A{row_idx}'].border = border
                    ws[f'B{row_idx}'].border = border
                    ws[f'A{row_idx}'].alignment = alignment
                    ws[f'B{row_idx}'].alignment = alignment
                    # ya no se usa number_format, son strings HH:MM:SS

                # 4. HISTORIAL (CON INCIDENCIAS)
                ws.append([])
                titulo_historial_row = ws.max_row + 1
                ws.merge_cells(
                    start_row=titulo_historial_row,
                    start_column=1,
                    end_row=titulo_historial_row,
                    end_column=5
                )
                cell_titulo = ws.cell(row=titulo_historial_row, column=1)
                cell_titulo.value = "HISTORIAL DETALLADO DE ASISTENCIA"
                cell_titulo.font = header_font
                cell_titulo.fill = header_fill
                cell_titulo.alignment = Alignment(horizontal="center")

                for col in range(1, 6):
                    ws.cell(row=titulo_historial_row, column=col).border = border

                encabezados = ["Fecha", "Hora de Entrada", "Hora de Salida", "Horas Presentes", "Incidencia"]
                header_row = ws.max_row + 1
                ws.append(encabezados)
                for col, header in enumerate(encabezados, start=1):
                    cell = ws.cell(row=header_row, column=col)
                    cell.font = subheader_font
                    cell.fill = subheader_fill
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center")

                if historial and isinstance(historial, list) and (
                    len(historial) == 0 or isinstance(historial[0], dict)
                ):
                    for reg in historial:
                        row = [
                            reg.get('fecha', '--/--/----'),
                            reg.get('hora_entrada', '--:--:--'),
                            reg.get('hora_salida', '--:--:--'),
                            reg.get('horas_presentes', '00:00:00'),   # HH:MM:SS
                            reg.get('motivo_incidencia', "")          # motivo de incidencia
                        ]
                        ws.append(row)
                else:
                    ws.append(["--/--/----", "--:--:--", "--:--:--", "00:00:00", ""])

                # Formato filas + resaltar solo la celda de hora de salida cuando hay incidencia
                for row_idx in range(header_row + 1, ws.max_row + 1):
                    for col_idx in range(1, 6):
                        cell = ws.cell(row=row_idx, column=col_idx)
                        cell.border = border
                        cell.alignment = alignment

                    # Columna 5 = Incidencia → si tiene texto, pintamos SOLO la celda de Hora de salida (col 3)
                    cell_inc = ws.cell(row=row_idx, column=5)
                    if isinstance(cell_inc.value, str) and cell_inc.value.strip():
                        cell_salida = ws.cell(row=row_idx, column=3)  # Hora de salida
                        cell_salida.fill = PatternFill(
                            start_color="FFF59D",  # amarillo suave
                            end_color="FFF59D",
                            fill_type="solid"
                        )

                # 5. LEYENDA MOTIVOS
                leyenda_row = ws.max_row + 2
                ws.merge_cells(
                    start_row=leyenda_row,
                    start_column=1,
                    end_row=leyenda_row,
                    end_column=5
                )
                cell_leyenda = ws.cell(row=leyenda_row, column=1)
                cell_leyenda.value = (
                    "Motivo de incidencias (solo cuando aplique): "
                    "Vista de campo (obra), Coordinación cerrada, Clases en línea."
                )
                cell_leyenda.font = Font(italic=True, size=10)
                cell_leyenda.alignment = Alignment(horizontal="left")

                # Ajuste de columnas
                for col in ws.columns:
                    max_length = 0
                    column = get_column_letter(col[0].column)
                    for cell in col:
                        try:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        except (ValueError, TypeError):
                            pass
                    ws.column_dimensions[column].width = max_length + 2

                ws.freeze_panes = 'A2'

                # PROTECCIÓN
                for row in ws.iter_rows():
                    for cell in row:
                        cell.protection = Protection(locked=True)

                ws.protection.sheet = True
                ws.protection.password = "12345"
                ws.protection.enable()

                wb.security = WorkbookProtection(
                    workbookPassword="12345",
                    lockStructure=True
                )

                try:
                    wb.save(ruta_xls)
                    messagebox.showinfo(
                        "Exportación exitosa",
                        f"Reporte generado correctamente:\n{ruta_xls}"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error al guardar",
                        f"No se pudo guardar el archivo:\n{e}"
                    )

            # ==========================
            # 4) SI VIENE FORMATO DESDE BOTÓN FIJO → ejecutar directo
            # ==========================
            if formato == "pdf":
                _exportar_pdf_core()
                return
            if formato == "excel":
                _exportar_excel_core()
                return

            # ==========================
            # 5) SI NO HAY FORMATO → mostrar ventanita como antes
            # ==========================
            formato_win = tk.Toplevel(self.ventana)
            formato_win.title("Exportar reporte")
            formato_win.geometry("300x120")
            formato_win.resizable(False, False)
            formato_win.transient(self.ventana)
            formato_win.grab_set()
            formato_win.focus_set()

            tk.Label(
                formato_win,
                text="¿En qué formato deseas exportar?",
                font=('Arial', 12, 'bold')
            ).pack(pady=10)

            btn_pdf = tk.Button(
                formato_win,
                text="PDF",
                width=12,
                bg="#2563eb",
                fg="white",
                font=('Arial', 11, 'bold'),
                command=lambda: (formato_win.destroy(), _exportar_pdf_core())
            )
            btn_pdf.pack(side=tk.LEFT, padx=20, pady=20)

            btn_xls = tk.Button(
                formato_win,
                text="Excel",
                width=12,
                bg="#059669",
                fg="white",
                font=('Arial', 11, 'bold'),
                command=lambda: (formato_win.destroy(), _exportar_excel_core())
            )
            btn_xls.pack(side=tk.RIGHT, padx=20, pady=20)

        except Exception as e:
            messagebox.showerror("Error inesperado", f"Ocurrió un error al exportar el reporte:\n{e}")



    def abrir_ventana_asistencias_dia(self):
        # Obtener asistencias del día desde el controlador
        asistencias = self.controlador.obtener_asistencias_hoy_completo()

        # Crear ventana nueva
        win = tk.Toplevel(self.ventana)
        win.title("Asistencias del Día")
        win.geometry("900x500")
        win.config(bg="white")

        tk.Label(win, text="Asistencias del Día", font=('Arial', 18, 'bold'), bg="white").pack(pady=10)

        # Frame para la tabla
        frame_tabla = tk.Frame(win, bg="white")
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")

        # Tabla
        columns = ("Nombre", "Fecha", "Hora de Entrada", "Hora de Salida", "Horas Presentes")
        tree = ttk.Treeview(frame_tabla, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200 if col == "Nombre" else 150, anchor="center")
        scrollbar.config(command=tree.yview)
        tree.pack(fill="both", expand=True)

        # Agrupar asistencias por usuario

        usuarios = defaultdict(list)
        for reg in asistencias:
            nombre = reg.get("nombre", "")
            usuarios[nombre].append(reg)

        # Insertar datos en la tabla
        for nombre, registros in usuarios.items():
            for i, reg in enumerate(registros):
                tree.insert("", "end", values=(
                    nombre if i == 0 else "",  # Solo mostrar el nombre en la primera fila de cada usuario
                    reg.get("fecha", "--/--/----"),
                    reg.get("hora_entrada", "--:--"),
                    reg.get("hora_salida", "--:--"),
                    reg.get("horas_presentes", "--:--")
                ))

        # Botones de exportar
        frame_botones = tk.Frame(win, bg="white")
        frame_botones.pack(pady=10)

        def exportar_pdf():
            ruta_pdf = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Guardar como PDF",
                initialfile=f"asistencias-de-hoy"
            )
            if ruta_pdf:
                pdf = FPDF(orientation='L')
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, f"Asistencias de Hoy", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(60, 8, "Nombre", 1)
                pdf.cell(40, 8, "Fecha", 1)
                pdf.cell(40, 8, "Hora Entrada", 1)
                pdf.cell(40, 8, "Hora Salida", 1)
                pdf.cell(40, 8, "Horas Presentes", 1)
                pdf.ln()
                pdf.set_font("Arial", "", 11)
                for nombre, registros in usuarios.items():
                    for i, reg in enumerate(registros):
                        pdf.cell(60, 8, nombre if i == 0 else "", 1)
                        pdf.cell(40, 8, str(reg.get("fecha", "")), 1)
                        pdf.cell(40, 8, str(reg.get("hora_entrada", "")), 1)
                        pdf.cell(40, 8, str(reg.get("hora_salida", "")), 1)
                        pdf.cell(40, 8, str(reg.get("horas_presentes", "")), 1)
                        pdf.ln()
                pdf.output(ruta_pdf)
                messagebox.showinfo("Exportación completada", "El reporte se exportó correctamente en PDF.")

        def exportar_excel():
            ruta_xls = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Guardar como Excel")
            if ruta_xls:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Asistencias del Día"
                # Estilos predefinidos
                header_font = Font(bold=True, color="FFFFFF", size=12)
                header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                subheader_font = Font(bold=True, color="000000", size=11)
                subheader_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
                border = Border(left=Side(style='thin'), 
                            right=Side(style='thin'), 
                            top=Side(style='thin'), 
                            bottom=Side(style='thin'))
                alignment = Alignment(horizontal="left", vertical="center")

                # 1. ENCABEZADO
                # Obtener fecha actual
                hoy = datetime.now()
                # Formatear la fecha en español
                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                nombre_mes = meses[hoy.month - 1]
                
                ws.merge_cells('A1:E1')
                ws['A1'] = f'Asistencia de hoy {hoy.day} de {nombre_mes} de {hoy.year}'
                ws['A1'].font = Font(bold=True, size=16, color="1F497D")
                ws['A1'].alignment = Alignment(horizontal="center")
                ws['A1'].border = border

                # 2. SUBENCABEZADO
                ws['A2'] = "Nombre"
                ws['A2'].font = header_font
                ws['A2'].fill = header_fill
                ws['A2'].border = border
                ws['B2'] = "Fecha"
                ws['B2'].font = header_font
                ws['B2'].fill = header_fill
                ws['B2'].border = border
                ws['C2'] = "Hora de Entrada"
                ws['C2'].font = header_font
                ws['C2'].fill = header_fill
                ws['C2'].border = border
                ws['D2'] = "Hora de Salida"
                ws['D2'].font = header_font
                ws['D2'].fill = header_fill
                ws['D2'].border = border
                ws['E2'] = "Horas Presentes"
                ws['E2'].font = header_font
                ws['E2'].fill = header_fill
                ws['E2'].border = border
                # Agregar datos con formato
                row_num = 3  # Empezamos en la fila 3 (después de los encabezados)
                for nombre, registros in usuarios.items():
                    for i, reg in enumerate(registros):
                        ws.cell(row=row_num, column=1, value=nombre if i == 0 else "")
                        ws.cell(row=row_num, column=2, value=reg.get("fecha", "--/--/----"))
                        ws.cell(row=row_num, column=3, value=reg.get("hora_entrada", "--:--"))
                        ws.cell(row=row_num, column=4, value=reg.get("hora_salida", "--:--"))
                        ws.cell(row=row_num, column=5, value=float(reg.get("horas_presentes", "--:--")))
                        # Aplicar borde a todas las celdas de la fila
                        for col in range(1, 6):
                            cell = ws.cell(row=row_num, column=col)
                            cell.border = border
                            
                        row_num += 1
                # Ajustar ancho de columnas
                for col in ws.columns:
                    max_length = 0
                    column = get_column_letter(col[0].column)
                    for cell in col:
                        try:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        except (ValueError, TypeError) as e:
                            print(f"Error al procesar valor de celda: {e}")
                    ws.column_dimensions[column].width = max_length + 2
                wb.save(ruta_xls)
                messagebox.showinfo("Exportación completada", "El reporte se exportó correctamente en Excel.")

        btn_pdf = tk.Button(frame_botones, text="Exportar PDF", width=15, bg="#2563eb", fg="white", font=('Arial', 11, 'bold'), command=exportar_pdf)
        btn_pdf.pack(side=tk.LEFT, padx=20)
        btn_xls = tk.Button(frame_botones, text="Exportar Excel", width=15, bg="#059669", fg="white", font=('Arial', 11, 'bold'), command=exportar_excel)
        btn_xls.pack(side=tk.LEFT, padx=20)


    def _manejar_exportacion(self):
        """Maneja la acción de exportación según la vista actual"""
        if self.vista_actual == 'estudiante' and hasattr(self, 'exportar_reporte_usuario'):
            self.exportar_reporte_usuario()
        elif self.vista_actual == 'general' and hasattr(self, '_exportar_reporte_general'):
            self._exportar_reporte_general()
    
    def _exportar_reporte_general(self):
        """Exporta el reporte general a Excel o PDF"""
        try:
            # Obtener mes y año seleccionados
            mes_idx = self.combo_mes.current()
            mes_nombre = self.combo_mes.get()
            anio = self.combo_anio.get()
            
            # Obtener los datos del TreeView
            tree = self.tree_reporte_general
            
            # Obtener los encabezados
            headers = [tree.heading(col)['text'] for col in tree['columns']]
            
            # Obtener los datos
            data = []
            for item in tree.get_children():
                values = tree.item(item, 'values')
                data.append(values)
            
            if not data:
                messagebox.showwarning("Advertencia", "No hay datos para exportar.")
                return
                
            # Crear DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # Mostrar diálogo para elegir formato
            file_types = [('Excel', '*.xlsx'), ('PDF', '*.pdf')]
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=file_types,
                title="Guardar reporte como...",
                initialfile=f"reporte-general-{mes_nombre.lower()}-{anio}"
            )
            
            if not file_path:  # Usuario canceló
                return
                
            if file_path.endswith('.xlsx'):
                # Crear un libro de trabajo de Excel
                wb = Workbook()
                ws = wb.active
                ws.title = "Reporte de Asistencias"
                
                # Definir estilos
                header_font = Font(bold=True, color="FFFFFF", size=12)
                header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                border = Border(left=Side(style='thin'), 
                             right=Side(style='thin'), 
                             top=Side(style='thin'), 
                             bottom=Side(style='thin'))
                
                #1. ENCABEZADO
                ws.merge_cells('A1:E1')
                if self.tipo_filtro.get() == 'rango':
                    ws['A1'] = f'Reporte General de Asistencias del {self.fecha_inicio.get()} al {self.fecha_fin.get()}'
                else:
                    ws['A1'] = f'Reporte General de Asistencias - {mes_nombre} {anio}'
                ws['A1'].font = Font(bold=True, size=16, color="1F497D")
                ws['A1'].alignment = Alignment(horizontal="center")
                ws['A1'].border = border

                # Escribir encabezados
                for col_num, column in enumerate(df.columns, 1):
                    cell = ws.cell(row=2, column=col_num, value=column)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Escribir datos
                for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 3):
                    for c_idx, value in enumerate(row, 1):
                        # Obtener el nombre de la columna actual
                        col_name = df.columns[c_idx-1] if c_idx <= len(df.columns) else ""
                        
                        # Convertir el valor según la columna
                        if col_name == "Matrícula" and value is not None and str(value).strip():
                            try:
                                value = int(float(str(value).strip()))
                            except (ValueError, TypeError):
                                pass
                        elif col_name == "Promedio Mensual (hrs)" and value is not None and str(value).strip():
                            try:
                                value = float(str(value).strip())
                            except (ValueError, TypeError):
                                pass
                        
                        cell = ws.cell(row=r_idx, column=c_idx, value=value)
                        cell.border = border
                        cell.alignment = Alignment(vertical="center")
                
                # Ajustar ancho de columnas
                # Primero, desagrupar celdas combinadas temporalmente
                merged_cells = list(ws.merged_cells.ranges)
                for merged_range in merged_cells:
                    ws.unmerge_cells(str(merged_range))
                
                # Ajustar ancho de cada columna
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    # Obtener el ancho máximo del contenido de la columna
                    for cell in column:
                        try:
                            if cell.value:
                                cell_value = str(cell.value)
                                # Considerar el ancho del texto en la celda y el ancho del encabezado
                                max_length = max(max_length, len(cell_value))
                        except (AttributeError, ValueError, TypeError) as e:
                            print(f"Error al procesar valor de celda: {e}")
                    
                    # Ajustar el ancho de la columna con un margen
                    if max_length > 0:
                        # Ajuste para el ancho de fuente y márgenes
                        adjusted_width = (max_length + 2) * 1.1
                        # Establecer límites mínimos y máximos para el ancho
                        adjusted_width = max(adjusted_width, 10)  # Ancho mínimo
                        adjusted_width = min(adjusted_width, 50)   # Ancho máximo
                        ws.column_dimensions[column_letter].width = adjusted_width
                
                # Volver a agrupar las celdas combinadas
                for merged_range in merged_cells:
                    ws.merge_cells(str(merged_range))
                
                # Guardar el archivo
                wb.save(file_path)
                messagebox.showinfo("Éxito", f"Reporte exportado exitosamente a:\n{file_path}")
                
            elif file_path.endswith('.pdf'):
                # Exportar a PDF
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                elements = []
                
                # Estilos
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'Title',
                    parent=styles['Heading1'],
                    fontSize=14,
                    spaceAfter=20,
                    alignment=1  # Centrado
                )
                
                # Título
                if self.tipo_filtro.get() == 'rango':
                    title = f"Reporte General de Asistencias del {self.fecha_inicio.get()} al {self.fecha_fin.get()}"
                else:
                    title = f"Reporte General de Asistencias - {mes_nombre} {anio}"
                elements.append(Paragraph(title, title_style))
                
                # Crear tabla con los datos
                table_data = [headers] + data
                table = Table(table_data)
                
                # Estilo de la tabla
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), '#2563eb'),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                table.setStyle(style)
                elements.append(table)
                
                # Generar el PDF
                doc.build(elements)
                messagebox.showinfo("Éxito", f"Reporte exportado exitosamente a:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar el reporte: {str(e)}")
            print(f"Error en _exportar_reporte_general: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def mostrar_reporte_general(self):
        """Muestra un reporte general con estadísticas de todos los estudiantes."""
        try:
            # 0) Validación de rango si aplica
            usar_rango = (hasattr(self, 'tipo_filtro') and self.tipo_filtro.get() == 'rango')
            fi = ff = None
            if usar_rango:
                try:
                    fi = self.fecha_inicio.get().strip()
                    ff = self.fecha_fin.get().strip()
                    datetime.strptime(fi, "%Y-%m-%d")
                    datetime.strptime(ff, "%Y-%m-%d")
                    if ff < fi:
                        messagebox.showerror("Error", "La fecha de fin no puede ser anterior a la fecha de inicio")
                        return
                except ValueError as ve:
                    messagebox.showerror("Error", f"Formato de fecha inválido. Use YYYY-MM-DD: {ve}")
                    return
                except Exception as e:
                    messagebox.showerror("Error", f"Error al validar fechas: {e}")
                    return

            # 1) Estado de vista
            self.vista_actual = 'general'
            #self.btn_exportar.config(state=tk.NORMAL, text="Exportar Reporte")

            # 2) Preparar contenedor visual
            if hasattr(self, 'frame_mensaje_central') and self.frame_mensaje_central.winfo_ismapped():
                self.frame_mensaje_central.place_forget()

            if hasattr(self, 'frame_reporte'):
                for w in self.frame_reporte.winfo_children():
                    w.destroy()
            else:
                self.frame_reporte = tk.Frame(self.ventana, bg="white")

            self.frame_reporte.pack(fill="both", expand=True, padx=30, pady=(170, 30), anchor="nw")

            # 3) Título
            titulo = "Reporte General de Asistencias"
            if usar_rango:
                titulo += f"\nDel {fi} al {ff}"
            else:
                mes_nombre = self.meses[self.combo_mes.current()] if hasattr(self, 'combo_mes') else ""
                anio = self.combo_anio.get() if hasattr(self, 'combo_anio') else ""
                titulo += f"\n{mes_nombre} {anio}"

            tk.Label(self.frame_reporte, text=titulo, font=('Arial', 16, 'bold'), bg="white").pack(pady=(10, 20))

            # 4) Treeview
            if usar_rango:
                columns = ("Nombre", "Matrícula", "Promedio (hrs)", "Hora Frec. Entrada", "Hora Frec. Salida")
            else:
                columns = ("Nombre", "Matrícula", "Promedio Mensual (hrs)", "Hora Frec. Entrada", "Hora Frec. Salida")

            self.tree_reporte_general = ttk.Treeview(
                self.frame_reporte, columns=columns, show="headings", selectmode="browse"
            )
            for col in columns:
                self.tree_reporte_general.heading(col, text=col, anchor=tk.W)
                self.tree_reporte_general.column(col, width=150, minwidth=100, stretch=tk.YES)
            self.tree_reporte_general.column("Nombre", width=250)

            vsb = ttk.Scrollbar(self.frame_reporte, orient="vertical", command=self.tree_reporte_general.yview)
            hsb = ttk.Scrollbar(self.frame_reporte, orient="horizontal", command=self.tree_reporte_general.xview)
            self.tree_reporte_general.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            self.tree_reporte_general.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)

            # 5) Mensaje de carga
            loading_label = tk.Label(self.frame_reporte, text="Cargando datos...", font=('Arial', 12), bg="white")
            loading_label.pack(pady=20)
            self.ventana.update()

            # 6) Helper: obtener todos los estudiantes (sin combobox viejo)
            def _fetch_alumnos():
                try:
                    alumnos = self.controlador.obtener_estudiantes_reportes() or []
                except Exception as e:
                    print("Error al obtener estudiantes:", e)
                    alumnos = []

                norm = []
                for est in alumnos:
                    if isinstance(est, dict):
                        nombre = est.get('nombre', '')
                        ap = est.get('apellido_p', est.get('apellido_paterno', '')) or ''
                        am = est.get('apellido_m', est.get('apellido_materno', '')) or ''
                        norm.append({
                            'id': est.get('id'),
                            'nombre': nombre,
                            'apellido_p': ap,
                            'apellido_m': am,
                            'matricula': est.get('matricula', 'N/A'),
                        })
                    elif isinstance(est, (list, tuple)) and len(est) >= 6:
                        # (id, email, matricula, nombre, ape_p, ape_m, ...)
                        norm.append({
                            'id': est[0],
                            'nombre': est[3] or '',
                            'apellido_p': est[4] or '',
                            'apellido_m': est[5] or '',
                            'matricula': est[2] or 'N/A',
                        })
                return norm

            # 7) Render final
            def actualizar_interfaz(filas):
                # limpia
                for item in self.tree_reporte_general.get_children():
                    self.tree_reporte_general.delete(item)
                loading_label.pack_forget()

                for fila in filas:
                    self.tree_reporte_general.insert("", "end", values=fila)

            # 8) Carga en hilo
            import threading

            def cargar_datos():
                try:
                    alumnos = _fetch_alumnos()
                    filas = []

                    if not alumnos:
                        self.ventana.after(0, lambda: actualizar_interfaz([]))
                        return

                    # Filtros actuales
                    if usar_rango:
                        params_common = {'fecha_inicio': fi, 'fecha_fin': ff}
                    else:
                        mes = self.combo_mes.current() + 1
                        anio = int(self.combo_anio.get())
                        params_common = {'mes': mes, 'anio': anio}

                    total = len(alumnos)
                    for i, est in enumerate(alumnos, 1):
                        est_id = est['id']
                        nombre_visible = f"{est['nombre']} {est['apellido_p']} {est['apellido_m']}".strip()
                        matricula = est['matricula']

                        stats = {}
                        try:
                            stats = self.controlador.obtener_estadisticas_estudiante(est_id, **params_common) or {}
                        except Exception as e:
                            print(f"Error stats alumno {est_id}: {e}")

                        # Conversión segura del promedio
                        prom = stats.get('promedio_mensual', 0 if not usar_rango else stats.get('promedio_mensual', 0))
                        try:
                            prom = float(prom)
                            prom_str = f"{prom:.2f}"
                        except (TypeError, ValueError):
                            prom_str = str(prom) if prom is not None else "0.00"

                        fila = (
                            nombre_visible,
                            matricula,
                            prom_str,
                            stats.get('hora_entrada_frecuente', 'N/A'),
                            stats.get('hora_salida_frecuente', 'N/A')
                        )
                        filas.append(fila)

                        if i % 5 == 0 or i == total:
                            self.ventana.after(0, lambda i=i, total=total:
                                            loading_label.config(text=f"Cargando... {i}/{total} estudiantes"))

                    self.ventana.after(0, lambda: actualizar_interfaz(filas))

                except Exception as e:
                    traceback.print_exc()
                    self.ventana.after(0, lambda: messagebox.showerror("Error", f"Error al cargar los datos: {e}"))

            threading.Thread(target=cargar_datos, daemon=True).start()

        except Exception as e:
            print(f"Error al mostrar reporte general: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", "Ocurrió un error al generar el reporte general.")

# --------------------------------------------- Contenido catálogo ---------------------------------------------

    def _contenido_catalogo(self, parent):
        # --- CONTENEDOR SCROLLABLE ---
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        # Canvas con scrollbar
        canvas2 = tk.Canvas(container, bg="lightblue")
        canvas2.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas2.yview)
        scrollbar.pack(side="right", fill="y")

        canvas2.configure(yscrollcommand=scrollbar.set)

        # Frame interno
        scrollable_frame = tk.Frame(canvas2, bg="lightblue")

        # Vincular tamaño del contenido al scroll
        def resize_scroll_region(event):
            canvas2.configure(scrollregion=canvas2.bbox("all"))
            # Hacer que el frame ocupe el ancho del canvas
            canvas2.itemconfig(window, width=canvas2.winfo_width())


        # Crear ventana en canvas
        window = canvas2.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Configurar el scroll con la rueda del mouse
        # def _on_mousewheel(event):
        #     canvas2.yview_scroll(int(-1*(event.delta/120)), "units")

        # canvas2.bind("<MouseWheel>", _on_mousewheel)
        # scrollable_frame.bind("<Configure>", _on_mousewheel)

        # # Función recursiva para bindear mousewheel a todos los hijos
        # def _bind_mousewheel_to_children(widget):
        #     widget.bind("<MouseWheel>", _on_mousewheel)
        #     for child in widget.winfo_children():
        #         _bind_mousewheel_to_children(child)

        # # Aplicar a todos los widgets del frame scrollable
        # _bind_mousewheel_to_children(scrollable_frame)
        # Pestaña 4: 
        _on_mousewheel_catalogo = self._configurar_scroll_con_rueda(canvas2, scrollable_frame)

        # Asegurar que el canvas reciba foco cuando el mouse entra
        # canvas2.bind("<Enter>", lambda e: canvas2.focus_set())

        scrollable_frame.bind("<Configure>", resize_scroll_region)

        # Título
        titulo = tk.Label(scrollable_frame, text="Catálogo", bg="lightblue", fg="#1a253c",
                        font=('Arial', 24, 'bold'))
        titulo.pack(pady=(30, 0), anchor='w', padx=30)
        
        # Verificar si el controlador está disponible
        if not hasattr(self, 'controlador') or self.controlador is None:
            error_label = tk.Label(scrollable_frame, text="Error: El controlador no está disponible. Por favor reinicie la aplicación.", 
                                 fg="red", bg="lightblue", font=('Arial', 12))
            error_label.pack(pady=20)
            return

        # style.configure("Blue.TFrame", background="lightblue")

        # Frame para centrar todo lo demás
        content_frame = tk.Frame(scrollable_frame, bg="lightblue")
        content_frame.pack(expand=True, fill='both', padx=100, pady=20)  # ocupa todo el ancho

        # Crear un notebook para las pestañas
        notebook = ttk.Notebook(content_frame, style='TNotebook')
        notebook.pack(padx=20, pady=10)
        
        # Pestaña de Generaciones
        tab_generaciones = ttk.Frame(notebook)
        notebook.add(tab_generaciones, text='Generaciones')
        
        # Pestaña de Áreas
        tab_areas = ttk.Frame(notebook)
        notebook.add(tab_areas, text='Áreas de Conocimiento')
        
        # Estilo para los botones
        style = ttk.Style()
        style.configure('TButton', padding=5)
        
        # # Obtener generaciones y áreas de conocimiento desde la base de datos
        # try:
        #     # Obtener generaciones como lista de diccionarios
        #     self.generaciones_data = {g['id']: g['nombre'] for g in self.controlador.obtener_generaciones()}
        #     generaciones = self.controlador.obtener_generaciones()
        #     # Obtener áreas de conocimiento
        #     areas = self.controlador.obtener_areas_conocimiento()
        #     print(generaciones)
        #     print(areas)
        # except Exception as e:
        #     messagebox.showerror("Error", f"Error al cargar los datos: {str(e)}")
        #     self.generaciones_data = {}
        #     generaciones = []
        #     areas = []
        
        # Configurar la pestaña de Generaciones
        self._configurar_tab_catalogo(
            tab_generaciones, 
            'Generación', 
            self.controlador.obtener_generaciones(),
            'generaciones',
            self._guardar_generacion,
            self._eliminar_generacion
        )
        
        # Configurar la pestaña de Áreas
        self._configurar_tab_catalogo(
            tab_areas,
            'Área de Conocimiento',
            self.controlador.obtener_areas_conocimiento(),
            'areas',
            self._guardar_area,
            self._eliminar_area
        )

        titulo2 = tk.Label(content_frame, text="Gestión de Asesores", bg="lightblue", fg="#1a253c",
                        font=('Arial', 24, 'bold'), anchor='w')
        titulo2.pack(fill='x', pady=30, padx=30)

        # Verificar si el controlador está disponible
        if not hasattr(self, 'controlador') or self.controlador is None:
            error_label = tk.Label(content_frame, text="Error: El controlador no está disponible. Por favor reinicie la aplicación.", 
                                 fg="red", bg="lightblue", font=('Arial', 12))
            error_label.pack(pady=20)
            return

        # Frame principal
        asesores_frame = ttk.Frame(content_frame, width=800)  # Ancho específico
        asesores_frame.pack(fill='x')
        asesores_frame.pack_propagate(True)  # Evita que se redimensione automáticamente
        
        # Frame para el formulario
        form_frame = ttk.LabelFrame(asesores_frame, padding=15, width=700)
        form_frame.pack(fill='x', pady=(0, 20))
        form_frame.pack_propagate(True)
        
        # Variables del formulario
        self.asesor_vars = {
            'employee_number': tk.StringVar(),
            'name': tk.StringVar(),
            'phone': tk.StringVar(),
            'email': tk.StringVar()
        }
        self.edit_asesor_id = None
        
        # Grid para los campos del formulario
        row = 0
        
        # Número de empleado
        ttk.Label(form_frame, text="Número de Empleado:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        entry_employee = ttk.Entry(form_frame, textvariable=self.asesor_vars['employee_number'], width=30)
        entry_employee.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        row += 1
        
        # Nombre
        ttk.Label(form_frame, text="Nombre Completo:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        entry_name = ttk.Entry(form_frame, textvariable=self.asesor_vars['name'], width=30)
        entry_name.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        row += 1
        
        # Teléfono
        ttk.Label(form_frame, text="Teléfono:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        entry_phone = ttk.Entry(form_frame, textvariable=self.asesor_vars['phone'], width=30)
        entry_phone.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        row += 1
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        entry_email = ttk.Entry(form_frame, textvariable=self.asesor_vars['email'], width=30)
        entry_email.grid(row=row, column=1, padx=5, pady=5, sticky='ew')
        row += 1
        
        # Configurar peso de columnas para que se expandan
        form_frame.columnconfigure(1, weight=1)
        
        # Botones del formulario
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        
        btn_guardar = ttk.Button(btn_frame, text="Guardar", 
                            command=self._guardar_asesor)
        btn_guardar.pack(side='left', padx=5)
        
        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", 
                                command=self._limpiar_formulario_asesor)
        btn_cancelar.pack(side='left', padx=5)
        
        # Frame para la lista de asesores
        list_frame = ttk.LabelFrame(asesores_frame, text="Asesores Existentes", padding=10)
        list_frame.pack(fill='both', expand=True)
        
        # Crear Treeview para asesores
        columns = ('id', 'employee_number', 'name', 'phone', 'email')
        self.tree_asesores = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        column_config = {
            'id': {'text': 'ID', 'width': 50, 'anchor': 'center'},
            'employee_number': {'text': 'N° Empleado', 'width': 100, 'anchor': 'center'},
            'name': {'text': 'Nombre', 'width': 200, 'anchor': 'w'},
            'phone': {'text': 'Teléfono', 'width': 100, 'anchor': 'center'},
            'email': {'text': 'Email', 'width': 170, 'anchor': 'w'}
        }
        
        for col, config in column_config.items():
            self.tree_asesores.heading(col, text=config['text'])
            self.tree_asesores.column(col, width=config['width'], anchor=config['anchor'])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree_asesores.yview)
        self.tree_asesores.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        self.tree_asesores.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones de acción
        btn_frame_actions = ttk.Frame(list_frame)
        btn_frame_actions.pack(fill='x', pady=5)
        
        btn_editar = ttk.Button(btn_frame_actions, text="Editar", 
                            command=self._editar_asesor)
        btn_editar.pack(side='left', padx=5)
        
        btn_eliminar = ttk.Button(btn_frame_actions, text="Eliminar", 
                                command=self._eliminar_asesor)
        btn_eliminar.pack(side='left', padx=5)
        
        # Cargar datos iniciales
        self._cargar_asesores()

        
    def _configurar_tab_catalogo(self, parent, label_text, datos_completos, tipo, guardar_callback, eliminar_callback):
        # Frame para el formulario
        form_frame = ttk.LabelFrame(parent, text=f"Agregar {label_text}", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Variables específicas por tipo
        if not hasattr(self, 'entry_vars'):
            self.entry_vars = {}
            self.edit_ids = {}
            self.trees = {}

        self.entry_vars[tipo] = tk.StringVar()
        self.edit_ids[tipo] = None
        
        # Entrada
        entry_frame = ttk.Frame(form_frame)
        entry_frame.pack(fill='x', pady=5)
        
        ttk.Label(entry_frame, text=f"{label_text}:").pack(side='left', padx=5)
        entry = ttk.Entry(entry_frame, textvariable=self.entry_vars[tipo], width=40)
        entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Botones del formulario
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill='x', pady=5)
        
        btn_guardar = ttk.Button(btn_frame, text="Guardar", 
                               command=lambda: guardar_callback(tipo))
        btn_guardar.pack(side='left', padx=5)
        
        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", 
                                 command=lambda: self._limpiar_formulario())
        btn_cancelar.pack(side='left', padx=5)
        
        # Lista de elementos
        list_frame = ttk.LabelFrame(parent, text=f"{label_text}s Existentes", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Crear Treeview
        columns = ('id', 'nombre')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configurar columnas
        tree.heading('id', text='ID')
        tree.heading('nombre', text=label_text)
        
        tree.column('id', width=50, anchor='center')
        tree.column('nombre', width=300, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Botones de acción
        btn_frame_actions = ttk.Frame(list_frame)
        btn_frame_actions.pack(fill='x', pady=5)
        
        btn_editar = ttk.Button(btn_frame_actions, text="Editar", 
                              command=lambda: self._editar_item(tree, entry, tipo))
        btn_editar.pack(side='left', padx=5)
        
        btn_eliminar = ttk.Button(btn_frame_actions, text="Eliminar", 
                                command=lambda: eliminar_callback(tree, tipo))
        btn_eliminar.pack(side='left', padx=5)
        
        # Guardar referencias
        self.trees[tipo] = tree
        self.entry = entry
        
        # Cargar datos iniciales
        self._cargar_datos_catalogo(tipo, datos_completos)
    
    def _cargar_datos_catalogo(self, tipo, datos_completos):
        # Limpiar treeview
        for item in self.trees[tipo].get_children():
            self.trees[tipo].delete(item)
        
        # Agregar datos iniciales
        for valor in datos_completos:
            self.trees[tipo].insert('', 'end', values=(int(valor['id']), valor['nombre']))
    
    def _limpiar_formulario(self, tipo):
        self.entry_vars[tipo].set('')
        self.edit_ids[tipo] = None
    
    def _editar_item(self, tree, entry, tipo):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un elemento para editar")
            return
            
        item = tree.item(selected[0])
        values = item['values']
        
        self.edit_ids[tipo] = values[0]
        self.entry_vars[tipo].set(values[1])
        entry.focus()
    
    def _guardar_generacion(self, tipo):
        nombre = self.entry_vars[tipo].get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "El nombre de la generación no puede estar vacío")
            return
            
        try:
            if self.edit_ids[tipo]:
                # Actualizar generación existente
                if self.controlador.actualizar_generacion(self.edit_ids[tipo], nombre):
                    # Actualizar en el treeview
                    for item in self.trees[tipo].get_children():
                        if self.trees[tipo].item(item)['values'][0] == self.edit_ids[tipo]:
                            self.trees[tipo].item(item, values=(self.edit_ids[tipo], nombre))
                            break
                    messagebox.showinfo("Éxito", "Generación actualizada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo actualizar la generación")
            else:
                # Crear nueva generación
                nuevo_id = self.controlador.crear_generacion(nombre)
                if nuevo_id:
                    self.trees[tipo].insert('', 0, values=(nuevo_id, nombre))
                    messagebox.showinfo("Éxito", "Generación creada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo crear la generación")
            
            self._limpiar_formulario(tipo)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la generación: {str(e)}")
    
    def _eliminar_generacion(self, tree, tipo):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione una generación para eliminar")
            return
            
        item = tree.item(selected[0])
        generacion_id = item['values'][0]
        generacion_nombre = item['values'][1]
        
        if messagebox.askyesno("Confirmar", 
                             f"¿Está seguro de eliminar la generación '{generacion_nombre}'?"):
            try:
                if self.controlador.eliminar_generacion(generacion_id):
                    tree.delete(selected[0])
                    messagebox.showinfo("Éxito", "Generación eliminada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar la generación")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar la generación: {str(e)}")
    
    def _guardar_area(self, tipo):
        nombre = self.entry_vars[tipo].get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "El nombre del área no puede estar vacío")
            return
            
        try:
            if self.edit_ids[tipo]:
                # Actualizar área existente
                if self.controlador.actualizar_area_conocimiento(self.edit_ids[tipo], nombre):
                    # Actualizar en el treeview
                    for item in self.trees[tipo].get_children():
                        if self.trees[tipo].item(item)['values'][0] == self.edit_ids[tipo]:
                            self.trees[tipo].item(item, values=(self.edit_ids[tipo], nombre))
                            break
                    messagebox.showinfo("Éxito", "Área actualizada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el área")
            else:
                # Crear nueva área
                nuevo_id = self.controlador.crear_area_conocimiento(nombre)
                if nuevo_id:
                    self.trees[tipo].insert('', 0, values=(nuevo_id, nombre))
                    messagebox.showinfo("Éxito", "Área creada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo crear el área")
            
            self._limpiar_formulario(tipo)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el área: {str(e)}")
    
    def _eliminar_area(self, tree, tipo):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un área para eliminar")
            return
            
        item = tree.item(selected[0])
        area_id = item['values'][0]
        area_nombre = item['values'][1]
        
        if messagebox.askyesno("Confirmar", 
                             f"¿Está seguro de eliminar el área '{area_nombre}'?"):
            try:
                if self.controlador.eliminar_area_conocimiento(area_id):
                    self.trees[tipo].delete(selected[0])
                    messagebox.showinfo("Éxito", "Área eliminada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el área")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar el área: {str(e)}")
    
    def _cargar_asesores(self):
        # Limpiar treeview
        for item in self.tree_asesores.get_children():
            self.tree_asesores.delete(item)
        
        try:
            # Obtener asesores desde la base de datos
            asesores = self.controlador.obtener_informacion_asesores()
            # Agregar datos al treeview
            for asesor in asesores:
                self.tree_asesores.insert('', 'end', values=(
                    asesor['id'],
                    asesor['employee_number'],
                    asesor['name'],
                    asesor['phone'],
                    asesor['email']
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar asesores: {str(e)}")

    def _limpiar_formulario_asesor(self):
        for var in self.asesor_vars.values():
            var.set('')
        self.edit_asesor_id = None

    def _editar_asesor(self):
        selected = self.tree_asesores.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un asesor para editar")
            return
            
        item = self.tree_asesores.item(selected[0])
        values = item['values']
        
        # Llenar el formulario con los datos del asesor seleccionado
        self.edit_asesor_id = values[0]  # ID
        self.asesor_vars['employee_number'].set(values[1])  # Número de empleado
        self.asesor_vars['name'].set(values[2])  # Nombre
        self.asesor_vars['phone'].set(values[3])  # Teléfono
        self.asesor_vars['email'].set(values[4])  # Email

    def _guardar_asesor(self):
        # Validar campos obligatorios
        if not all([self.asesor_vars['employee_number'].get().strip(),
                    self.asesor_vars['name'].get().strip(),
                    self.asesor_vars['email'].get().strip()]):
            messagebox.showwarning("Advertencia", "Por favor complete todos los campos obligatorios")
            return
        
        datos_asesor = {
            'employee_number': self.asesor_vars['employee_number'].get().strip(),
            'name': self.asesor_vars['name'].get().strip(),
            'phone': self.asesor_vars['phone'].get().strip(),
            'email': self.asesor_vars['email'].get().strip()
        }
        
        try:
            if self.edit_asesor_id:
                # Actualizar asesor existente
                if self.controlador.actualizar_asesor(self.edit_asesor_id, datos_asesor):
                    messagebox.showinfo("Éxito", "Asesor actualizado correctamente")
                    self._cargar_asesores()  # Recargar datos
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el asesor")
            else:
                # Crear nuevo asesor
                nuevo_id = self.controlador.crear_asesor(datos_asesor)
                if nuevo_id:
                    messagebox.showinfo("Éxito", "Asesor creado correctamente")
                    self._cargar_asesores()  # Recargar datos
                else:
                    messagebox.showerror("Error", "No se pudo crear el asesor")
            
            self._limpiar_formulario_asesor()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el asesor: {str(e)}")

    def _eliminar_asesor(self):
        selected = self.tree_asesores.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un asesor para eliminar")
            return
            
        item = self.tree_asesores.item(selected[0])
        asesor_id = item['values'][0]
        asesor_nombre = item['values'][2]
        
        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar al asesor: {asesor_nombre}?"):
            try:
                if self.controlador.eliminar_asesor(asesor_id):
                    messagebox.showinfo("Éxito", "Asesor eliminado correctamente")
                    self._cargar_asesores()  # Recargar datos
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el asesor")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar el asesor: {str(e)}")

    def mostrar(self):
        # Ensure the controller is set before showing the window
        if not hasattr(self, 'controlador') or self.controlador is None:
            raise ValueError("Controller must be set before showing the window")
        
        # Refresh the catalog UI to ensure it has the latest data
        if hasattr(self, 'frame4') and hasattr(self, 'notebook'):
            # Destroy the existing catalog content
            for widget in self.frame4.winfo_children():
                widget.destroy()
            # Recreate the catalog content
            self._contenido_catalogo(self.frame4)
        
        # Start the main loop
        self.ventana.mainloop()