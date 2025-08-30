import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import sys

# --- INICIO: Lógica del programa ---


def leer_archivo(nombre_archivo):
    """Lee un archivo y devuelve una lista de líneas. Si no existe, devuelve una lista vacía."""
    if not os.path.exists(nombre_archivo):
        print(f"Info: El archivo {nombre_archivo} no existe, se tratará como vacío.")
        return []
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return archivo.readlines()
    except Exception as e:
        print(f"Error al leer el archivo {nombre_archivo}: {e}")
        return None


def escribir_archivo(nombre_archivo, lineas):
    """Escribe una lista de líneas en un archivo, ordenándolas alfabéticamente."""
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            # Ordenar items alfabéticamente antes de escribir
            lineas.sort()
            archivo.writelines(lineas)
    except Exception as e:
        print(f"Error al escribir en el archivo {nombre_archivo}: {e}")


def procesar_item_bodega(linea):
    """Procesa un item de un archivo de bodega. Devuelve nombre y cantidad."""
    match = re.search(r"(\s+\d+)$", linea)
    if not match:
        return None, None
    cantidad = int(match.group(1).strip())
    nombre = linea[: match.start()].strip()
    return nombre, cantidad


def procesar_item_archivo(item, linea_numero=None, archivo_nombre=None):
    """Procesa un item de los archivos de entrada. Devuelve nombre y cantidad."""
    partes = item.strip().rsplit(maxsplit=2)
    if len(partes) < 2:
        print(
            f"Error: Formato inválido en la línea {linea_numero} del archivo {archivo_nombre}: {item.strip()}"
        )
        return None, None
    nombre = " ".join(partes[:-1]).strip()
    try:
        cantidad_str = partes[-1]
        if cantidad_str.lower().endswith("ok"):
            cantidad_str = cantidad_str[:-2].strip()
        cantidad = int(cantidad_str)
    except ValueError:
        print(
            f"Error: La cantidad no es un número válido en la línea {linea_numero} del archivo {archivo_nombre}: {item.strip()}"
        )
        return None, None
    return nombre, cantidad


def buscar_item_en_bodega(nombre, bodega_lineas):
    """Busca un item en una lista de líneas y devuelve su índice y cantidad."""
    for i, linea in enumerate(bodega_lineas):
        nombre_bodega, cantidad_bodega = procesar_item_bodega(linea)
        if nombre_bodega and nombre_bodega.strip().lower() == nombre.strip().lower():
            return i, cantidad_bodega
    return None, 0


def eliminar_duplicados_bodega(bodega_lineas):
    """Elimina items duplicados en una lista de líneas, sumando sus cantidades."""
    items_unicos = {}
    for linea in bodega_lineas:
        nombre, cantidad = procesar_item_bodega(linea)
        if nombre is None or cantidad is None:
            continue
        nombre_limpio = nombre.strip().lower()
        if nombre_limpio in items_unicos:
            items_unicos[nombre_limpio]["cantidad"] += cantidad
        else:
            items_unicos[nombre_limpio] = {
                "cantidad": cantidad,
                "nombre_original": nombre,
            }

    bodega_sin_duplicados = [
        f"    {datos['nombre_original']} {datos['cantidad']}\n"
        for _, datos in items_unicos.items()
    ]
    return bodega_sin_duplicados


# --- FIN: Lógica del programa ---


