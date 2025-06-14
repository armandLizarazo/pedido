import os
import sys
import platform
import re
import csv
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ==============================================================================
# 1. CLASE GestorInventario
# ==============================================================================
class GestorInventario:
    def __init__(self, archivo_inventario=None):
        self.archivo_inventario = archivo_inventario or "bodegac.txt"
        self.archivo_ventas = "registro_ventas.csv"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f: pass
        if not os.path.exists(self.archivo_ventas):
            with open(self.archivo_ventas, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Descripcion', 'Cantidad', 'CostoUnitario', 'PrecioUnitario', 'TotalVenta', 'Ganancia', 'ArchivoOrigen'])

    def registrar_venta(self, linea_num, descripcion, stock_actual, cantidad_vendida, costo, precio_venta):
        try:
            cantidad_vendida_int = int(cantidad_vendida)
            if cantidad_vendida_int <= 0: return False, "La cantidad debe ser positiva."
            if cantidad_vendida_int > int(stock_actual): return False, "No hay stock suficiente."
            
            success, msg = self.modificar_cantidad(linea_num, -cantidad_vendida_int)
            if not success: return False, f"Error al actualizar stock: {msg}"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_venta = cantidad_vendida_int * float(precio_venta)
            ganancia = (float(precio_venta) - float(costo)) * cantidad_vendida_int
            archivo_origen = os.path.basename(self.archivo_inventario)
            venta_data = [timestamp, descripcion, cantidad_vendida, f"{float(costo):.2f}", f"{float(precio_venta):.2f}", f"{total_venta:.2f}", f"{ganancia:.2f}", archivo_origen]
            
            with open(self.archivo_ventas, 'a', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(venta_data)
            return True, "Venta registrada con éxito."
        except ValueError: return False, "Cantidad, costo y precio deben ser números."
        except Exception as e: return False, f"Error al registrar venta: {e}"

    def cambiar_archivo(self, nuevo_archivo):
        self.archivo_inventario = nuevo_archivo
        self.crear_archivos_si_no_existen()
        return f"Archivo de inventario cambiado a: {self.archivo_inventario}"

    def leer_datos(self):
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            datos, errores = [], []
            for i, linea in enumerate(lineas, 1):
                partes = linea.strip().rsplit(' ', 1)
                if len(partes) == 2:
                    descripcion, cantidad_str = partes
                    try:
                        datos.append((i, descripcion.strip(), int(cantidad_str)))
                    except ValueError:
                        errores.append(f"Línea {i}: Cantidad no es un número.")
                elif linea.strip():
                    errores.append(f"Línea {i}: Formato incorrecto.")
            return datos, errores
        except Exception as e:
            return [], [f"Error al leer: {e}"]

    def agregar_linea(self, descripcion, cantidad):
        try:
            with open(self.archivo_inventario, 'a', encoding='utf-8') as f:
                f.write(f"    {descripcion} {int(cantidad)}\n")
            return True, "Ítem agregado."
        except ValueError: return False, "Cantidad debe ser un número."
        except Exception as e: return False, f"Error: {e}"

    def modificar_linea(self, num_linea, desc, cant):
        try:
            lineas = self._leer_lineas_archivo()
            if 1 <= num_linea <= len(lineas):
                lineas[num_linea - 1] = f"    {desc} {int(cant)}\n"
                self._escribir_lineas_archivo(lineas)
                return True, "Ítem modificado."
            return False, "Número de línea fuera de rango."
        except ValueError: return False, "Cantidad debe ser un número."
        except Exception as e: return False, f"Error: {e}"

    def modificar_cantidad(self, num_linea, cambio):
        try:
            lineas = self._leer_lineas_archivo()
            if 1 <= num_linea <= len(lineas):
                partes = lineas[num_linea - 1].strip().rsplit(' ', 1)
                if len(partes) == 2:
                    desc, cant_str = partes
                    nueva_cant = int(cant_str) + int(cambio)
                    if nueva_cant < 0: return False, "Stock no puede ser negativo."
                    lineas[num_linea - 1] = f"    {desc.strip()} {nueva_cant}\n"
                    self._escribir_lineas_archivo(lineas)
                    return True, "Stock actualizado."
                return False, "Formato de línea inválido."
            return False, "Número de línea fuera de rango."
        except ValueError: return False, "Cantidad debe ser un número."
        except Exception as e: return False, f"Error: {e}"

    def eliminar_linea(self, num_linea):
        try:
            lineas = self._leer_lineas_archivo()
            if 1 <= num_linea <= len(lineas):
                linea_eliminada = lineas.pop(num_linea - 1)
                self._escribir_lineas_archivo(lineas)
                return True, f"Eliminado: {linea_eliminada.strip()}"
            return False, "Número de línea fuera de rango."
        except Exception as e: return False, f"Error: {e}"

    def ordenar_alfabeticamente(self):
        try:
            lineas = self._leer_lineas_archivo()
            lineas.sort(key=str.lower)
            self._escribir_lineas_archivo(lineas)
            return True, "Inventario ordenado alfabéticamente."
        except Exception as e: return False, f"Error al ordenar: {e}"

    def verificar_formato(self):
        errores = []
        for i, linea in enumerate(self._leer_lineas_archivo(), 1):
            if not linea.strip(): continue
            partes = linea.strip().rsplit(' ', 1)
            if len(partes) != 2 or not partes[1].isdigit():
                errores.append(f"Línea {i}: '{linea.strip()}'")
        return errores

    def leer_historial_ventas(self):
        try:
            with open(self.archivo_ventas, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                return list(reader)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer historial de ventas: {e}")
            return []
            
    def _leer_lineas_archivo(self):
        with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
            return f.readlines()
            
    def _escribir_lineas_archivo(self, lineas):
        with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
            f.writelines(lineas)

# ==============================================================================
# 2. CLASE InventarioGUI
# ==============================================================================
class InventarioGUI:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Inventario y Ventas v1.4")
        master.geometry("1100x700")
        self.style = ttk.Style(); self.style.theme_use("clam")
        self.gestor = GestorInventario()
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.inventario_tab = ttk.Frame(self.notebook, padding="10")
        self.ventas_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.inventario_tab, text='Gestión de Inventario')
        self.notebook.add(self.ventas_tab, text='Ventas y Análisis')
        self.crear_widgets_inventario()
        self.crear_widgets_ventas()
        self.populate_inventory_treeview()
        self.populate_sales_treeview()
        self.add_placeholder(None)

    def crear_widgets_inventario(self):
        top_frame = ttk.Frame(self.inventario_tab); top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        filter_frame = ttk.Frame(self.inventario_tab); filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        tree_frame = ttk.Frame(self.inventario_tab); tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        action_frame = ttk.Frame(self.inventario_tab); action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        self.lbl_archivo = ttk.Label(top_frame, text=f"Archivo: {self.gestor.archivo_inventario}"); self.lbl_archivo.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Cambiar Archivo", command=self.cambiar_archivo).pack(side=tk.LEFT, padx=5)
        self.status_label_inv = ttk.Label(top_frame, text="Listo.", anchor=tk.E); self.status_label_inv.pack(side=tk.RIGHT, padx=5)
        ttk.Label(filter_frame, text="Filtrar por palabra clave:").pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry = ttk.Entry(filter_frame, width=20); self.filtro_palabra_entry.pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry.bind("<FocusIn>", self.clear_placeholder); self.filtro_palabra_entry.bind("<FocusOut>", self.add_placeholder)
        ttk.Label(filter_frame, text="y por cantidad:").pack(side=tk.LEFT, padx=5)
        self.filtro_op_combo = ttk.Combobox(filter_frame, values=["", ">", "<", "="], width=3, state="readonly"); self.filtro_op_combo.pack(side=tk.LEFT, padx=5)
        self.filtro_cant_entry = ttk.Entry(filter_frame, width=10); self.filtro_cant_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Aplicar Filtro / Refrescar", command=self.populate_inventory_treeview).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="Limpiar", command=self.limpiar_filtros).pack(side=tk.LEFT, padx=5)
        self.inventory_tree = ttk.Treeview(tree_frame, columns=("Linea", "Item", "Cantidad"), show="headings")
        self.inventory_tree.heading("Linea", text="Línea"); self.inventory_tree.heading("Item", text="Item"); self.inventory_tree.heading("Cantidad", text="Cantidad en Stock")
        self.inventory_tree.column("Linea", width=60, anchor=tk.CENTER); self.inventory_tree.column("Item", width=500); self.inventory_tree.column("Cantidad", width=120, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set); self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        stock_group = ttk.LabelFrame(action_frame, text="Stock"); stock_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(stock_group, text="Sumar Unidades (+)", command=lambda: self.ajustar_cantidad(True)).pack(pady=2, padx=5)
        ttk.Button(stock_group, text="Restar Unidades (-)", command=lambda: self.ajustar_cantidad(False)).pack(pady=2, padx=5)
        item_group = ttk.LabelFrame(action_frame, text="Ítems"); item_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(item_group, text="Agregar Nuevo", command=self.agregar_item).pack(pady=2, padx=5)
        ttk.Button(item_group, text="Modificar Seleccionado", command=self.modificar_item).pack(pady=2, padx=5)
        ttk.Button(item_group, text="Eliminar Seleccionado", command=self.eliminar_item).pack(pady=2, padx=5)
        tools_group = ttk.LabelFrame(action_frame, text="Herramientas"); tools_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(tools_group, text="Ordenar Alfabéticamente", command=self.ordenar_alfabeticamente).pack(pady=2, padx=5)
        ttk.Button(tools_group, text="Verificar Formato", command=self.verificar_formato).pack(pady=2, padx=5)
        style_vender = ttk.Style(); style_vender.configure("Vender.TButton", foreground="white", background="navy", font=('Helvetica', 10, 'bold'))
        ttk.Button(action_frame, text="VENDER ITEM", command=self.iniciar_venta, style="Vender.TButton").pack(side=tk.RIGHT, padx=20, ipady=10, fill=tk.Y)

    def crear_widgets_ventas(self):
        filter_frame = ttk.LabelFrame(self.ventas_tab, text="Filtros de Búsqueda", padding="10"); filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        analisis_frame = ttk.LabelFrame(self.ventas_tab, text="Totales de la Vista Actual", padding="10"); analisis_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        historial_frame = ttk.Frame(self.ventas_tab); historial_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(filter_frame, text="Desde (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_fecha_desde = ttk.Entry(filter_frame); self.filtro_fecha_desde.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="Hasta (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_fecha_hasta = ttk.Entry(filter_frame); self.filtro_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="Descripción del Ítem:").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_desc_venta = ttk.Entry(filter_frame, width=30); self.filtro_desc_venta.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        btn_filtrar = ttk.Button(filter_frame, text="Filtrar Ventas", command=self.populate_sales_treeview); btn_filtrar.pack(side=tk.LEFT, padx=10, pady=5)
        btn_limpiar = ttk.Button(filter_frame, text="Mostrar Todo", command=self.limpiar_filtros_ventas); btn_limpiar.pack(side=tk.LEFT, padx=5, pady=5)
        self.lbl_total_items = ttk.Label(analisis_frame, text="Items Vendidos: 0", font=("Helvetica", 10, "bold")); self.lbl_total_items.pack(side=tk.LEFT, padx=20)
        self.lbl_costo_total = ttk.Label(analisis_frame, text="Costo Total: $0.00", font=("Helvetica", 10, "bold")); self.lbl_costo_total.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ventas = ttk.Label(analisis_frame, text="Total Ventas: $0.00", font=("Helvetica", 10, "bold")); self.lbl_total_ventas.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ganancia = ttk.Label(analisis_frame, text="Ganancia Total: $0.00", font=("Helvetica", 10, "bold")); self.lbl_total_ganancia.pack(side=tk.LEFT, padx=20)
        columnas = ("Timestamp", "Item", "Cantidad", "CostoU", "PrecioU", "Total", "Ganancia", "ArchivoOrigen")
        self.sales_tree = ttk.Treeview(historial_frame, columns=columnas, show="headings")
        self.sales_tree.heading("Timestamp", text="Fecha y Hora"); self.sales_tree.heading("Item", text="Item Vendido"); self.sales_tree.heading("Cantidad", text="Cant."); self.sales_tree.heading("CostoU", text="Costo Unit."); self.sales_tree.heading("PrecioU", text="Precio Unit."); self.sales_tree.heading("Total", text="Total Venta"); self.sales_tree.heading("Ganancia", text="Ganancia"); self.sales_tree.heading("ArchivoOrigen", text="Origen")
        for col in columnas: self.sales_tree.column(col, anchor=tk.W, width=100)
        self.sales_tree.column("Cantidad", anchor=tk.CENTER, width=60); self.sales_tree.column("Timestamp", width=140); self.sales_tree.column("Item", width=250); self.sales_tree.column("ArchivoOrigen", width=120, anchor=tk.CENTER)
        scrollbar_s = ttk.Scrollbar(historial_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar_s.set); self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)

    def populate_inventory_treeview(self):
        for i in self.inventory_tree.get_children(): self.inventory_tree.delete(i)
        datos, errores = self.gestor.leer_datos()
        if errores: messagebox.showwarning("Aviso", "\n".join(errores))
        palabra_clave = self.filtro_palabra_entry.get(); operador = self.filtro_op_combo.get(); cant_str = self.filtro_cant_entry.get()
        if palabra_clave == "Palabra clave...": palabra_clave = ""
        cant_filtro = None
        if operador and cant_str:
            try: cant_filtro = int(cant_str)
            except ValueError: messagebox.showerror("Error", "Cantidad de filtro debe ser un número."); return
        count = 0
        for linea_num, desc, cant in datos:
            mostrar = True
            if palabra_clave and palabra_clave.lower() not in desc.lower(): mostrar = False
            if mostrar and cant_filtro is not None:
                if (operador == ">" and not cant > cant_filtro) or (operador == "<" and not cant < cant_filtro) or (operador == "=" and not cant == cant_filtro): mostrar = False
            if mostrar: self.inventory_tree.insert("", tk.END, values=(linea_num, desc, cant)); count += 1
        self.status_label_inv.config(text=f"Mostrando {count} de {len(datos)} ítems.")

    def populate_sales_treeview(self):
        for i in self.sales_tree.get_children(): self.sales_tree.delete(i)
        
        historial = self.gestor.leer_historial_ventas()
        
        desde_str = self.filtro_fecha_desde.get()
        hasta_str = self.filtro_fecha_hasta.get()
        desc_str = self.filtro_desc_venta.get().lower()

        total_items_vendidos, costo_total_vista, total_ventas, total_ganancia = 0, 0.0, 0.0, 0.0

        for venta in historial:
            if len(venta) < 7: continue

            # --- Filtro de Fecha ---
            fecha_valida = True
            if desde_str or hasta_str:
                try:
                    fecha_venta = datetime.strptime(venta[0], "%Y-%m-%d %H:%M:%S")
                    if desde_str and fecha_venta < datetime.strptime(desde_str, "%Y-%m-%d"):
                        fecha_valida = False
                    if hasta_str and fecha_venta > (datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)):
                        fecha_valida = False
                except ValueError:
                    fecha_valida = False 
            if not fecha_valida: continue

            # --- Filtro de Descripción ---
            if desc_str and desc_str not in venta[1].lower():
                continue

            # --- Si pasa los filtros, se procesa y se muestra ---
            try:
                cantidad = int(venta[2])
                costo_unitario = float(venta[3])
                total_venta_actual = float(venta[5])
                ganancia_actual = float(venta[6])

                total_items_vendidos += cantidad
                costo_total_vista += cantidad * costo_unitario
                total_ventas += total_venta_actual
                total_ganancia += ganancia_actual

                origen = venta[7] if len(venta) > 7 else "N/A"
                self.sales_tree.insert("", tk.END, values=(venta[:7] + [origen]))

            except (ValueError, IndexError) as e:
                print(f"ADVERTENCIA: Se omitió la fila de venta por datos inválidos: {venta}, Error: {e}")
                continue
        
        self.lbl_total_items.config(text=f"Items Vendidos: {total_items_vendidos}")
        self.lbl_costo_total.config(text=f"Costo Total: ${costo_total_vista:.2f}")
        self.lbl_total_ventas.config(text=f"Total Ventas: ${total_ventas:.2f}")
        self.lbl_total_ganancia.config(text=f"Ganancia Total: ${total_ganancia:.2f}")


    def limpiar_filtros(self):
        self.filtro_palabra_entry.delete(0, tk.END); self.add_placeholder(None)
        self.filtro_op_combo.set(""); self.filtro_cant_entry.delete(0, tk.END)
        self.populate_inventory_treeview()
        
    def limpiar_filtros_ventas(self):
        self.filtro_fecha_desde.delete(0, tk.END)
        self.filtro_fecha_hasta.delete(0, tk.END)
        self.filtro_desc_venta.delete(0, tk.END)
        self.populate_sales_treeview()

    def _get_selected_item_values(self):
        selected = self.inventory_tree.focus()
        if not selected: messagebox.showwarning("Sin Selección", "Por favor, seleccione un ítem de la lista."); return None
        return self.inventory_tree.item(selected, 'values')

    def agregar_item(self):
        win_add = tk.Toplevel(self.master); win_add.title("Agregar Nuevo Ítem"); win_add.grab_set(); win_add.resizable(False, False)
        frame = ttk.Frame(win_add, padding="10"); frame.pack()
        ttk.Label(frame, text="Descripción:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        desc_entry = ttk.Entry(frame, width=40); desc_entry.grid(row=0, column=1, pady=2, padx=5)
        ttk.Label(frame, text="Cantidad Inicial:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        cant_entry = ttk.Entry(frame, width=15); cant_entry.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        def do_add():
            desc = desc_entry.get().strip(); cant = cant_entry.get().strip()
            if not desc or not cant: messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=win_add); return
            success, message = self.gestor.agregar_linea(desc, cant)
            if success: self.populate_inventory_treeview(); win_add.destroy(); messagebox.showinfo("Éxito", message)
            else: messagebox.showerror("Error", message, parent=win_add)
        btn_frame = ttk.Frame(frame); btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Guardar Ítem", command=do_add).pack(); desc_entry.focus_set()

    def modificar_item(self):
        values = self._get_selected_item_values()
        if not values: return
        linea, desc, cant = values
        win_mod = tk.Toplevel(self.master); win_mod.title("Modificar Ítem"); win_mod.grab_set(); win_mod.resizable(False, False)
        frame = ttk.Frame(win_mod, padding="10"); frame.pack()
        ttk.Label(frame, text="Descripción:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        desc_entry = ttk.Entry(frame, width=40); desc_entry.grid(row=0, column=1, pady=2, padx=5); desc_entry.insert(0, desc)
        ttk.Label(frame, text="Cantidad:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        cant_entry = ttk.Entry(frame, width=15); cant_entry.grid(row=1, column=1, sticky="w", pady=2, padx=5); cant_entry.insert(0, cant)
        def do_mod():
            nueva_desc = desc_entry.get().strip(); nueva_cant = cant_entry.get().strip()
            if not nueva_desc or not nueva_cant: messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=win_mod); return
            success, message = self.gestor.modificar_linea(int(linea), nueva_desc, nueva_cant)
            if success: self.populate_inventory_treeview(); win_mod.destroy(); messagebox.showinfo("Éxito", message)
            else: messagebox.showerror("Error", message, parent=win_mod)
        btn_frame = ttk.Frame(frame); btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Guardar Cambios", command=do_mod).pack(); desc_entry.focus_set()

    def eliminar_item(self):
        values = self._get_selected_item_values()
        if not values: return
        linea, desc, cant = values
        if messagebox.askyesno("Confirmar", f"¿Eliminar este ítem?\n\n{desc}"):
            success, msg = self.gestor.eliminar_linea(int(linea))
            if success: self.populate_inventory_treeview(); messagebox.showinfo("Éxito", msg)
            else: messagebox.showerror("Error", msg)

    def ajustar_cantidad(self, sumar):
        values = self._get_selected_item_values()
        if not values: return
        linea, desc, _ = values
        accion = "sumar" if sumar else "restar"
        try:
            cambio = simpledialog.askinteger("Ajustar Stock", f"Cantidad a {accion} para:\n{desc}", parent=self.master, minvalue=1)
            if cambio is not None:
                cambio_final = cambio if sumar else -cambio
                success, msg = self.gestor.modificar_cantidad(int(linea), cambio_final)
                if success: self.populate_inventory_treeview()
                else: messagebox.showerror("Error", msg)
        except ValueError: messagebox.showerror("Error", "Debe ser un número.")

# --- AÑADE ESTA FUNCIÓN DENTRO DE LA CLASE InventarioGUI ---

    def ordenar_alfabeticamente(self):
        if messagebox.askyesno("Confirmar", "¿Desea ordenar el inventario alfabéticamente?"):
            success, msg = self.gestor.ordenar_alfabeticamente()
            if success:
                self.populate_inventory_treeview()
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)


    def ordenar_inventario(self):
        if messagebox.askyesno("Confirmar", "Ordenar el inventario alfabéticamente?"):
            success, msg = self.gestor.ordenar_alfabeticamente()
            if success: self.populate_inventory_treeview(); messagebox.showinfo("Éxito", msg)
            else: messagebox.showerror("Error", msg)

    def verificar_formato(self):
        errores = self.gestor.verificar_formato()
        if not errores: messagebox.showinfo("Verificación", "¡El formato de todas las líneas es correcto!")
        else: messagebox.showwarning("Verificación", "Líneas con formato incorrecto:\n\n" + "\n".join(errores))

    def iniciar_venta(self):
        values = self._get_selected_item_values()
        if not values: return
        linea_num, desc, stock_actual = values
        win_vender = tk.Toplevel(self.master); win_vender.title("Registrar Venta"); win_vender.grab_set(); win_vender.resizable(False, False)
        frame = ttk.Frame(win_vender, padding="15"); frame.pack()
        ttk.Label(frame, text=f"Item: {desc}", font=("Helvetica", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(frame, text=f"Stock Actual: {stock_actual}").grid(row=1, column=0, columnspan=2, pady=(0, 15))
        ttk.Label(frame, text="Cantidad a Vender:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        cant_entry = ttk.Entry(frame, width=15); cant_entry.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(frame, text="Costo Unitario ($):").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        costo_entry = ttk.Entry(frame, width=15); costo_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(frame, text="Precio de Venta ($):").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        precio_entry = ttk.Entry(frame, width=15); precio_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        def do_vender():
            cant = cant_entry.get(); costo = costo_entry.get(); precio = precio_entry.get()
            if not all([cant, costo, precio]): messagebox.showerror("Error de Validación", "Todos los campos son obligatorios.", parent=win_vender); return
            success, message = self.gestor.registrar_venta(int(linea_num), desc, stock_actual, cant, costo, precio)
            if success:
                win_vender.destroy(); messagebox.showinfo("Venta Exitosa", message)
                self.populate_inventory_treeview(); self.populate_sales_treeview()
                self.notebook.select(self.ventas_tab)
            else: messagebox.showerror("Error en la Venta", message, parent=win_vender)
        btn_confirmar = ttk.Button(frame, text="Confirmar Venta", command=do_vender, style="Vender.TButton"); btn_confirmar.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        cant_entry.focus_set()

    def cambiar_archivo(self):
        nuevo_archivo = filedialog.askopenfilename(title="Seleccionar nuevo archivo de inventario", filetypes=(("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")))
        if nuevo_archivo:
            mensaje = self.gestor.cambiar_archivo(nuevo_archivo)
            self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")
            self.populate_inventory_treeview()
            messagebox.showinfo("Éxito", mensaje)
            
    def clear_placeholder(self, event):
        if self.filtro_palabra_entry.get() == "Palabra clave...": self.filtro_palabra_entry.delete(0, tk.END); self.filtro_palabra_entry.config(foreground='black')
        
    def add_placeholder(self, event):
        if not self.filtro_palabra_entry.get(): self.filtro_palabra_entry.insert(0, "Palabra clave..."); self.filtro_palabra_entry.config(foreground='grey')

# ==============================================================================
# 3. BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()