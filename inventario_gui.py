import os
import sys
import platform
import re
import csv
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import subprocess
import hashlib

# --- PARCHE DE COMPATIBILIDAD para hashlib en versiones antiguas de Python ---
# Soluciona el error "'usedforsecurity' is an invalid keyword argument" al generar PDFs.
try:
    hashlib.md5(usedforsecurity=False)
except TypeError:
    _old_md5 = hashlib.md5
    def _new_md5(data=b'', **kwargs):
        return _old_md5(data)
    hashlib.md5 = _new_md5
# --- FIN DEL PARCHE ---

# --- Dependencia para PDF ---
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==============================================================================
# 1. CLASE GestorInventario
# ==============================================================================
class GestorInventario:
    def __init__(self, archivo_inventario=None):
        self.archivo_inventario = archivo_inventario or "bodegac.txt"
        self.archivo_ventas = "registro_ventas.csv"
        self.directorio_facturas = "facturas"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f: pass
        if not os.path.exists(self.archivo_ventas):
            with open(self.archivo_ventas, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'ID_Venta', 'Descripcion', 'Cantidad', 'CostoUnitario', 'PrecioUnitario', 'TotalVenta', 'Ganancia', 'ArchivoOrigen', 'Cliente'])
        if not os.path.exists(self.directorio_facturas):
            os.makedirs(self.directorio_facturas)

    def procesar_item_venta(self, id_venta, timestamp, item_details, cliente):
        try:
            cantidad_vendida = item_details['cantidad']
            precio_venta = item_details['precio']
            costo = item_details['costo']
            
            success, msg = self.modificar_cantidad(item_details['linea_num'], -cantidad_vendida)
            if not success:
                return False, f"Error al actualizar stock para {item_details['desc']}: {msg}"
            
            total_venta_item = cantidad_vendida * precio_venta
            ganancia_item = (precio_venta - costo) * cantidad_vendida
            archivo_origen = os.path.basename(self.archivo_inventario)
            
            venta_data = [
                timestamp.strftime("%Y-%m-%d %H:%M:%S"), id_venta, item_details['desc'],
                cantidad_vendida, f"{costo:.2f}", f"{precio_venta:.2f}",
                f"{total_venta_item:.2f}", f"{ganancia_item:.2f}", archivo_origen, cliente
            ]
            
            with open(self.archivo_ventas, 'a', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow(venta_data)
            
            return True, "Item procesado."
        except Exception as e:
            return False, f"Error procesando item {item_details['desc']}: {e}"

    def generar_factura_consolidada_txt(self, id_venta, timestamp, carrito, total_general, cliente, cliente_contacto):
        nombre_factura = f"Factura_POS_{id_venta}.txt"
        ruta_factura = os.path.join(self.directorio_facturas, nombre_factura)
        ancho_factura = 40

        with open(ruta_factura, 'w', encoding='utf-8') as f:
            f.write("Geek Tecnology".center(ancho_factura) + "\n")
            f.write("Contacto: 304 6313 31 14".center(ancho_factura) + "\n")
            f.write(f"Recibo No: {id_venta}".center(ancho_factura) + "\n")
            f.write("-" * ancho_factura + "\n")
            f.write(f"Fecha: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Cliente: {cliente}\n")
            if cliente_contacto:
                f.write(f"Contacto Cliente: {cliente_contacto}\n")
            f.write("=" * ancho_factura + "\n")
            f.write(f"{'Cant.':<6}{'Descripción':<22}{'Valor':>12}\n")
            f.write("-" * ancho_factura + "\n")
            
            for item in carrito:
                desc_corta = (item['desc'][:20] + '..') if len(item['desc']) > 21 else item['desc']
                subtotal = item['cantidad'] * item['precio']
                f.write(f"{item['cantidad']:<6}{desc_corta:<22}{f'${subtotal:10.2f}':>12}\n")

            f.write("=" * ancho_factura + "\n")
            f.write(f"{'TOTAL:':>28} {f'${total_general:10.2f}':>11}\n")
            f.write("\n" * 2)
            f.write("¡Gracias por su compra!".center(ancho_factura) + "\n")
            f.write("\n" * 2)

        return ruta_factura

    def generar_factura_consolidada_pdf(self, id_venta, timestamp, carrito, total_general, cliente, cliente_contacto):
        nombre_factura_pdf = f"Factura_PDF_{id_venta}.pdf"
        ruta_factura = os.path.join(self.directorio_facturas, nombre_factura_pdf)

        doc = SimpleDocTemplate(ruta_factura, pagesize=(3 * inch, 6 * inch), leftMargin=0.2*inch, rightMargin=0.2*inch, topMargin=0.2*inch, bottomMargin=0.2*inch)
        story = []
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(name='CenterBold', alignment=TA_CENTER, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT, fontName='Helvetica', fontSize=8, leading=10))
        styles.add(ParagraphStyle(name='RightBold', alignment=TA_RIGHT, fontName='Helvetica-Bold', fontSize=10))
        styles.add(ParagraphStyle(name='CenterSmall', alignment=TA_CENTER, fontName='Helvetica', fontSize=7))
        
        story.append(Paragraph("Geek Tecnology", styles['CenterBold']))
        story.append(Paragraph("Contacto: 304 6313 31 14", styles['CenterSmall']))
        story.append(Paragraph(f"Recibo No: {id_venta}", styles['CenterSmall']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(f"<b>Fecha:</b> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Left']))
        story.append(Paragraph(f"<b>Cliente:</b> {cliente}", styles['Left']))
        if cliente_contacto:
            story.append(Paragraph(f"<b>Contacto:</b> {cliente_contacto}", styles['Left']))
        story.append(Spacer(1, 0.1*inch))
        
        data = [['Cant', 'Descripción', 'Subtotal']]
        for item in carrito:
            subtotal = item['cantidad'] * item['precio']
            data.append([item['cantidad'], Paragraph(item['desc'], styles['Left']), f"${subtotal:,.2f}"])

        table = Table(data, colWidths=[0.4*inch, 1.5*inch, 0.7*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8), ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige), ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 7), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph(f"TOTAL: ${total_general:,.2f}", styles['RightBold']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("¡Gracias por su compra!", styles['CenterBold']))

        doc.build(story)
        return ruta_factura

    def imprimir_factura_directo(self, ruta_factura):
        try:
            current_os = platform.system()
            if current_os == "Windows": os.startfile(ruta_factura, "print")
            elif current_os == "Darwin": os.system(f"lpr '{ruta_factura}'")
            elif current_os == "Linux": os.system(f"lp '{ruta_factura}'")
            else: messagebox.showwarning("Impresión no soportada", "La impresión automática no está soportada en este sistema operativo.")
        except Exception as e: messagebox.showerror("Error de Impresión", f"No se pudo enviar la factura a la impresora.\nError: {e}")

    def cambiar_archivo(self, nuevo_archivo):
        self.archivo_inventario = nuevo_archivo
        self.crear_archivos_si_no_existen()
        return f"Archivo de inventario cambiado a: {self.archivo_inventario}"

    def leer_datos(self):
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f: lineas = f.readlines()
            datos, errores = [], []
            for i, linea in enumerate(lineas, 1):
                partes = linea.strip().rsplit(' ', 1)
                if len(partes) == 2:
                    descripcion, cantidad_str = partes
                    try: datos.append((i, descripcion.strip(), int(cantidad_str)))
                    except ValueError: errores.append(f"Línea {i}: Cantidad no es un número.")
                elif linea.strip(): errores.append(f"Línea {i}: Formato incorrecto.")
            return datos, errores
        except Exception as e: return [], [f"Error al leer: {e}"]

    def agregar_linea(self, descripcion, cantidad):
        try:
            with open(self.archivo_inventario, 'a', encoding='utf-8') as f: f.write(f"    {descripcion} {int(cantidad)}\n")
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

    def transferir_a_local(self, descripcion, cantidad_transferida):
        archivo_local = "local.txt"
        try:
            if not os.path.exists(archivo_local):
                with open(archivo_local, 'w', encoding='utf-8') as f: pass

            with open(archivo_local, 'r', encoding='utf-8') as f:
                lineas = f.readlines()

            item_encontrado = False
            descripcion_stripped = descripcion.strip()

            for i, linea in enumerate(lineas):
                partes = linea.strip().rsplit(' ', 1)
                if len(partes) == 2:
                    desc_local, cant_actual_str = partes
                    if desc_local.strip() == descripcion_stripped:
                        nueva_cantidad = int(cant_actual_str) + cantidad_transferida
                        lineas[i] = f"    {descripcion_stripped} {nueva_cantidad}\n"
                        item_encontrado = True
                        break
            
            if not item_encontrado:
                lineas.append(f"    {descripcion_stripped} {cantidad_transferida}\n")

            with open(archivo_local, 'w', encoding='utf-8') as f:
                f.writelines(lineas)
            
            return True, f"Item '{descripcion_stripped}' actualizado en {archivo_local}."

        except Exception as e:
            return False, f"No se pudo actualizar {archivo_local}: {e}"

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
            if not os.path.exists(self.archivo_ventas): return []
            with open(self.archivo_ventas, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                return list(reader)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer historial de ventas: {e}")
            return []
            
    def _leer_lineas_archivo(self):
        with open(self.archivo_inventario, 'r', encoding='utf-8') as f: return f.readlines()
            
    def _escribir_lineas_archivo(self, lineas):
        with open(self.archivo_inventario, 'w', encoding='utf-8') as f: f.writelines(lineas)

# ==============================================================================
# 2. CLASE InventarioGUI
# ==============================================================================
class InventarioGUI:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Inventario y Ventas v2.4 - Transferencia a Local")
        master.geometry("1100x700")
        self.style = ttk.Style(); self.style.theme_use("clam")
        self.gestor = GestorInventario()
        self.carrito = []
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
        
        venta_group = ttk.Frame(action_frame); venta_group.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        style_add = ttk.Style(); style_add.configure("Add.TButton", foreground="white", background="green", font=('Helvetica', 10, 'bold'))
        ttk.Button(venta_group, text="AGREGAR A VENTA", command=self.agregar_a_venta, style="Add.TButton").pack(ipady=5, fill=tk.X)
        self.btn_ver_carrito = ttk.Button(venta_group, text="Ver Carrito (0)", command=self.mostrar_carrito, state="disabled")
        self.btn_ver_carrito.pack(ipady=5, fill=tk.X, pady=(5,0))

    def crear_widgets_ventas(self):
        filter_frame = ttk.LabelFrame(self.ventas_tab, text="Filtros de Búsqueda", padding="10"); filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        analisis_frame = ttk.LabelFrame(self.ventas_tab, text="Totales de la Vista Actual", padding="10"); analisis_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        historial_frame = ttk.Frame(self.ventas_tab); historial_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(filter_frame, text="Desde (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_fecha_desde = ttk.Entry(filter_frame); self.filtro_fecha_desde.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="Hasta (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_fecha_hasta = ttk.Entry(filter_frame); self.filtro_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Label(filter_frame, text="Descripción o ID Venta:").pack(side=tk.LEFT, padx=(0, 5), pady=5)
        self.filtro_desc_venta = ttk.Entry(filter_frame, width=30); self.filtro_desc_venta.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Button(filter_frame, text="Filtrar Ventas", command=self.populate_sales_treeview).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Button(filter_frame, text="Mostrar Todo", command=self.limpiar_filtros_ventas).pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_ver_recibo = ttk.Button(filter_frame, text="Ver Recibo (.txt)", command=self.abrir_recibo_txt, state="disabled")
        self.btn_ver_recibo.pack(side=tk.LEFT, padx=10, pady=5)

        self.lbl_total_items = ttk.Label(analisis_frame, text="Items Vendidos: 0", font=("Helvetica", 10, "bold")); self.lbl_total_items.pack(side=tk.LEFT, padx=20)
        self.lbl_costo_total = ttk.Label(analisis_frame, text="Costo Total: $0.00", font=("Helvetica", 10, "bold")); self.lbl_costo_total.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ventas = ttk.Label(analisis_frame, text="Total Ventas: $0.00", font=("Helvetica", 10, "bold")); self.lbl_total_ventas.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ganancia = ttk.Label(analisis_frame, text="Ganancia Total: $0.00", font=("Helvetica", 10, "bold")); self.lbl_total_ganancia.pack(side=tk.LEFT, padx=20)
        
        columnas = ("Timestamp", "ID_Venta", "Item", "Cantidad", "CostoU", "PrecioU", "Total", "Ganancia", "Origen", "Cliente")
        self.sales_tree = ttk.Treeview(historial_frame, columns=columnas, show="headings")
        for col in columnas: self.sales_tree.heading(col, text=col.replace('_', ' '))
        for col in columnas: self.sales_tree.column(col, anchor=tk.W, width=90)
        self.sales_tree.column("Timestamp", width=140); self.sales_tree.column("Item", width=250)
        scrollbar_s = ttk.Scrollbar(historial_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar_s.set); self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)
        self.sales_tree.bind('<<TreeviewSelect>>', self.on_sale_select)

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
        filtro_texto = self.filtro_desc_venta.get().lower()

        total_items, costo_total, total_ventas, total_ganancia = 0, 0.0, 0.0, 0.0

        for venta_original in historial:
            venta = list(venta_original)

            if len(venta) < 8: continue
            if len(venta) == 9: venta.insert(1, "N/A")
            if len(venta) == 8:
                venta.insert(1, "N/A")
                venta.append("N/A")
            if len(venta) != 10: continue

            fecha_valida = True
            if desde_str or hasta_str:
                try:
                    fecha_venta = datetime.strptime(venta[0], "%Y-%m-%d %H:%M:%S")
                    if desde_str and fecha_venta < datetime.strptime(desde_str, "%Y-%m-%d"): fecha_valida = False
                    if hasta_str and fecha_venta > (datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)): fecha_valida = False
                except ValueError: fecha_valida = False 
            if not fecha_valida: continue

            id_venta_csv = venta[1].lower()
            desc_csv = venta[2].lower()
            if filtro_texto and not (filtro_texto in desc_csv or filtro_texto in id_venta_csv): continue

            try:
                total_items += int(venta[3])
                costo_total += int(venta[3]) * float(venta[4])
                total_ventas += float(venta[6])
                total_ganancia += float(venta[7])
                self.sales_tree.insert("", tk.END, values=tuple(venta))
            except (ValueError, IndexError): continue
        
        self.lbl_total_items.config(text=f"Items Vendidos: {total_items}")
        self.lbl_costo_total.config(text=f"Costo Total: ${costo_total:.2f}")
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
        linea, desc, cant_actual_str = values
        accion = "sumar" if sumar else "restar"
        try:
            cambio = simpledialog.askinteger("Ajustar Stock", f"Cantidad a {accion} para:\n{desc}", parent=self.master, minvalue=1)
            if cambio is not None:
                if sumar:
                    success, msg = self.gestor.modificar_cantidad(int(linea), cambio)
                    if success: messagebox.showinfo("Éxito", msg)
                    else: messagebox.showerror("Error", msg)
                else: # Restar y transferir
                    if cambio > int(cant_actual_str):
                        messagebox.showerror("Error", "No se puede restar más stock del que existe.")
                        return
                    success, msg = self.gestor.modificar_cantidad(int(linea), -cambio)
                    if success:
                        success_local, msg_local = self.gestor.transferir_a_local(desc, cambio)
                        if success_local:
                            messagebox.showinfo("Operación Completa", f"{msg}\n{cambio} unidad(es) transferida(s) a 'local.txt'.")
                        else:
                            messagebox.showwarning("Error de Transferencia", f"{msg}\nPero hubo un error al transferir a 'local.txt':\n{msg_local}")
                    else:
                        messagebox.showerror("Error", msg)
                self.populate_inventory_treeview()
        except ValueError: messagebox.showerror("Error", "Debe ser un número.")

    def ordenar_alfabeticamente(self):
        if messagebox.askyesno("Confirmar", "¿Desea ordenar el inventario alfabéticamente?"):
            success, msg = self.gestor.ordenar_alfabeticamente()
            if success: self.populate_inventory_treeview(); messagebox.showinfo("Éxito", msg)
            else: messagebox.showerror("Error", msg)

    def verificar_formato(self):
        errores = self.gestor.verificar_formato()
        if not errores: messagebox.showinfo("Verificación", "¡El formato de todas las líneas es correcto!")
        else: messagebox.showwarning("Verificación", "Líneas con formato incorrecto:\n\n" + "\n".join(errores))

    def agregar_a_venta(self):
        values = self._get_selected_item_values()
        if not values: return
        linea_num, desc, stock_actual = values

        win_add_cart = tk.Toplevel(self.master); win_add_cart.title("Agregar Item a Venta"); win_add_cart.grab_set()
        frame = ttk.Frame(win_add_cart, padding="15")
        frame.pack()
        
        ttk.Label(frame, text=f"Item: {desc}", font=("Helvetica", 11, "bold")).grid(row=0, columnspan=2, pady=(0, 10))
        ttk.Label(frame, text=f"Stock Actual: {stock_actual}").grid(row=1, columnspan=2, pady=(0, 15))
        
        ttk.Label(frame, text="Cantidad a Vender:").grid(row=2, column=0, sticky="w", pady=5)
        cant_entry = ttk.Entry(frame, width=15); cant_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(frame, text="Costo Unitario ($):").grid(row=3, column=0, sticky="w", pady=5)
        costo_entry = ttk.Entry(frame, width=15); costo_entry.grid(row=3, column=1, sticky="w", pady=5)
        
        ttk.Label(frame, text="Precio de Venta ($):").grid(row=4, column=0, sticky="w", pady=5)
        precio_entry = ttk.Entry(frame, width=15); precio_entry.grid(row=4, column=1, sticky="w", pady=5)
        
        def do_add_to_cart():
            try:
                cantidad = int(cant_entry.get())
                costo = float(costo_entry.get())
                precio = float(precio_entry.get())
                if cantidad <= 0: raise ValueError("La cantidad debe ser positiva.")
                if cantidad > int(stock_actual): messagebox.showerror("Stock Insuficiente", "La cantidad a vender supera el stock actual.", parent=win_add_cart); return
            except (ValueError, TypeError):
                messagebox.showerror("Datos Inválidos", "Por favor, ingrese números válidos en todos los campos.", parent=win_add_cart)
                return

            item_data = {
                'linea_num': int(linea_num), 'desc': desc, 'stock_actual': int(stock_actual),
                'cantidad': cantidad, 'costo': costo, 'precio': precio
            }
            self.carrito.append(item_data)
            self.actualizar_vista_carrito()
            win_add_cart.destroy()

        ttk.Button(frame, text="Agregar al Carrito", command=do_add_to_cart).grid(row=5, columnspan=2, pady=(20, 0))
        cant_entry.focus_set()

    def actualizar_vista_carrito(self):
        num_items = len(self.carrito)
        self.btn_ver_carrito.config(text=f"Ver Carrito ({num_items})")
        self.btn_ver_carrito.config(state="normal" if num_items > 0 else "disabled")

    def mostrar_carrito(self):
        win_cart = tk.Toplevel(self.master)
        win_cart.title("Carrito de Venta")
        win_cart.grab_set()
        win_cart.geometry("600x550")
        win_cart.minsize(500, 450)

        bottom_panel = ttk.Frame(win_cart, padding=10)
        bottom_panel.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tree_panel = ttk.Frame(win_cart, padding=10)
        tree_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        top_controls_frame = ttk.Frame(tree_panel)
        top_controls_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(top_controls_frame, text="Eliminar Item Seleccionado", command=lambda: eliminar_item_carrito()).pack(side=tk.LEFT)
        lbl_total = ttk.Label(top_controls_frame, text="", font=("Helvetica", 12, "bold"))
        lbl_total.pack(side=tk.RIGHT)

        cart_tree = ttk.Treeview(tree_panel, columns=("Desc", "Cant", "PrecioU", "Subtotal"), show="headings")
        cart_tree.heading("Desc", text="Descripción"); cart_tree.heading("Cant", text="Cantidad"); cart_tree.heading("PrecioU", text="Precio Unit."); cart_tree.heading("Subtotal", text="Subtotal")
        scrollbar = ttk.Scrollbar(tree_panel, orient=tk.VERTICAL, command=cart_tree.yview)
        cart_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        cart_tree.pack(fill=tk.BOTH, expand=True)

        client_frame = ttk.LabelFrame(bottom_panel, text="Datos del Cliente", padding="10")
        client_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(client_frame, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        cliente_entry = ttk.Entry(client_frame, width=30); cliente_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(client_frame, text="Contacto (Opcional):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        cliente_contacto_entry = ttk.Entry(client_frame, width=30); cliente_contacto_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        client_frame.columnconfigure(1, weight=1)
        
        style_confirm = ttk.Style(); style_confirm.configure("Confirm.TButton", foreground="white", background="navy", font=('Helvetica', 10, 'bold'))
        ttk.Button(bottom_panel, text="CONFIRMAR VENTA Y FACTURAR", style="Confirm.TButton", command=lambda: finalizar_venta()).pack(fill=tk.X, ipady=5)

        total_general = 0
        def populate_cart_tree():
            nonlocal total_general
            for i in cart_tree.get_children(): cart_tree.delete(i)
            total_general = 0
            for i, item in enumerate(self.carrito):
                subtotal = item['cantidad'] * item['precio']
                total_general += subtotal
                cart_tree.insert("", tk.END, iid=i, values=(item['desc'], item['cantidad'], f"${item['precio']:.2f}", f"${subtotal:.2f}"))
            lbl_total.config(text=f"TOTAL: ${total_general:.2f}")
        
        populate_cart_tree()

        def eliminar_item_carrito():
            selected_iid = cart_tree.focus()
            if not selected_iid:
                messagebox.showwarning("Sin Selección", "Seleccione un item del carrito para eliminar.", parent=win_cart)
                return
            del self.carrito[int(selected_iid)]
            populate_cart_tree()
            self.actualizar_vista_carrito()

        def finalizar_venta():
            cliente = cliente_entry.get().strip() or "Cliente General"
            cliente_contacto = cliente_contacto_entry.get().strip()
            if not self.carrito:
                messagebox.showerror("Carrito Vacío", "No hay items en el carrito para vender.", parent=win_cart)
                return

            timestamp = datetime.now()
            id_venta = timestamp.strftime('%Y%m%d%H%M%S')
            
            carrito_copia = list(self.carrito)

            for item in carrito_copia:
                success, msg = self.gestor.procesar_item_venta(id_venta, timestamp, item, cliente)
                if not success:
                    messagebox.showerror("Error en Venta", msg, parent=win_cart)
                    self.populate_inventory_treeview()
                    return
            
            ruta_txt = self.gestor.generar_factura_consolidada_txt(id_venta, timestamp, carrito_copia, total_general, cliente, cliente_contacto)
            
            win_cart.destroy()
            self.show_output_options_dialog(ruta_txt, id_venta, timestamp, carrito_copia, total_general, cliente, cliente_contacto)
            
            self.carrito.clear()
            self.actualizar_vista_carrito()
            self.populate_inventory_treeview()
            self.populate_sales_treeview()
            self.notebook.select(self.ventas_tab)

    def show_output_options_dialog(self, ruta_factura_txt, id_venta, timestamp, carrito, total_general, cliente, cliente_contacto):
        win_options = tk.Toplevel(self.master); win_options.title("Venta Exitosa"); win_options.grab_set()
        frame = ttk.Frame(win_options, padding="20"); frame.pack()
        ttk.Label(frame, text="Venta registrada con éxito.\n¿Qué desea hacer ahora?", justify=tk.CENTER, font=("Helvetica", 10)).pack(pady=(0, 15))
        btn_frame = ttk.Frame(frame); btn_frame.pack()

        def on_print():
            self.gestor.imprimir_factura_directo(ruta_factura_txt)
            win_options.destroy()

        def on_pdf():
            if not REPORTLAB_AVAILABLE:
                messagebox.showerror("Librería Faltante", "Para generar PDF, necesita instalar 'reportlab'.\n\nAbra una terminal y ejecute:\npip install reportlab", parent=win_options)
                return
            try:
                pdf_path = self.gestor.generar_factura_consolidada_pdf(id_venta, timestamp, carrito, total_general, cliente, cliente_contacto)
                messagebox.showinfo("Éxito", f"Factura guardada como PDF en:\n{pdf_path}", parent=self.master)
                win_options.destroy()
            except Exception as e:
                messagebox.showerror("Error al crear PDF", f"No se pudo generar el archivo PDF.\nError: {e}", parent=win_options)

        ttk.Button(btn_frame, text="Imprimir Recibo", command=on_print).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Guardar como PDF", command=on_pdf).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Finalizar", command=win_options.destroy).pack(side=tk.LEFT, padx=10)

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

    def on_sale_select(self, event):
        if len(self.sales_tree.selection()) == 1:
            self.btn_ver_recibo.config(state="normal")
        else:
            self.btn_ver_recibo.config(state="disabled")

    def abrir_recibo_txt(self):
        if not self.sales_tree.selection(): return
        
        selected_item = self.sales_tree.selection()[0]
        id_venta = self.sales_tree.item(selected_item, 'values')[1]
        
        nombre_archivo = f"Factura_POS_{id_venta}.txt"
        ruta_archivo = os.path.join(self.gestor.directorio_facturas, nombre_archivo)

        if os.path.exists(ruta_archivo):
            try:
                current_os = platform.system()
                if current_os == "Windows":
                    os.startfile(ruta_archivo)
                elif current_os == "Darwin": # macOS
                    subprocess.call(('open', ruta_archivo))
                else: # Linux
                    subprocess.call(('xdg-open', ruta_archivo))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
        else:
            messagebox.showinfo("No Encontrado", f"No se encontró el archivo de recibo:\n{nombre_archivo}\n\n(Es posible que sea de una venta anterior al sistema de recibos).")

# ==============================================================================
# 3. BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()