# --- INICIO: Clase de la Interfaz Gráfica ---


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Bodega - Transferencias y Compras")
        self.root.geometry("800x600")

        self.archivos_a_analizar = []

        # --- Creación de Widgets ---
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        files_frame = tk.LabelFrame(
            main_frame, text="1. Archivos de Entrada (con 'ok')", padx=10, pady=10
        )
        files_frame.pack(fill=tk.X, pady=(0, 10))
        self.select_button = tk.Button(
            files_frame,
            text="Seleccionar Archivos...",
            command=self.seleccionar_archivos_transferencia,
        )
        self.select_button.pack(side=tk.LEFT)
        self.selected_files_label = tk.Label(
            files_frame,
            text="Ningún archivo seleccionado",
            wraplength=600,
            justify=tk.LEFT,
        )
        self.selected_files_label.pack(side=tk.LEFT, padx=(10, 0))

        files_config_frame = tk.LabelFrame(
            main_frame, text="2. Archivos de Inventario", padx=10, pady=10
        )
        files_config_frame.pack(fill=tk.X, pady=(0, 10))

        origen_label = tk.Label(files_config_frame, text="Archivo Bodega:")
        origen_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.origen_file_entry = tk.Entry(files_config_frame)
        self.origen_file_entry.insert(0, "bodegac.txt")
        self.origen_file_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        self.browse_origen_button = tk.Button(
            files_config_frame,
            text="...",
            command=lambda: self.seleccionar_archivo_inventario(self.origen_file_entry),
        )
        self.browse_origen_button.grid(row=0, column=2)

        destino_label = tk.Label(files_config_frame, text="Archivo Local:")
        destino_label.grid(row=1, column=0, sticky="w")
        self.destino_file_entry = tk.Entry(files_config_frame)
        self.destino_file_entry.insert(0, "local.txt")
        self.destino_file_entry.grid(row=1, column=1, sticky="ew", padx=(5, 5))
        self.browse_destino_button = tk.Button(
            files_config_frame,
            text="...",
            command=lambda: self.seleccionar_archivo_inventario(
                self.destino_file_entry
            ),
        )
        self.browse_destino_button.grid(row=1, column=2)

        files_config_frame.grid_columnconfigure(1, weight=1)

        action_frame = tk.LabelFrame(main_frame, text="3. Acciones", padx=10, pady=10)
        action_frame.pack(fill=tk.X, pady=(5, 10))

        self.process_button = tk.Button(
            action_frame,
            text="Realizar Transferencia",
            command=self.procesar_todo,
            font=("Helvetica", 10, "bold"),
            bg="#D5E8D4",
        )
        self.process_button.pack(
            side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(0, 5)
        )

        # --- NUEVO BOTÓN ---
        self.add_purchase_button = tk.Button(
            action_frame,
            text="Agregar Compra a Bodega",
            command=self.agregar_compra,
            font=("Helvetica", 10, "bold"),
            bg="#FFF2CC",
        )
        self.add_purchase_button.pack(
            side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(5, 5)
        )

        self.list_zero_button = tk.Button(
            action_frame, text="Listar Items en Cero", command=self.listar_items_cero
        )
        self.list_zero_button.pack(
            side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(5, 0)
        )

        console_frame = tk.LabelFrame(
            main_frame, text="Registro de Actividad", padx=10, pady=10
        )
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_output = scrolledtext.ScrolledText(
            console_frame, wrap=tk.WORD, state="disabled", font=("Courier New", 11)
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)

    def seleccionar_archivos_transferencia(self):
        self.archivos_a_analizar = filedialog.askopenfilenames(
            title="Seleccione los archivos para analizar",
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")),
        )
        if self.archivos_a_analizar:
            nombres = "\n".join(
                [os.path.basename(ruta) for ruta in self.archivos_a_analizar]
            )
            self.selected_files_label.config(text=f"Seleccionados:\n{nombres}")
        else:
            self.selected_files_label.config(text="Ningún archivo seleccionado")

    def seleccionar_archivo_inventario(self, entry_widget):
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccione el archivo de inventario",
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")),
        )
        if ruta_archivo:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ruta_archivo)

    def log_message(self, message):
        self.console_output.config(state="normal")
        self.console_output.insert(tk.END, message)
        self.console_output.see(tk.END)
        self.console_output.config(state="disabled")

    def procesar_todo(self):
        self.console_output.config(state="normal")
        self.console_output.delete("1.0", tk.END)
        self.console_output.config(state="disabled")

        stdout_backup = sys.stdout
        sys.stdout = self

        try:
            archivo_origen_path = self.origen_file_entry.get()
            archivo_destino_path = self.destino_file_entry.get()

            if (
                not self.archivos_a_analizar
                or not archivo_origen_path
                or not archivo_destino_path
            ):
                messagebox.showwarning(
                    "Faltan Datos",
                    "Por favor, complete todos los campos: archivos de entrada, bodega y local.",
                )
                return
            if archivo_origen_path == archivo_destino_path:
                messagebox.showwarning(
                    "Error de Lógica",
                    "El archivo de bodega y local no pueden ser el mismo.",
                )
                return

            print("--- Iniciando proceso de TRANSFERENCIA ---\n")

            bodega_origen = leer_archivo(archivo_origen_path)
            bodega_destino = leer_archivo(archivo_destino_path)
            if bodega_origen is None or bodega_destino is None:
                return

            for archivo in self.archivos_a_analizar:
                print(f"\n--- Analizando archivo: {os.path.basename(archivo)} ---")
                lineas = leer_archivo(archivo)
                if lineas is None:
                    continue

                for linea_numero, linea in enumerate(lineas, start=1):
                    if linea.strip().lower().endswith("ok"):
                        item_procesar = linea.strip()[:-2].strip()
                        nombre, cant_a_transferir = procesar_item_archivo(
                            item_procesar, linea_numero, os.path.basename(archivo)
                        )
                        if nombre is None or cant_a_transferir is None:
                            continue

                        indice_origen, cant_origen = buscar_item_en_bodega(
                            nombre, bodega_origen
                        )

                        if indice_origen is None:
                            print(
                                f"INFO: Item '{nombre}' no encontrado en bodega. Se agregará con stock 0."
                            )
                            bodega_origen.append(f"    {nombre.strip()} 0\n")
                            indice_origen, cant_origen = buscar_item_en_bodega(
                                nombre, bodega_origen
                            )

                        if cant_origen < cant_a_transferir:
                            print(
                                f"AVISO: Stock insuficiente en '{os.path.basename(archivo_origen_path)}' para '{nombre}'. Se necesitan {cant_a_transferir}, hay {cant_origen}. No se transfiere."
                            )
                            continue

                        print(
                            f"Transfiriendo: {nombre} (Cantidad: {cant_a_transferir})"
                        )

                        nueva_cant_origen = cant_origen - cant_a_transferir
                        print(
                            f"  - Bodega ({os.path.basename(archivo_origen_path)}): {cant_origen} -> {nueva_cant_origen}"
                        )

                        bodega_origen[indice_origen] = (
                            f"    {nombre.strip()} {nueva_cant_origen}\n"
                        )

                        indice_destino, cant_destino = buscar_item_en_bodega(
                            nombre, bodega_destino
                        )
                        nueva_cant_destino = cant_destino + cant_a_transferir
                        print(
                            f"  - Local ({os.path.basename(archivo_destino_path)}): {cant_destino} -> {nueva_cant_destino}"
                        )

                        if indice_destino is not None:
                            bodega_destino[indice_destino] = (
                                f"    {nombre.strip()} {nueva_cant_destino}\n"
                            )
                        else:
                            bodega_destino.append(
                                f"    {nombre.strip()} {nueva_cant_destino}\n"
                            )

            print("\n--- Consolidando y guardando cambios ---")
            bodega_destino = eliminar_duplicados_bodega(bodega_destino)

            escribir_archivo(archivo_origen_path, bodega_origen)
            escribir_archivo(archivo_destino_path, bodega_destino)
            print("\n¡Transferencia completada y archivos actualizados correctamente!")
            messagebox.showinfo(
                "Proceso Completado",
                "La transferencia de inventario se ha completado exitosamente.",
            )

        except Exception as e:
            print(f"\n--- Ocurrió un error inesperado ---")
            print(str(e))
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")
        finally:
            sys.stdout = sys.__stdout__

    # --- NUEVA FUNCIÓN ---
    def agregar_compra(self):
        """Lee los archivos seleccionados y agrega las cantidades al archivo de bodega."""
        self.console_output.config(state="normal")
        self.console_output.delete("1.0", tk.END)
        self.console_output.config(state="disabled")

        stdout_backup = sys.stdout
        sys.stdout = self

        try:
            archivo_bodega_path = self.origen_file_entry.get()

            if not self.archivos_a_analizar or not archivo_bodega_path:
                messagebox.showwarning(
                    "Faltan Datos",
                    "Por favor, seleccione los archivos de compra y especifique el archivo de Bodega.",
                )
                return

            print("--- Iniciando proceso de AGREGAR COMPRA ---\n")

            bodega = leer_archivo(archivo_bodega_path)
            if bodega is None:
                return

            for archivo in self.archivos_a_analizar:
                print(
                    f"\n--- Analizando archivo de compra: {os.path.basename(archivo)} ---"
                )
                lineas = leer_archivo(archivo)
                if lineas is None:
                    continue

                for linea_numero, linea in enumerate(lineas, start=1):
                    if linea.strip().lower().endswith("ok"):
                        item_procesar = linea.strip()[:-2].strip()
                        nombre, cant_a_agregar = procesar_item_archivo(
                            item_procesar, linea_numero, os.path.basename(archivo)
                        )
                        if nombre is None or cant_a_agregar is None:
                            continue

                        indice, cant_existente = buscar_item_en_bodega(nombre, bodega)

                        print(f"Agregando: {nombre} (Cantidad: {cant_a_agregar})")

                        if indice is not None:
                            nueva_cantidad = cant_existente + cant_a_agregar
                            print(
                                f"  - Bodega ({os.path.basename(archivo_bodega_path)}): {cant_existente} -> {nueva_cantidad}"
                            )
                            bodega[indice] = f"    {nombre.strip()} {nueva_cantidad}\n"
                        else:
                            print(
                                f"  - Item nuevo en Bodega. Cantidad inicial: {cant_a_agregar}"
                            )
                            bodega.append(f"    {nombre.strip()} {cant_a_agregar}\n")

            print("\n--- Consolidando bodega y guardando cambios ---")
            bodega_actualizada = eliminar_duplicados_bodega(bodega)
            escribir_archivo(archivo_bodega_path, bodega_actualizada)
            print("\n¡Compra agregada y bodega actualizada correctamente!")
            messagebox.showinfo(
                "Proceso Completado",
                "La compra se ha registrado en la bodega exitosamente.",
            )

        except Exception as e:
            print(f"\n--- Ocurrió un error inesperado ---")
            print(str(e))
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")
        finally:
            sys.stdout = sys.__stdout__

    def listar_items_cero(self):
        """Lee los archivos de inventario y lista los items con cantidad 0 en una nueva ventana."""
        archivo_origen_path = self.origen_file_entry.get()
        archivo_destino_path = self.destino_file_entry.get()

        if not archivo_origen_path or not archivo_destino_path:
            messagebox.showwarning(
                "Faltan Datos", "Por favor, especifique los archivos de Bodega y Local."
            )
            return

        items_cero_origen = []
        lineas_origen = leer_archivo(archivo_origen_path)
        if lineas_origen is not None:
            for linea in lineas_origen:
                nombre, cantidad = procesar_item_bodega(linea)
                if cantidad == 0:
                    items_cero_origen.append(nombre)

        items_cero_destino = []
        lineas_destino = leer_archivo(archivo_destino_path)
        if lineas_destino is not None:
            for linea in lineas_destino:
                nombre, cantidad = procesar_item_bodega(linea)
                if cantidad == 0:
                    items_cero_destino.append(nombre)

        if not items_cero_origen and not items_cero_destino:
            messagebox.showinfo(
                "Resultado",
                "No se encontraron items con stock 0 en los archivos especificados.",
            )
            return

        top = tk.Toplevel(self.root)
        top.title("Items con Stock Cero")
        top.geometry("450x350")
        top.transient(self.root)
        top.grab_set()

        text_area = scrolledtext.ScrolledText(
            top, wrap=tk.WORD, font=("Courier New", 9)
        )
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        resultado_texto = ""
        if items_cero_origen:
            resultado_texto += f"--- {os.path.basename(archivo_origen_path)} ---\n"
            for item in sorted(items_cero_origen):
                resultado_texto += f"- {item}\n"
            resultado_texto += "\n"

        if items_cero_destino:
            resultado_texto += f"--- {os.path.basename(archivo_destino_path)} ---\n"
            for item in sorted(items_cero_destino):
                resultado_texto += f"- {item}\n"

        text_area.insert(tk.INSERT, resultado_texto)
        text_area.config(state="disabled")

    def write(self, text):
        self.log_message(text)

    def flush(self):
        pass


# --- FIN: Clase de la Interfaz Gráfica ---

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
