import customtkinter as ctk
import os
from PIL import (
    Image,
)  # Solo Image de Pillow es necesario ahora para abrir y opcionalmente redimensionar

# ImageTk ya no es estrictamente necesario si usamos CTkImage directamente con el objeto Image de Pillow

# Configuración inicial de CustomTkinter (apariencia)
ctk.set_appearance_mode("System")  # Puede ser "System", "Light", "Dark"
ctk.set_default_color_theme("blue")  # Tema de color


# --- Clases de Diálogo Personalizadas (sin cambios) ---
class ConfirmDialog(ctk.CTkToplevel):
    """Diálogo de confirmación simple (Sí/No)."""

    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x170")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(
            self, text=message, wraplength=380, font=("Arial", 12), justify="left"
        ).pack(pady=20, padx=10)

        frame_buttons = ctk.CTkFrame(self)
        frame_buttons.pack(pady=10)

        btn_yes = ctk.CTkButton(
            frame_buttons, text="Sí", command=self._on_yes, width=80
        )
        btn_yes.pack(side="left", padx=10)

        btn_no = ctk.CTkButton(frame_buttons, text="No", command=self._on_no, width=80)
        btn_no.pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self._on_no)
        self.wait_window()

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()

    def get_result(self):
        return self.result


class ChoiceDialog(ctk.CTkToplevel):
    """Diálogo para múltiples opciones."""

    def __init__(self, parent, title, message, choices):
        super().__init__(parent)
        self.title(title)
        num_choices = len(choices)
        height = 150 + num_choices * 45
        self.geometry(f"480x{height}")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(
            self, text=message, wraplength=460, font=("Arial", 12), justify="left"
        ).pack(pady=15, padx=10)

        frame_buttons = ctk.CTkFrame(self)
        frame_buttons.pack(pady=10)

        for text, value in choices:
            btn = ctk.CTkButton(
                frame_buttons,
                text=text,
                command=lambda v=value: self._on_choice(v),
                width=400,
            )
            btn.pack(pady=5, padx=10)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window()

    def _on_choice(self, value):
        self.result = value
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def get_result(self):
        return self.result


class SuggestionsPopup(ctk.CTkToplevel):
    """Popup para mostrar sugerencias de autocompletado."""

    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.entry_widget = entry_widget
        self.overrideredirect(True)
        self.withdraw()

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=280, height=100)
        self.scrollable_frame.pack(fill="both", expand=True)
        self.suggestion_buttons = []

    def show_suggestions(self, suggestions, x, y, height):
        for btn in self.suggestion_buttons:
            btn.destroy()
        self.suggestion_buttons = []

        if not suggestions:
            self.withdraw()
            return

        self.geometry(f"+{x}+{y + height + 2}")

        for suggestion in suggestions[:10]:
            btn = ctk.CTkButton(
                self.scrollable_frame,
                text=suggestion,
                command=lambda s=suggestion: self._select_suggestion(s),
                anchor="w",
                font=("Arial", 11),
            )
            btn.pack(fill="x", pady=1, padx=1)
            self.suggestion_buttons.append(btn)

        self.deiconify()
        self.attributes("-topmost", True)

    def _select_suggestion(self, suggestion):
        self.entry_widget.delete(0, ctk.END)
        self.entry_widget.insert(0, suggestion)
        self.withdraw()
        self.entry_widget.focus_set()

    def hide(self):
        self.withdraw()


class GestorPedidosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gestor de Pedidos e Inventario")
        self.geometry("900x830")

        self.archivo_bodega = "bodegac.txt"
        self.encoding_archivos = "latin-1"
        self._inicializar_bodega()
        self.lista_items_bodega_sugerencias = []
        self._cargar_items_bodega_para_sugerencias()

        # --- Frame Principal ---
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True)

        # --- Frame para el Logo ---
        self.frame_logo = ctk.CTkFrame(main_container, fg_color="#FF69B4")
        self.frame_logo.pack(fill="x", pady=(0, 5))

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, "Logo1.PNG")

            if not os.path.exists(logo_path):
                raise FileNotFoundError(
                    f"El archivo del logo no se encontró en: {logo_path}"
                )

            logo_image_pil = Image.open(logo_path)

            target_logo_width = 60
            target_logo_height = 60

            ratio_w = target_logo_width / logo_image_pil.width
            ratio_h = target_logo_height / logo_image_pil.height
            ratio = min(ratio_w, ratio_h)

            new_width = int(logo_image_pil.width * ratio)
            new_height = int(logo_image_pil.height * ratio)

            if hasattr(Image, "Resampling"):
                resampling_filter = Image.Resampling.LANCZOS
            elif hasattr(Image, "LANCZOS"):
                resampling_filter = Image.LANCZOS
            else:
                resampling_filter = Image.ANTIALIAS

            logo_image_pil_resized = logo_image_pil.resize(
                (new_width, new_height), resampling_filter
            )

            self.logo_ctk_image = ctk.CTkImage(
                light_image=logo_image_pil_resized,
                dark_image=logo_image_pil_resized,
                size=(new_width, new_height),
            )

            logo_label = ctk.CTkLabel(
                self.frame_logo, image=self.logo_ctk_image, text=""
            )
            logo_label.pack(pady=10)

        except FileNotFoundError as fnf_error:
            print(f"ADVERTENCIA AL CARGAR LOGO (FileNotFoundError): {fnf_error}")
            ctk.CTkLabel(
                self.frame_logo, text="Logo no encontrado", font=("Arial", 14)
            ).pack(pady=20)
        except Exception as e:
            print(f"ERROR DETALLADO AL CARGAR LOGO: {e}")
            print(f"Tipo de error: {type(e)}")
            ctk.CTkLabel(
                self.frame_logo, text="Error al cargar Logo", font=("Arial", 14)
            ).pack(pady=20)

        # --- Frame para el resto de la aplicación (debajo del logo) ---
        app_content_frame = ctk.CTkFrame(main_container)
        app_content_frame.pack(pady=0, padx=10, fill="both", expand=True)

        app_content_frame.grid_columnconfigure(0, weight=1)
        app_content_frame.grid_columnconfigure(1, weight=1)

        self.frame_superior_entradas = ctk.CTkFrame(app_content_frame)
        self.frame_superior_entradas.grid(
            row=0, column=0, columnspan=2, pady=(10, 0), sticky="ew"
        )

        self.frame_superior_entradas.grid_columnconfigure(0, weight=2)
        self.frame_superior_entradas.grid_columnconfigure(1, weight=1)
        self.frame_superior_entradas.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            self.frame_superior_entradas, text="Descripción:", font=("Arial", 13)
        ).grid(row=0, column=0, padx=(5, 0), pady=(5, 0), sticky="sw")
        self.entry_descripcion = ctk.CTkEntry(
            self.frame_superior_entradas, font=("Arial", 12)
        )
        self.entry_descripcion.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.entry_descripcion.bind("<Return>", self.procesar_elemento_enter)
        self.entry_descripcion.bind(
            "<KeyRelease>", self._actualizar_sugerencias_descripcion
        )
        self.entry_descripcion.bind(
            "<FocusOut>",
            lambda e: self.after(200, self._hide_suggestions_if_not_focused_popup),
        )

        self.suggestions_popup = SuggestionsPopup(self, self.entry_descripcion)

        ctk.CTkLabel(
            self.frame_superior_entradas, text="Cantidad:", font=("Arial", 13)
        ).grid(row=0, column=1, padx=(5, 0), pady=(5, 0), sticky="sw")
        self.entry_cantidad_pedido = ctk.CTkEntry(
            self.frame_superior_entradas, width=100, font=("Arial", 12)
        )
        self.entry_cantidad_pedido.grid(
            row=1, column=1, padx=5, pady=(0, 5), sticky="ew"
        )
        self.entry_cantidad_pedido.bind("<Return>", self.procesar_elemento_enter)

        ctk.CTkLabel(
            self.frame_superior_entradas, text="Archivo Pedido:", font=("Arial", 13)
        ).grid(row=0, column=2, padx=(5, 0), pady=(5, 0), sticky="sw")
        self.opciones_pedido = ["pdcentro", "pdpr", "pdst", "np"]
        self.combo_nombre_pedido = ctk.CTkComboBox(
            self.frame_superior_entradas,
            values=self.opciones_pedido,
            font=("Arial", 12),
            width=150,
        )
        self.combo_nombre_pedido.grid(row=1, column=2, padx=5, pady=(0, 5), sticky="ew")
        self.combo_nombre_pedido.set(self.opciones_pedido[0])

        self.btn_procesar = ctk.CTkButton(
            app_content_frame,
            text="Procesar Elemento",
            command=self.procesar_elemento,
            font=("Arial", 14),
            height=35,
        )
        self.btn_procesar.grid(row=1, column=0, columnspan=2, pady=(10, 10), sticky="n")

        self.frame_bodega = ctk.CTkFrame(app_content_frame)
        self.frame_bodega.grid(row=2, column=0, pady=5, padx=5, sticky="nsew")
        app_content_frame.grid_rowconfigure(2, weight=1)

        self.frame_pedido = ctk.CTkFrame(app_content_frame)
        self.frame_pedido.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")

        self.frame_mensajes = ctk.CTkFrame(app_content_frame)
        self.frame_mensajes.grid(
            row=3, column=0, columnspan=2, pady=10, padx=5, sticky="ew"
        )
        app_content_frame.grid_rowconfigure(3, weight=0)

        ctk.CTkLabel(
            self.frame_bodega,
            text="Inventario Bodega (bodegac.txt)",
            font=("Arial", 16, "bold"),
        ).pack(pady=5)
        self.texto_bodega = ctk.CTkTextbox(
            self.frame_bodega, font=("Courier New", 12), wrap="none"
        )
        self.texto_bodega.pack(pady=5, padx=5, fill="both", expand=True)

        # Frame para botones de bodega
        frame_botones_bodega = ctk.CTkFrame(self.frame_bodega)
        frame_botones_bodega.pack(pady=5)
        self.btn_refrescar_bodega = ctk.CTkButton(
            frame_botones_bodega,
            text="Refrescar Bodega",
            command=self.cargar_y_mostrar_bodega_con_sugerencias,
            font=("Arial", 12),
        )
        self.btn_refrescar_bodega.pack(side="left", padx=5)
        # NUEVO BOTÓN PARA ELIMINAR DE BODEGA
        self.btn_eliminar_bodega = ctk.CTkButton(
            frame_botones_bodega,
            text="Eliminar Item",
            command=self.eliminar_item_bodega,
            font=("Arial", 12),
            fg_color="tomato",
            hover_color="darkred",
        )
        self.btn_eliminar_bodega.pack(side="left", padx=5)

        ctk.CTkLabel(
            self.frame_pedido, text="Detalle del Pedido", font=("Arial", 16, "bold")
        ).pack(pady=5)
        self.texto_pedido_actual = ctk.CTkTextbox(
            self.frame_pedido, font=("Courier New", 12), wrap="none"
        )
        self.texto_pedido_actual.pack(pady=5, padx=5, fill="both", expand=True)

        frame_botones_pedido = ctk.CTkFrame(self.frame_pedido)
        frame_botones_pedido.pack(pady=5)
        self.btn_cargar_pedido = ctk.CTkButton(
            frame_botones_pedido,
            text="Cargar/Ver Pedido",
            command=self.cargar_y_mostrar_pedido,
            font=("Arial", 12),
        )
        self.btn_cargar_pedido.pack(side="left", padx=5)
        self.btn_limpiar_pedido_display = ctk.CTkButton(
            frame_botones_pedido,
            text="Limpiar Vista Pedido",
            command=lambda: self.texto_pedido_actual.delete("1.0", ctk.END),
            font=("Arial", 12),
        )
        self.btn_limpiar_pedido_display.pack(side="left", padx=5)
        # NUEVO BOTÓN PARA ELIMINAR DE PEDIDO
        self.btn_eliminar_pedido = ctk.CTkButton(
            frame_botones_pedido,
            text="Eliminar Item",
            command=self.eliminar_item_pedido,
            font=("Arial", 12),
            fg_color="tomato",
            hover_color="darkred",
        )
        self.btn_eliminar_pedido.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_mensajes, text="Mensajes:", font=("Arial", 14)).pack(
            anchor="w", pady=(5, 0)
        )
        self.texto_mensajes = ctk.CTkTextbox(
            self.frame_mensajes, height=100, font=("Arial", 12), wrap="word"
        )
        self.texto_mensajes.pack(pady=5, fill="x", expand=True)
        self.texto_mensajes.configure(state="disabled")

        self.btn_salir = ctk.CTkButton(
            main_container,
            text="Salir",
            command=self.quit_app,
            fg_color="#FF69B4",
            hover_color="#D4509A",
            font=("Arial", 14),
        )
        self.btn_salir.pack(pady=10, side="bottom", fill="x", padx=10)

        self.cargar_y_mostrar_bodega_con_sugerencias()

    def _cargar_items_bodega_para_sugerencias(self):
        self.lista_items_bodega_sugerencias = []
        lineas_bodega = self.leer_archivo_completo(self.archivo_bodega)
        if lineas_bodega:
            for linea in lineas_bodega:
                linea_stripped = linea.strip()
                if not linea_stripped or linea_stripped.startswith("#"):
                    continue
                partes_bodega = linea_stripped.split()
                if len(partes_bodega) >= 2:
                    descripcion_bodega = " ".join(partes_bodega[:-1]).strip()
                    if descripcion_bodega:
                        self.lista_items_bodega_sugerencias.append(descripcion_bodega)
            self.lista_items_bodega_sugerencias = sorted(
                list(set(self.lista_items_bodega_sugerencias))
            )

    def _actualizar_sugerencias_descripcion(self, event=None):
        texto_actual = self.entry_descripcion.get().lower()
        if not texto_actual:
            self.suggestions_popup.hide()
            return

        sugerencias_filtradas = [
            item
            for item in self.lista_items_bodega_sugerencias
            if texto_actual in item.lower()
        ]

        if sugerencias_filtradas:
            x = self.entry_descripcion.winfo_rootx()
            y = self.entry_descripcion.winfo_rooty()
            height = self.entry_descripcion.winfo_height()
            self.suggestions_popup.show_suggestions(sugerencias_filtradas, x, y, height)
        else:
            self.suggestions_popup.hide()

    def _hide_suggestions_if_not_focused_popup(self):
        focused_widget = self.focus_get()
        if (
            focused_widget != self.suggestions_popup
            and focused_widget != self.entry_descripcion
            and not (
                isinstance(focused_widget, ctk.CTkButton)
                and focused_widget.master == self.suggestions_popup.scrollable_frame
            )
        ):
            self.suggestions_popup.hide()

    def cargar_y_mostrar_bodega_con_sugerencias(self):
        self.cargar_y_mostrar_bodega()
        self._cargar_items_bodega_para_sugerencias()

    def quit_app(self):
        self.quit()
        self.destroy()

    def _inicializar_bodega(self):
        if not os.path.exists(self.archivo_bodega):
            print(
                f"Advertencia: El archivo '{self.archivo_bodega}' no existe. Se creará uno vacío."
            )
            try:
                with open(
                    self.archivo_bodega, "w", encoding=self.encoding_archivos
                ) as bodega:
                    bodega.write("# Inventario Central (bodegac.txt)\n")
                print(f"Archivo '{self.archivo_bodega}' creado.")
            except IOError as e:
                print(f"Error crítico al crear '{self.archivo_bodega}': {e}.")

    def escribir_archivo(self, ruta_archivo, lineas_lista, encabezado_opcional=None):
        try:
            with open(ruta_archivo, "w", encoding=self.encoding_archivos) as f_out:
                if encabezado_opcional and not os.path.exists(ruta_archivo):
                    f_out.write(encabezado_opcional)
                elif (
                    encabezado_opcional
                    and os.path.exists(ruta_archivo)
                    and os.path.getsize(ruta_archivo) == 0
                ):
                    f_out.write(encabezado_opcional)

                f_out.writelines(lineas_lista)
            return True
        except IOError as e:
            self.mostrar_mensaje(
                f"Error crítico al escribir en '{ruta_archivo}': {e}.", "error"
            )
            return False

    def leer_archivo_completo(self, ruta_archivo):
        try:
            with open(ruta_archivo, "r", encoding=self.encoding_archivos) as f:
                return f.readlines()
        except FileNotFoundError:
            return []
        except UnicodeDecodeError:
            self.mostrar_mensaje(
                f"Error de codificación al leer '{ruta_archivo}'. Verifique.", "error"
            )
            return None
        except IOError as e:
            self.mostrar_mensaje(f"Error al leer '{ruta_archivo}': {e}", "error")
            return None

    def cargar_y_mostrar_bodega(self):
        self.texto_bodega.configure(state="normal")
        self.texto_bodega.delete("1.0", ctk.END)
        lineas = self.leer_archivo_completo(self.archivo_bodega)
        if lineas is not None:
            if lineas:
                for linea in lineas:
                    self.texto_bodega.insert(ctk.END, linea)
            else:
                self.texto_bodega.insert(
                    ctk.END, f"# {self.archivo_bodega} está vacío o no existe.\n"
                )
        else:
            self.texto_bodega.insert(
                ctk.END, f"# Error al cargar '{self.archivo_bodega}'.\n"
            )
        self.texto_bodega.configure(state="disabled")

    def cargar_y_mostrar_pedido(self):
        nombre_base = self.combo_nombre_pedido.get()
        if not nombre_base:
            self.mostrar_mensaje(
                "Seleccione un archivo de pedido de la lista.", "warning"
            )
            return

        nombre_pedido_completo = nombre_base + ".txt"
        self.texto_pedido_actual.configure(state="normal")
        self.texto_pedido_actual.delete("1.0", ctk.END)

        lineas = self.leer_archivo_completo(nombre_pedido_completo)

        if lineas is not None:
            if lineas:
                self.texto_pedido_actual.insert(
                    ctk.END, f"# Contenido de: {nombre_pedido_completo}\n"
                )
                for linea in lineas:
                    self.texto_pedido_actual.insert(ctk.END, linea)
            elif os.path.exists(nombre_pedido_completo):
                self.texto_pedido_actual.insert(
                    ctk.END, f"# Archivo '{nombre_pedido_completo}' está vacío.\n"
                )
            else:
                self.texto_pedido_actual.insert(
                    ctk.END,
                    f"# Archivo '{nombre_pedido_completo}' no existe. Se creará al agregar elementos.\n",
                )
        else:
            self.texto_pedido_actual.insert(
                ctk.END, f"# Error al cargar '{nombre_pedido_completo}'.\n"
            )
        self.texto_pedido_actual.configure(state="disabled")

    def mostrar_mensaje(self, mensaje, tipo="info"):
        self.texto_mensajes.configure(state="normal")
        prefix = ""
        if tipo == "error":
            prefix = "ERROR: "
        elif tipo == "warning":
            prefix = "ADVERTENCIA: "
        else:
            prefix = "INFO: "
        self.texto_mensajes.insert(ctk.END, f"{prefix}{mensaje}\n")
        self.texto_mensajes.see(ctk.END)
        self.texto_mensajes.configure(state="disabled")

    def procesar_elemento_enter(self, event):
        self.procesar_elemento()

    def procesar_elemento(self):
        self.suggestions_popup.hide()

        descripcion = self.entry_descripcion.get().strip()
        cantidad_pedido_str = self.entry_cantidad_pedido.get().strip()

        if not descripcion:
            self.mostrar_mensaje(
                "La descripción del elemento no puede estar vacía.", "warning"
            )
            self.entry_descripcion.focus()
            return

        try:
            cantidad_pedido = int(cantidad_pedido_str)
            if cantidad_pedido <= 0:
                self.mostrar_mensaje(
                    "La cantidad para el pedido debe ser > 0.", "warning"
                )
                self.entry_cantidad_pedido.focus()
                return
        except ValueError:
            self.mostrar_mensaje("Cantidad para pedido inválida.", "error")
            self.entry_cantidad_pedido.focus()
            return

        self.mostrar_mensaje(
            f"Procesando: '{descripcion}', Cant. Pedido: {cantidad_pedido}", "info"
        )

        elementos_bodega_actuales = self.leer_archivo_completo(self.archivo_bodega)
        if elementos_bodega_actuales is None:
            self.mostrar_mensaje(
                "No se pudo leer bodega. Operación cancelada.", "error"
            )
            return

        elemento_en_bodega = False
        cantidad_bodega_actual_item = 0
        indice_bodega_item = -1
        descripcion_normalizada = descripcion.lower()

        for i, linea in enumerate(elementos_bodega_actuales):
            linea_stripped = linea.strip()
            if not linea_stripped or linea_stripped.startswith("#"):
                continue

            partes_bodega = linea_stripped.split()
            if len(partes_bodega) >= 2:
                desc_bodega_actual = " ".join(partes_bodega[:-1]).strip()
                if desc_bodega_actual.lower() == descripcion_normalizada:
                    elemento_en_bodega = True
                    indice_bodega_item = i
                    try:
                        cantidad_bodega_actual_item = int(partes_bodega[-1])
                    except ValueError:
                        cantidad_bodega_actual_item = 0
                    break

        if not elemento_en_bodega:
            dialog = ConfirmDialog(
                self,
                "Agregar a Bodega",
                f"El elemento '{descripcion}' no existe en bodega.\n¿Desea agregarlo con cantidad 0?",
            )
            if dialog.get_result():
                nueva_linea_bodega = f"    {descripcion} 0\n"
                elementos_bodega_actuales.append(nueva_linea_bodega)
                if self.escribir_archivo(
                    self.archivo_bodega, elementos_bodega_actuales
                ):
                    self.mostrar_mensaje(
                        f"'{descripcion}' agregado a bodega con cantidad 0.", "info"
                    )
                    self.cargar_y_mostrar_bodega_con_sugerencias()
                    cantidad_bodega_actual_item = 0
                    elemento_en_bodega = True
                    indice_bodega_item = len(elementos_bodega_actuales) - 1
                else:
                    self.mostrar_mensaje(
                        f"No se pudo agregar '{descripcion}' a bodega.", "error"
                    )
                    return
            else:
                self.mostrar_mensaje(
                    f"'{descripcion}' no fue agregado a bodega. No se puede procesar para pedido.",
                    "info",
                )
                return
        else:
            self.mostrar_mensaje(
                f"'{descripcion}' en bodega. Stock: {cantidad_bodega_actual_item}.",
                "info",
            )

        if elemento_en_bodega and cantidad_bodega_actual_item > 0:
            if cantidad_pedido > cantidad_bodega_actual_item:
                self.mostrar_mensaje(
                    f"Pedido ({cantidad_pedido}) para '{descripcion}' excede stock ({cantidad_bodega_actual_item}).",
                    "warning",
                )

            dialog_restar = ctk.CTkInputDialog(
                text=f"Stock de '{descripcion}': {cantidad_bodega_actual_item}.\n¿Cuántas unidades restar de bodega? (0-{cantidad_bodega_actual_item})\n(Enter o cancelar para no restar)",
                title="Restar de Bodega",
            )
            self.after(100, lambda: dialog_restar.attributes("-topmost", True))
            input_restar_str = dialog_restar.get_input()

            if input_restar_str is not None and input_restar_str.strip() != "":
                try:
                    cantidad_a_restar_de_bodega = int(input_restar_str)
                    if 0 <= cantidad_a_restar_de_bodega <= cantidad_bodega_actual_item:
                        if cantidad_a_restar_de_bodega > 0:
                            nueva_cantidad_bodega = (
                                cantidad_bodega_actual_item
                                - cantidad_a_restar_de_bodega
                            )
                            desc_original_item_bodega = " ".join(
                                elementos_bodega_actuales[indice_bodega_item]
                                .strip()
                                .split()[:-1]
                            )
                            elementos_bodega_actuales[indice_bodega_item] = (
                                f"    {desc_original_item_bodega} {nueva_cantidad_bodega}\n"
                            )
                            if self.escribir_archivo(
                                self.archivo_bodega, elementos_bodega_actuales
                            ):
                                self.mostrar_mensaje(
                                    f"Se restaron {cantidad_a_restar_de_bodega} de '{descripcion}'. Stock: {nueva_cantidad_bodega}.",
                                    "info",
                                )
                                self.cargar_y_mostrar_bodega_con_sugerencias()
                            else:
                                self.mostrar_mensaje(
                                    f"Error al actualizar stock de '{descripcion}'.",
                                    "error",
                                )
                                return
                        else:
                            self.mostrar_mensaje(
                                f"No se restaron unidades de '{descripcion}' de bodega.",
                                "info",
                            )
                    else:
                        self.mostrar_mensaje(
                            f"Cantidad a restar inválida. Debe ser entre 0 y {cantidad_bodega_actual_item}.",
                            "error",
                        )
                except ValueError:
                    self.mostrar_mensaje(
                        "Entrada para restar de bodega no es un número válido.", "error"
                    )
            else:
                self.mostrar_mensaje(
                    f"No se modificó el stock de '{descripcion}' en bodega.", "info"
                )

        elif elemento_en_bodega and cantidad_bodega_actual_item == 0:
            self.mostrar_mensaje(
                f"'{descripcion}' tiene 0 stock en bodega. No se puede restar.", "info"
            )

        nombre_pedido_base = self.combo_nombre_pedido.get()
        if not nombre_pedido_base:
            self.mostrar_mensaje("Seleccione un archivo de pedido.", "warning")
            return

        nombre_pedido_completo = nombre_pedido_base + ".txt"
        lineas_pedido_actual = self.leer_archivo_completo(nombre_pedido_completo)
        if lineas_pedido_actual is None:
            self.mostrar_mensaje(
                f"Error al leer pedido '{nombre_pedido_completo}'. Operación cancelada.",
                "error",
            )
            return

        elemento_en_pedido_actual = False
        cantidad_en_pedido_item_actual = 0
        indice_pedido_item_actual = -1
        accion_pedido_realizada = None

        for i, linea in enumerate(lineas_pedido_actual):
            linea_stripped = linea.strip()
            if not linea_stripped or linea_stripped.startswith("#"):
                continue

            partes_pedido = linea_stripped.split()
            if len(partes_pedido) >= 2:
                desc_pedido_item = " ".join(partes_pedido[:-1]).strip()
                if desc_pedido_item.lower() == descripcion_normalizada:
                    elemento_en_pedido_actual = True
                    indice_pedido_item_actual = i
                    try:
                        cantidad_en_pedido_item_actual = int(partes_pedido[-1])
                    except ValueError:
                        cantidad_en_pedido_item_actual = 0
                    break

        if elemento_en_pedido_actual:
            self.mostrar_mensaje(
                f"'{descripcion}' ya existe en '{nombre_pedido_completo}' (Cant: {cantidad_en_pedido_item_actual}).",
                "info",
            )
            choices = [
                (f"Reemplazar con {cantidad_pedido}", "reemplazar"),
                (
                    f"Sumar {cantidad_pedido} (Total: {cantidad_en_pedido_item_actual + cantidad_pedido})",
                    "sumar",
                ),
                ("No hacer nada", "nada"),
            ]
            choice_dialog = ChoiceDialog(
                self,
                "Modificar Pedido",
                f"'{descripcion}' ya está en el pedido '{nombre_pedido_base}'.\nCantidad actual: {cantidad_en_pedido_item_actual}\nCantidad nueva: {cantidad_pedido}",
                choices,
            )
            decision = choice_dialog.get_result()

            if decision == "reemplazar":
                desc_original_pedido = " ".join(
                    lineas_pedido_actual[indice_pedido_item_actual].strip().split()[:-1]
                )
                lineas_pedido_actual[indice_pedido_item_actual] = (
                    f"    {desc_original_pedido} {cantidad_pedido}\n"
                )
                accion_pedido_realizada = f"reemplazado con {cantidad_pedido}"
            elif decision == "sumar":
                desc_original_pedido = " ".join(
                    lineas_pedido_actual[indice_pedido_item_actual].strip().split()[:-1]
                )
                nueva_cantidad_en_pedido = (
                    cantidad_en_pedido_item_actual + cantidad_pedido
                )
                lineas_pedido_actual[indice_pedido_item_actual] = (
                    f"    {desc_original_pedido} {nueva_cantidad_en_pedido}\n"
                )
                accion_pedido_realizada = (
                    f"sumado, nueva cant: {nueva_cantidad_en_pedido}"
                )
            elif decision == "nada":
                self.mostrar_mensaje(
                    f"No se modificó '{descripcion}' en el pedido.", "info"
                )
            else:
                self.mostrar_mensaje(
                    f"Modificación de '{descripcion}' en pedido cancelada.", "info"
                )
        else:
            lineas_pedido_actual.append(f"    {descripcion} {cantidad_pedido}\n")
            accion_pedido_realizada = f"agregado con cant {cantidad_pedido}"

        if accion_pedido_realizada:
            encabezado = f"# Pedido: {nombre_pedido_base}\n"
            if self.escribir_archivo(
                nombre_pedido_completo,
                lineas_pedido_actual,
                encabezado_opcional=encabezado,
            ):
                self.mostrar_mensaje(
                    f"'{descripcion}' {accion_pedido_realizada} en '{nombre_pedido_completo}'.",
                    "info",
                )
                self.cargar_y_mostrar_pedido()
            else:
                self.mostrar_mensaje(
                    f"Error al escribir en '{nombre_pedido_completo}'.", "error"
                )

        self.entry_descripcion.delete(0, ctk.END)
        self.entry_cantidad_pedido.delete(0, ctk.END)
        self.entry_descripcion.focus()

    # --- NUEVAS FUNCIONES PARA ELIMINAR ITEMS ---

    def eliminar_item_bodega(self):
        """Abre un diálogo para eliminar un item de la bodega."""
        dialog = ctk.CTkInputDialog(
            text="Ingrese la descripción EXACTA del item a eliminar de la Bodega:",
            title="Eliminar Item de Bodega",
        )
        self.after(100, lambda: dialog.attributes("-topmost", True))
        descripcion_a_eliminar = dialog.get_input()

        if not descripcion_a_eliminar or not descripcion_a_eliminar.strip():
            self.mostrar_mensaje("Operación de eliminación cancelada.", "info")
            return

        descripcion_a_eliminar = descripcion_a_eliminar.strip()
        descripcion_normalizada = descripcion_a_eliminar.lower()

        lineas_bodega = self.leer_archivo_completo(self.archivo_bodega)
        if lineas_bodega is None:
            self.mostrar_mensaje(
                "No se pudo leer la bodega para eliminar el item.", "error"
            )
            return

        indice_a_eliminar = -1
        desc_encontrada = ""
        for i, linea in enumerate(lineas_bodega):
            linea_stripped = linea.strip()
            if not linea_stripped or linea_stripped.startswith("#"):
                continue
            partes = linea_stripped.split()
            if len(partes) >= 2:
                desc_actual = " ".join(partes[:-1]).strip()
                if desc_actual.lower() == descripcion_normalizada:
                    indice_a_eliminar = i
                    desc_encontrada = desc_actual
                    break

        if indice_a_eliminar != -1:
            confirm_dialog = ConfirmDialog(
                self,
                "Confirmar Eliminación",
                f"¿Está seguro que desea eliminar '{desc_encontrada}' permanentemente de la bodega?",
            )
            if confirm_dialog.get_result():
                lineas_bodega.pop(indice_a_eliminar)
                if self.escribir_archivo(self.archivo_bodega, lineas_bodega):
                    self.mostrar_mensaje(
                        f"Item '{desc_encontrada}' eliminado de la bodega.", "info"
                    )
                    self.cargar_y_mostrar_bodega_con_sugerencias()  # Refresca UI y sugerencias
                else:
                    self.mostrar_mensaje(
                        f"Error al escribir en bodega después de eliminar.", "error"
                    )
            else:
                self.mostrar_mensaje("Eliminación cancelada por el usuario.", "info")
        else:
            self.mostrar_mensaje(
                f"Item '{descripcion_a_eliminar}' no encontrado en la bodega.",
                "warning",
            )

    def eliminar_item_pedido(self):
        """Abre un diálogo para eliminar un item del pedido actual."""
        nombre_pedido_base = self.combo_nombre_pedido.get()
        if not nombre_pedido_base:
            self.mostrar_mensaje("Seleccione un archivo de pedido primero.", "warning")
            return
        nombre_pedido_completo = nombre_pedido_base + ".txt"

        dialog = ctk.CTkInputDialog(
            text=f"Item a eliminar del pedido '{nombre_pedido_base}':",
            title="Eliminar Item de Pedido",
        )
        self.after(100, lambda: dialog.attributes("-topmost", True))
        descripcion_a_eliminar = dialog.get_input()

        if not descripcion_a_eliminar or not descripcion_a_eliminar.strip():
            self.mostrar_mensaje("Operación de eliminación cancelada.", "info")
            return

        descripcion_a_eliminar = descripcion_a_eliminar.strip()
        descripcion_normalizada = descripcion_a_eliminar.lower()

        lineas_pedido = self.leer_archivo_completo(nombre_pedido_completo)
        if lineas_pedido is None:
            return

        indice_a_eliminar = -1
        desc_encontrada = ""
        for i, linea in enumerate(lineas_pedido):
            linea_stripped = linea.strip()
            if not linea_stripped or linea_stripped.startswith("#"):
                continue
            partes = linea_stripped.split()
            if len(partes) >= 2:
                desc_actual = " ".join(partes[:-1]).strip()
                if desc_actual.lower() == descripcion_normalizada:
                    indice_a_eliminar = i
                    desc_encontrada = desc_actual
                    break

        if indice_a_eliminar != -1:
            confirm_dialog = ConfirmDialog(
                self,
                "Confirmar Eliminación",
                f"¿Está seguro que desea eliminar '{desc_encontrada}' del pedido '{nombre_pedido_base}'?",
            )
            if confirm_dialog.get_result():
                lineas_pedido.pop(indice_a_eliminar)
                if self.escribir_archivo(nombre_pedido_completo, lineas_pedido):
                    self.mostrar_mensaje(
                        f"Item '{desc_encontrada}' eliminado de '{nombre_pedido_completo}'.",
                        "info",
                    )
                    self.cargar_y_mostrar_pedido()  # Refresca la vista del pedido
                else:
                    self.mostrar_mensaje(
                        f"Error al escribir en el pedido '{nombre_pedido_completo}'.",
                        "error",
                    )
            else:
                self.mostrar_mensaje("Eliminación cancelada por el usuario.", "info")
        else:
            self.mostrar_mensaje(
                f"Item '{descripcion_a_eliminar}' no encontrado en '{nombre_pedido_completo}'.",
                "warning",
            )


if __name__ == "__main__":
    app = GestorPedidosApp()
    app.mainloop()
