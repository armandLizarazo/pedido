import os
import sys
import platform
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ==============================================================================
# AQUÍ VA TU CÓDIGO ORIGINAL (CLASE GestorInventario)
# He hecho algunos ajustes menores para que funcione mejor con la GUI
# (principalmente, devolver datos en lugar de solo imprimir)
# ==============================================================================

class GestorInventario:
    def __init__(self, archivo_inventario=None):
        self.archivo_inventario = archivo_inventario or "bodegac.txt"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                pass

    def cambiar_archivo(self, nuevo_archivo):
        self.archivo_inventario = nuevo_archivo
        self.crear_archivos_si_no_existen()
        return f"Archivo cambiado a: {self.archivo_inventario}"

    def leer_datos(self):
        """Lee los datos del archivo y los devuelve como lista de tuplas."""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            datos = []
            errores = []
            for i, linea in enumerate(lineas, 1):
                linea_strip = linea.strip()
                partes = linea_strip.rsplit(' ', 1)
                
                if len(partes) == 2:
                    descripcion, cantidad_str = partes
                    try:
                        cantidad = int(cantidad_str)
                        # Usamos la línea original para mantener espacios iniciales si los hay
                        # pero para la GUI, a menudo es mejor tener datos limpios.
                        # Aquí, extraemos la descripción limpia.
                        descripcion_limpia = linea.strip().rsplit(' ', 1)[0].strip()
                        datos.append((i, descripcion_limpia, cantidad))
                    except ValueError:
                        errores.append(f"Línea {i}: Cantidad no es número ({linea_strip})")
                elif linea_strip: # Ignorar líneas vacías pero reportar otras inválidas
                    errores.append(f"Línea {i}: Formato incorrecto ({linea_strip})")
            return datos, errores
        except FileNotFoundError:
            return [], [f"Error: No se encontró el archivo {self.archivo_inventario}"]
        except UnicodeDecodeError:
            return [], [f"Error: No se pudo leer el archivo {self.archivo_inventario}. Problema de codificación."]
        except Exception as e:
            return [], [f"Error inesperado al leer: {e}"]

    def agregar_linea(self, descripcion, cantidad):
        try:
            cantidad_int = int(cantidad)
            with open(self.archivo_inventario, 'a', encoding='utf-8') as f:
                # Mantenemos el formato de 4 espacios
                f.write(f"    {descripcion} {cantidad_int}\n")
            return True, "Línea agregada correctamente."
        except ValueError:
            return False, "Error: La cantidad debe ser un número válido."
        except Exception as e:
            return False, f"Error al agregar: {e}"

    def modificar_linea(self, numero_linea, nueva_descripcion, nueva_cantidad):
        try:
            nueva_cantidad_int = int(nueva_cantidad)
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                lineas[numero_linea - 1] = f"    {nueva_descripcion} {nueva_cantidad_int}\n"
                with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                    f.writelines(lineas)
                return True, "Línea modificada correctamente."
            else:
                return False, "Error: Número de línea fuera de rango."
        except ValueError:
            return False, "Error: La cantidad debe ser un número válido."
        except Exception as e:
            return False, f"Error al modificar: {e}"

    def modificar_cantidad(self, numero_linea, cambio_cantidad):
        try:
            cambio_cantidad_int = int(cambio_cantidad)
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                linea = lineas[numero_linea - 1].strip()
                partes = linea.rsplit(' ', 1)
                
                if len(partes) == 2:
                    descripcion, cantidad_str = partes
                    try:
                        cantidad_actual = int(cantidad_str)
                        nueva_cantidad = cantidad_actual + cambio_cantidad_int
                        if nueva_cantidad < 0:
                            return False, "Error: La cantidad no puede ser negativa."
                        
                        # Reconstruimos la descripción original (todo menos la cantidad)
                        descripcion_original = linea.rsplit(' ', 1)[0]
                        lineas[numero_linea - 1] = f"    {descripcion_original.strip()} {nueva_cantidad}\n"
                        
                        with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                            f.writelines(lineas)
                        return True, "Cantidad modificada correctamente."
                    except ValueError:
                        return False, "Error: Cantidad inválida en el archivo."
                else:
                    return False, "Error: Formato de línea inválido."
            else:
                return False, "Error: Número de línea fuera de rango."
        except ValueError:
            return False, "Error: La cantidad debe ser un número válido."
        except Exception as e:
            return False, f"Error al modificar cantidad: {e}"

    def eliminar_linea(self, numero_linea):
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if 1 <= numero_linea <= len(lineas):
                linea_eliminada = lineas.pop(numero_linea - 1).strip()
                with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                    f.writelines(lineas)
                return True, f"Línea eliminada: {linea_eliminada}"
            else:
                return False, "Error: Número de línea fuera de rango."
        except Exception as e:
            return False, f"Error al eliminar: {e}"

    def verificar_formato(self):
        """Devuelve una lista de errores de formato."""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            lineas_invalidas = []
            for i, linea in enumerate(lineas, 1):
                linea_original = linea.rstrip('\n').rstrip('\r') # Guardar original sin salto
                
                # Ignorar líneas completamente vacías
                if not linea.strip():
                    continue

                if not linea.startswith("    "):
                    lineas_invalidas.append(f"Línea {i}: No empieza con 4 espacios -> '{linea_original}'")
                
                partes = linea.strip().rsplit(' ', 1)
                if len(partes) != 2:
                     lineas_invalidas.append(f"Línea {i}: Formato incorrecto (espacio + número al final) -> '{linea_original}'")
                elif not partes[1].isdigit():
                     lineas_invalidas.append(f"Línea {i}: No termina con un número -> '{linea_original}'")

            return lineas_invalidas
        except Exception as e:
            return [f"Error al verificar formato: {e}"]

    def ordenar_alfabeticamente(self):
        """Ordena alfabéticamente las líneas del archivo."""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if not lineas:
                return True, "El archivo está vacío, no hay nada que ordenar."

            # Separar líneas válidas e inválidas para ordenar solo las válidas
            validas = []
            invalidas = []
            for linea in lineas:
                if linea.strip().rsplit(' ', 1)[-1].isdigit() and linea.startswith("    "):
                     validas.append(linea)
                else:
                     invalidas.append(linea)

            validas.sort(key=lambda linea: linea.strip().lower())
            
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                f.writelines(validas + invalidas) # Poner inválidas al final
            
            return True, "Archivo ordenado alfabéticamente (líneas inválidas movidas al final)."
        except Exception as e:
            return False, f"Error al ordenar: {e}"

