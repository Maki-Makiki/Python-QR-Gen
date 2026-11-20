import io
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont

ver = "1.2.1"
autor = "Maki"


class GeneradorQRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de QR Portable v" + ver + " - by " + autor)

        # Cargar el ícono de la ventana y barra de tareas
        try:
            ruta_icono = self.obtener_ruta_recurso("QR Code Icon.png")
            self.icono_img = ImageTk.PhotoImage(Image.open(ruta_icono))
            self.root.iconphoto(True, self.icono_img)
            self.root.wm_iconphoto(True, self.icono_img)
        except Exception as e:
            print("No se pudo cargar el ícono:", e)

        self.root.geometry("400x520")
        self.root.minsize(320, 420)

        self.qr_pil_image = None
        self.qr_tk_image = None

        self.es_oscuro = self.detectar_tema_oscuro()

        if self.es_oscuro:
            self.colores = {
                "bg": "#1e1e1e",
                "fg": "#f3f3f3",
                "input_bg": "#2d2d2d",
                "input_fg": "#ffffff",
                "btn_sec_bg": "#333333",
                "btn_sec_fg": "#ffffff",
                "preview_bg": "#252526",
                "accent": "#0078D7",
                "select_bg": "#2d2d2d",
            }
        else:
            self.colores = {
                "bg": "#f3f3f3",
                "fg": "#1a1a1a",
                "input_bg": "#ffffff",
                "input_fg": "#000000",
                "btn_sec_bg": "#e1e1e1",
                "btn_sec_fg": "#1a1a1a",
                "preview_bg": "#e8e8e8",
                "accent": "#0078D7",
                "select_bg": "#ffffff",
            }

        self.root.configure(bg=self.colores["bg"])

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        # Fila 0: Etiqueta
        tk.Label(
            root,
            text="Ingresa la URL o texto:",
            font=("Arial", 11),
            bg=self.colores["bg"],
            fg=self.colores["fg"],
        ).grid(row=0, column=0, pady=(15, 5), padx=20, sticky="w")

        # Fila 1: Caja de Texto
        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self.al_escribir)

        self.url_entry = tk.Entry(
            root,
            textvariable=self.url_var,
            font=("Arial", 11),
            bg=self.colores["input_bg"],
            fg=self.colores["input_fg"],
            insertbackground=self.colores["fg"],
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        self.url_entry.grid(row=1, column=0, pady=5, padx=20, sticky="ew", ipady=3)
        self.url_entry.focus()

        # Fila 2: Controles 2x2
        frame_controles = tk.Frame(root, bg=self.colores["bg"])
        frame_controles.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        frame_controles.columnconfigure(0, weight=1)
        frame_controles.columnconfigure(1, weight=1)

        self.auto_var = tk.BooleanVar(value=True)
        self.chk_auto = tk.Checkbutton(
            frame_controles,
            text="AutoGenerar QR",
            variable=self.auto_var,
            command=self.al_cambiar_opcion,
            font=("Arial", 10),
            bg=self.colores["bg"],
            fg=self.colores["fg"],
            activebackground=self.colores["bg"],
            activeforeground=self.colores["fg"],
            selectcolor=self.colores["select_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.chk_auto.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.mostrar_url_var = tk.BooleanVar(value=False)
        self.chk_url = tk.Checkbutton(
            frame_controles,
            text="Mostrar URL debajo",
            variable=self.mostrar_url_var,
            command=self.al_cambiar_opcion,
            font=("Arial", 10),
            bg=self.colores["bg"],
            fg=self.colores["fg"],
            activebackground=self.colores["bg"],
            activeforeground=self.colores["fg"],
            selectcolor=self.colores["select_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.chk_url.grid(row=0, column=1, sticky="w", pady=(0, 8))

        self.btn_generar = tk.Button(
            frame_controles,
            text="Generar QR",
            command=lambda: self.generar_qr(silencioso=False),
            bg=self.colores["accent"],
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.btn_generar.grid(row=1, column=0, sticky="ew", padx=(0, 5), ipady=4)

        self.btn_guardar = tk.Button(
            frame_controles,
            text="Guardar como...",
            command=self.guardar_qr,
            state=tk.DISABLED,
            font=("Arial", 10),
            bg=self.colores["btn_sec_bg"],
            fg=self.colores["btn_sec_fg"],
            relief="flat",
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.btn_guardar.grid(row=1, column=1, sticky="ew", padx=(5, 0), ipady=4)

        # Fila 3: Área para mostrar el QR (Canvas para renderizado fiable en Linux y Windows)
        self.canvas_qr = tk.Canvas(
            root,
            bg=self.colores["preview_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas_qr.grid(row=3, column=0, pady=(5, 20), padx=20, sticky="nsew")
        self.canvas_qr.bind("<Configure>", self.redimensionar_preview)

        # Menú contextual (Clic derecho en la imagen)
        self.menu_qr = tk.Menu(
            root,
            tearoff=0,
            bg=self.colores["input_bg"],
            fg=self.colores["fg"],
            activebackground=self.colores["accent"],
            activeforeground="white",
        )
        self.menu_qr.add_command(
            label="Copiar imagen al portapapeles", command=self.copiar_al_portapapeles
        )
        self.menu_qr.add_command(label="Guardar como...", command=self.guardar_qr)

        self.canvas_qr.bind("<Button-3>", self.mostrar_menu_qr)

        # Pintar la barra superior en oscuro una vez que la ventana ya sea visible
        if self.es_oscuro:
            self.root.after(50, self.pintar_barra_oscura)

    def detectar_tema_oscuro(self):
        # 1. Windows
        if sys.platform == "win32":
            try:
                import winreg

                ruta = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ruta) as clave:
                    valor, _ = winreg.QueryValueEx(clave, "AppsUseLightTheme")
                    return valor == 0
            except Exception:
                pass
        # 2. Linux (BazziteOS / Fedora KDE o GNOME)
        elif sys.platform.startswith("linux"):
            try:
                salida = subprocess.check_output(
                    ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                if "dark" in salida.lower():
                    return True
            except Exception:
                pass
            try:
                for cmd in ("kreadconfig6", "kreadconfig5"):
                    salida = subprocess.check_output(
                        [cmd, "--group", "General", "--key", "ColorScheme"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                    )
                    if "dark" in salida.lower():
                        return True
            except Exception:
                pass
        return False

    def obtener_ruta_recurso(self, nombre_archivo):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, nombre_archivo)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)

    def pintar_barra_oscura(self):
        if sys.platform == "win32":
            try:
                import ctypes

                hwnd = ctypes.windll.user32.GetAncestor(self.root.winfo_id(), 2)
                valor = ctypes.c_int(1)
                for atributo in (20, 19):
                    res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)
                    )
                    if res == 0:
                        break
            except Exception:
                pass

    def al_escribir(self, *args):
        if self.auto_var.get():
            self.generar_qr(silencioso=True)

    def al_cambiar_opcion(self):
        if self.url_var.get().strip():
            self.generar_qr(silencioso=True)

    def cargar_fuente(self, tamano):
        for nombre_fuente in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
            try:
                return ImageFont.truetype(nombre_fuente, tamano)
            except IOError:
                continue
        return ImageFont.load_default()

    def generar_qr(self, silencioso=False):
        texto = self.url_var.get().strip()

        if not texto:
            if not silencioso:
                messagebox.showwarning(
                    "Atención", "Por favor, escribe una web o texto primero."
                )
            self.qr_pil_image = None
            self.qr_tk_image = None
            self.btn_guardar.config(state=tk.DISABLED)
            self.actualizar_vista_previa()
            return

        qr = qrcode.QRCode(version=1, box_size=10, border=3)
        qr.add_data(texto)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        if self.mostrar_url_var.get():
            ancho_qr, alto_qr = img_qr.size
            margen_lateral = 20
            ancho_max_texto = ancho_qr - (margen_lateral * 2)

            tamano_fuente = 22
            fuente = self.cargar_fuente(tamano_fuente)
            draw_temp = ImageDraw.Draw(img_qr)

            while tamano_fuente > 10:
                bbox = draw_temp.textbbox((0, 0), texto, font=fuente)
                ancho_texto = bbox[2] - bbox[0]
                if ancho_texto <= ancho_max_texto:
                    break
                tamano_fuente -= 1
                fuente = self.cargar_fuente(tamano_fuente)

            bbox = draw_temp.textbbox((0, 0), texto, font=fuente)
            ancho_texto = bbox[2] - bbox[0]

            borde_qr = 30
            separacion = 15

            pos_y = (alto_qr - borde_qr) + separacion - bbox[1]
            alto_total = pos_y + bbox[3] + separacion

            lienzo = Image.new("RGB", (ancho_qr, alto_total), "white")
            lienzo.paste(img_qr, (0, 0))

            draw = ImageDraw.Draw(lienzo)
            pos_x = (ancho_qr - ancho_texto) // 2
            draw.text((pos_x, pos_y), texto, fill="black", font=fuente)

            self.qr_pil_image = lienzo
        else:
            self.qr_pil_image = img_qr

        self.btn_guardar.config(state=tk.NORMAL)
        self.actualizar_vista_previa()

    def redimensionar_preview(self, event):
        self.actualizar_vista_previa(event.width, event.height)

    def actualizar_vista_previa(self, ancho_disp=None, alto_disp=None):
        if ancho_disp is None or alto_disp is None:
            self.canvas_qr.update_idletasks()
            ancho_disp = self.canvas_qr.winfo_width()
            alto_disp = self.canvas_qr.winfo_height()

        if ancho_disp < 20 or alto_disp < 20:
            return

        self.canvas_qr.delete("all")

        # Si no hay QR generado, mostrar el texto de ayuda centrado
        if not self.qr_pil_image:
            self.canvas_qr.create_text(
                ancho_disp // 2,
                alto_disp // 2,
                text="Aquí aparecerá tu QR",
                fill=self.colores["fg"],
                font=("Arial", 10),
            )
            return

        max_w = ancho_disp - 20
        max_h = alto_disp - 20

        img_w, img_h = self.qr_pil_image.size
        ratio = min(max_w / img_w, max_h / img_h)
        nuevo_w = max(1, int(img_w * ratio))
        nuevo_h = max(1, int(img_h * ratio))

        img_resized = self.qr_pil_image.resize(
            (nuevo_w, nuevo_h), Image.Resampling.LANCZOS
        )
        self.qr_tk_image = ImageTk.PhotoImage(img_resized)
        self.canvas_qr.create_image(
            ancho_disp // 2,
            alto_disp // 2,
            image=self.qr_tk_image,
            anchor="center",
        )

    def guardar_qr(self):
        if self.qr_pil_image:
            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("Imagen PNG", "*.png"), ("Imagen JPEG", "*.jpg")],
                title="Guardar código QR",
                initialfile="mi_codigo_qr.png",
            )
            if ruta_archivo:
                self.qr_pil_image.save(ruta_archivo)
                messagebox.showinfo("Éxito", "Código QR guardado correctamente.")

    def mostrar_menu_qr(self, event):
        if self.qr_pil_image:
            try:
                self.menu_qr.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu_qr.grab_release()

    def copiar_al_portapapeles(self):
        if not self.qr_pil_image:
            return

        try:
            # --- WINDOWS ---
            if sys.platform == "win32":
                import ctypes

                salida = io.BytesIO()
                self.qr_pil_image.convert("RGB").save(salida, "BMP")
                datos_dib = salida.getvalue()[14:]
                salida.close()

                CF_DIB = 8
                GMEM_MOVEABLE = 0x0002

                kernel32 = ctypes.windll.kernel32
                user32 = ctypes.windll.user32

                kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
                kernel32.GlobalAlloc.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

                h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(datos_dib))
                p_global = kernel32.GlobalLock(h_global)
                ctypes.memmove(p_global, datos_dib, len(datos_dib))
                kernel32.GlobalUnlock(h_global)

                user32.OpenClipboard(None)
                user32.EmptyClipboard()
                user32.SetClipboardData(CF_DIB, h_global)
                user32.CloseClipboard()

            # --- LINUX (Wayland / X11) ---
            elif sys.platform.startswith("linux"):
                salida = io.BytesIO()
                self.qr_pil_image.save(salida, "PNG")
                datos_png = salida.getvalue()
                salida.close()

                copiado = False
                for cmd in (
                    ["wl-copy", "--type", "image/png"],
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-i"],
                ):
                    try:
                        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                        proc.communicate(input=datos_png)
                        if proc.returncode == 0:
                            copiado = True
                            break
                    except FileNotFoundError:
                        continue

                if not copiado:
                    messagebox.showwarning(
                        "Aviso",
                        "Instala 'wl-clipboard' o 'xclip' en tu sistema para copiar imágenes.",
                    )
                    return

            titulo_original = self.root.title()
            self.root.title("¡QR copiado al portapapeles!")
            self.root.after(1500, lambda: self.root.title(titulo_original))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar al portapapeles:\n{e}")


if __name__ == "__main__":
    try:
        ventana = tk.Tk()
        app = GeneradorQRApp(ventana)
        ventana.mainloop()
    except Exception as e:
        import traceback

        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror("Error al iniciar", traceback.format_exc())