# ==============================================================================
# AQUÍ COMIENZA EL CÓDIGO DE LA INTERFAZ GRÁFICA (GUI)
# ==============================================================================

class InventarioGUI:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Inventario Profesional")
        master.geometry("800x600")

        # Configurar estilo ttk para un look más moderno
        self.style = ttk.Style()
        self.style.theme_use("clam") # Puedes probar 'alt', 'default', 'classic', 'clam'

        # Inicializar el gestor de inventario
        self.gestor = GestorInventario()

        # --- Frames ---
        self.top_frame = ttk.Frame(master, padding="10")
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.filter_frame = ttk.Frame(master, padding="10")
        self.filter_frame.pack(side=tk.TOP, fill=tk.X)

        self.tree_frame = ttk.Frame(master, padding="10")
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.action_frame = ttk.Frame(master, padding="10")
        self.action_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.status_frame = ttk.Frame(master, padding="5", relief="sunken")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Top Frame (Archivo) ---
        self.lbl_archivo = ttk.Label(self.top_frame, text=f"Archivo: {self.gestor.archivo_inventario}")
        self.lbl_archivo.pack(side=tk.LEFT, padx=5)
        self.btn_cambiar_archivo = ttk.Button(self.top_frame, text="Cambiar Archivo", command=self.cambiar_archivo)
        self.btn_cambiar_archivo.pack(side=tk.LEFT, padx=5)

        # --- Filter Frame ---
        ttk.Label(self.filter_frame, text="Filtrar:").pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry = ttk.Entry(self.filter_frame, width=20)
        self.filtro_palabra_entry.pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry.insert(0, "Palabra clave...")
        self.filtro_palabra_entry.bind("<FocusIn>", self.clear_placeholder)
        self.filtro_palabra_entry.bind("<FocusOut>", self.add_placeholder)

        self.filtro_op_combo = ttk.Combobox(self.filter_frame, values=["", ">", "<", "="], width=3, state="readonly")
        self.filtro_op_combo.pack(side=tk.LEFT, padx=5)
        self.filtro_op_combo.set("")

        self.filtro_cant_entry = ttk.Entry(self.filter_frame, width=10)
        self.filtro_cant_entry.pack(side=tk.LEFT, padx=5)
        
        self.btn_filtrar = ttk.Button(self.filter_frame, text="Aplicar Filtro / Refrescar", command=self.populate_treeview)
        self.btn_filtrar.pack(side=tk.LEFT, padx=10)
        
        self.btn_limpiar_filtro = ttk.Button(self.filter_frame, text="Limpiar", command=self.limpiar_filtros)
        self.btn_limpiar_filtro.pack(side=tk.LEFT, padx=5)

        # --- Treeview Frame (Tabla de Inventario) ---
        self.tree = ttk.Treeview(self.tree_frame, columns=("Linea", "Item", "Cantidad"), show="headings")
        self.tree.heading("Linea", text="Línea")
        self.tree.heading("Item", text="Item")
        self.tree.heading("Cantidad", text="Cantidad")

        self.tree.column("Linea", width=50, anchor=tk.CENTER)
        self.tree.column("Item", width=400)
        self.tree.column("Cantidad", width=100, anchor=tk.E)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Action Frame (Botones) ---
        btn_width = 25
        self.btn_agregar = ttk.Button(self.action_frame, text="Agregar Item", command=self.agregar_item, width=btn_width)
        self.btn_agregar.pack(pady=5, fill=tk.X)

        self.btn_modificar = ttk.Button(self.action_frame, text="Modificar Item Seleccionado", command=self.modificar_item, width=btn_width)
        self.btn_modificar.pack(pady=5, fill=tk.X)

        self.btn_sumar = ttk.Button(self.action_frame, text="Sumar Unidades (+)", command=lambda: self.ajustar_cantidad(True), width=btn_width)
        self.btn_sumar.pack(pady=5, fill=tk.X)

        self.btn_restar = ttk.Button(self.action_frame, text="Restar Unidades (-)", command=lambda: self.ajustar_cantidad(False), width=btn_width)
        self.btn_restar.pack(pady=5, fill=tk.X)
        
        self.btn_eliminar = ttk.Button(self.action_frame, text="Eliminar Item Seleccionado", command=self.eliminar_item, width=btn_width)
        self.btn_eliminar.pack(pady=5, fill=tk.X)

        self.btn_ordenar = ttk.Button(self.action_frame, text="Ordenar Alfabéticamente", command=self.ordenar_inventario, width=btn_width)
        self.btn_ordenar.pack(pady=15, fill=tk.X)

        self.btn_verificar = ttk.Button(self.action_frame, text="Verificar Formato", command=self.verificar_formato, width=btn_width)
        self.btn_verificar.pack(pady=5, fill=tk.X)
        
        self.btn_salir = ttk.Button(self.action_frame, text="Salir", command=master.quit, width=btn_width)
        self.btn_salir.pack(side=tk.BOTTOM, pady=20)


        # --- Status Bar ---
        self.status_label = ttk.Label(self.status_frame, text="Listo.", anchor=tk.W)
        self.status_label.pack(fill=tk.X)

        # --- Carga Inicial ---
        self.populate_treeview()

    # --- Funciones de Placeholder para Entry ---
    def clear_placeholder(self, event):
        if self.filtro_palabra_entry.get() == "Palabra clave...":
            self.filtro_palabra_entry.delete(0, tk.END)
            self.filtro_palabra_entry.config(foreground='black')

    def add_placeholder(self, event):
        if not self.filtro_palabra_entry.get():
            self.filtro_palabra_entry.insert(0, "Palabra clave...")
            self.filtro_palabra_entry.config(foreground='grey')

    # --- Funciones de la GUI ---
    def update_status(self, message):
        self.status_label.config(text=message)

    def populate_treeview(self):
        # Limpiar Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Leer datos
        datos, errores = self.gestor.leer_datos()

        if errores:
            messagebox.showwarning("Errores al Leer", "\n".join(errores))

        # Aplicar filtros
        palabra_clave = self.filtro_palabra_entry.get()
        if palabra_clave == "Palabra clave...":
            palabra_clave = ""
            
        operador = self.filtro_op_combo.get()
        cantidad_filtro_str = self.filtro_cant_entry.get()
        
        cantidad_filtro = None
        if cantidad_filtro_str and operador:
            try:
                cantidad_filtro = int(cantidad_filtro_str)
            except ValueError:
                messagebox.showerror("Error de Filtro", "La cantidad de filtro debe ser un número.")
                self.update_status("Error: Cantidad de filtro inválida.")
                return

        # Poblar Treeview
        total_items = 0
        suma_cantidades = 0
        for linea_num, desc, cant in datos:
            mostrar = True # Mostrar por defecto

            # Filtrar por palabra clave
            if palabra_clave and palabra_clave.lower() not in desc.lower():
                mostrar = False

            # Filtrar por cantidad
            if mostrar and cantidad_filtro is not None and operador:
                if operador == ">" and not cant > cantidad_filtro:
                    mostrar = False
                elif operador == "<" and not cant < cantidad_filtro:
                    mostrar = False
                elif operador == "=" and not cant == cantidad_filtro:
                    mostrar = False
            
            if mostrar:
                self.tree.insert("", tk.END, values=(linea_num, desc, cant))
                total_items += 1
                suma_cantidades += cant

        self.update_status(f"Mostrando {total_items} items. Suma cantidades: {suma_cantidades}. Archivo: {self.gestor.archivo_inventario}")

    def limpiar_filtros(self):
        self.filtro_palabra_entry.delete(0, tk.END)
        self.add_placeholder(None) # Poner placeholder de nuevo
        self.filtro_op_combo.set("")
        self.filtro_cant_entry.delete(0, tk.END)
        self.populate_treeview()


    def cambiar_archivo(self):
        nuevo_archivo = filedialog.askopenfilename(
            title="Seleccionar Archivo de Inventario",
            filetypes=(("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*"))
        )
        if nuevo_archivo:
            mensaje = self.gestor.cambiar_archivo(nuevo_archivo)
            self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")
            self.populate_treeview()
            messagebox.showinfo("Archivo Cambiado", mensaje)

    def agregar_item(self):
        # Usar Toplevel para una ventana emergente más controlada
        win_add = tk.Toplevel(self.master)
        win_add.title("Agregar Nuevo Item")
        win_add.geometry("350x150")
        win_add.transient(self.master) # Mantenerla sobre la principal
        win_add.grab_set() # Bloquear la principal hasta cerrar

        ttk.Label(win_add, text="Descripción:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        desc_entry = ttk.Entry(win_add, width=40)
        desc_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(win_add, text="Cantidad:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        cant_entry = ttk.Entry(win_add, width=15)
        cant_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        def do_add():
            desc = desc_entry.get().strip()
            cant = cant_entry.get().strip()
            if not desc or not cant:
                messagebox.showwarning("Entrada Incompleta", "Debe ingresar descripción y cantidad.", parent=win_add)
                return

            success, message = self.gestor.agregar_linea(desc, cant)
            if success:
                messagebox.showinfo("Éxito", message, parent=win_add)
                self.populate_treeview()
                win_add.destroy()
            else:
                messagebox.showerror("Error", message, parent=win_add)

        btn_frame = ttk.Frame(win_add)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Agregar", command=do_add).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=win_add.destroy).pack(side=tk.LEFT, padx=10)
        
        desc_entry.focus_set()


    def get_selected_item(self):
        """Obtiene el item seleccionado en el Treeview."""
        selected = self.tree.focus() # Obtiene el ID del item seleccionado
        if not selected:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un item de la lista.")
            return None
        return self.tree.item(selected, 'values') # Retorna la tupla de valores

    def modificar_item(self):
        selected_values = self.get_selected_item()
        if not selected_values:
            return

        linea_num, desc_actual, cant_actual = selected_values

        win_mod = tk.Toplevel(self.master)
        win_mod.title("Modificar Item")
        win_mod.geometry("350x150")
        win_mod.transient(self.master)
        win_mod.grab_set()

        ttk.Label(win_mod, text=f"Línea {linea_num}:").grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        ttk.Label(win_mod, text="Descripción:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        desc_entry = ttk.Entry(win_mod, width=40)
        desc_entry.grid(row=1, column=1, padx=10, pady=5)
        desc_entry.insert(0, desc_actual)

        ttk.Label(win_mod, text="Cantidad:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        cant_entry = ttk.Entry(win_mod, width=15)
        cant_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        cant_entry.insert(0, cant_actual)

        def do_mod():
            nueva_desc = desc_entry.get().strip()
            nueva_cant = cant_entry.get().strip()
            if not nueva_desc or not nueva_cant:
                messagebox.showwarning("Entrada Incompleta", "Debe ingresar descripción y cantidad.", parent=win_mod)
                return

            success, message = self.gestor.modificar_linea(int(linea_num), nueva_desc, nueva_cant)
            if success:
                messagebox.showinfo("Éxito", message, parent=win_mod)
                self.populate_treeview()
                win_mod.destroy()
            else:
                messagebox.showerror("Error", message, parent=win_mod)

        btn_frame = ttk.Frame(win_mod)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Guardar Cambios", command=do_mod).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancelar", command=win_mod.destroy).pack(side=tk.LEFT, padx=10)
        
        desc_entry.focus_set()


    def ajustar_cantidad(self, sumar=True):
        selected_values = self.get_selected_item()
        if not selected_values:
            return

        linea_num, desc, _ = selected_values
        accion = "sumar" if sumar else "restar"
        signo = 1 if sumar else -1

        try:
            cambio = simpledialog.askinteger(
                f"Ajustar Cantidad",
                f"Ingrese la cantidad a {accion} para '{desc}':",
                parent=self.master,
                minvalue=1 # Siempre pedir un número positivo
            )
            if cambio is not None:
                success, message = self.gestor.modificar_cantidad(int(linea_num), cambio * signo)
                if success:
                    self.populate_treeview()
                    self.update_status(message)
                else:
                    messagebox.showerror("Error", message)
        except ValueError:
             messagebox.showerror("Error", "Debe ingresar un número entero válido.")

    def eliminar_item(self):
        selected_values = self.get_selected_item()
        if not selected_values:
            return

        linea_num, desc, cant = selected_values

        if messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de que desea eliminar la línea {linea_num}:\n'{desc} {cant}'?"):
            success, message = self.gestor.eliminar_linea(int(linea_num))
            if success:
                messagebox.showinfo("Éxito", message)
                self.populate_treeview()
            else:
                messagebox.showerror("Error", message)

    def ordenar_inventario(self):
        if messagebox.askyesno("Confirmar Ordenar", "¿Está seguro de que desea ordenar el archivo alfabéticamente?\n(Las líneas con formato incorrecto podrían moverse al final)"):
            success, message = self.gestor.ordenar_alfabeticamente()
            if success:
                messagebox.showinfo("Éxito", message)
                self.populate_treeview()
            else:
                messagebox.showerror("Error", message)

    def verificar_formato(self):
        errores = self.gestor.verificar_formato()
        if not errores:
            messagebox.showinfo("Verificación de Formato", "¡El formato del archivo es correcto!")
            self.update_status("Formato verificado: OK.")
        else:
            mensaje_error = "Se encontraron los siguientes problemas de formato:\n\n" + "\n".join(errores)
            mensaje_error += "\n\nUse 'Modificar Item' para corregir las líneas afectadas."
            messagebox.showwarning("Verificación de Formato", mensaje_error)
            self.update_status(f"Formato verificado: {len(errores)} errores encontrados.")


# --- Función Principal ---
def main_gui():
    # Intentar configurar la consola para latin-1 solo en Windows (menos relevante para GUI, pero mantenido por si acaso)
    if platform.system() == "Windows":
        try:
            os.system("chcp 1252 > nul")
        except:
            pass
            
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui()