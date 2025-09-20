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
try:
    hashlib.md5(usedforsecurity=False)
except TypeError:
    _old_md5 = hashlib.md5

    def _new_md5(data=b"", **kwargs):
        return _old_md5(data)

    hashlib.md5 = _new_md5
# --- FIN DEL PARCHE ---

# --- Dependencias Externas ---
try:
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from tkcalendar import DateEntry

    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False


# ==============================================================================
# 1. CLASE GestorCaja
# ==============================================================================
class GestorCaja:
    def __init__(self):
        self.archivo_registros = "caja_registros.csv"
        self.archivo_movimientos = "movimientos_caja.csv"
        self.archivo_historial_conteos = "conteo_caja_historial.csv"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        if not os.path.exists(self.archivo_registros):
            with open(self.archivo_registros, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Fecha",
                        "DineroInicial",
                        "Base",
                        "PagosElectronicos",
                        "DineroEnCaja",
                        "TotalVentas",
                        "TotalMovimientos",
                        "EfectivoEsperado",
                        "Diferencia",
                    ]
                )
        if not os.path.exists(self.archivo_movimientos):
            with open(self.archivo_movimientos, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Tipo", "Descripcion", "Monto"])
        if not os.path.exists(self.archivo_historial_conteos):
            with open(
                self.archivo_historial_conteos, "w", encoding="utf-8", newline=""
            ) as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "TotalContado", "DetalleConteo"])

    def iniciar_dia(self, dinero_inicial, base):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        if self.obtener_datos_dia(fecha_hoy):
            return False, "El día ya ha sido iniciado."

        try:
            with open(self.archivo_registros, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([fecha_hoy, dinero_inicial, base, 0, 0, 0, 0, 0, 0])
            return True, "Día iniciado correctamente."
        except Exception as e:
            return False, f"Error al iniciar el día: {e}"

    def registrar_movimiento(self, tipo, descripcion, monto):
        try:
            monto_float = float(monto)
            if tipo in ["Gasto", "Préstamo/Retiro"]:
                monto_float = -abs(monto_float)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.archivo_movimientos, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, tipo, descripcion, monto_float])
            return True, "Movimiento registrado."
        except ValueError:
            return False, "El monto debe ser un número válido."
        except Exception as e:
            return False, f"Error al registrar movimiento: {e}"

    def guardar_conteo_historial(self, total, detalle):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(
                self.archivo_historial_conteos, "a", encoding="utf-8", newline=""
            ) as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, total, detalle])
            return True, "Conteo guardado en el historial."
        except Exception as e:
            return False, f"Error al guardar conteo: {e}"

    def obtener_historial_conteos(self):
        try:
            with open(self.archivo_historial_conteos, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                return list(reader)
        except FileNotFoundError:
            return []
        except Exception as e:
            messagebox.showerror(
                "Error de Lectura", f"No se pudo leer el historial de conteos: {e}"
            )
            return []

    def obtener_datos_dia(self, fecha_str):
        try:
            with open(self.archivo_registros, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Fecha"] == fecha_str:
                        return row
            return None
        except FileNotFoundError:
            return None

    def obtener_movimientos_dia(self, fecha_str):
        movimientos = []
        try:
            with open(self.archivo_movimientos, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Timestamp"].startswith(fecha_str):
                        movimientos.append(row)
            return movimientos
        except FileNotFoundError:
            return []

    def calcular_cuadre(
        self, fecha_str, pagos_electronicos, dinero_real_caja, total_ventas_dia
    ):
        datos_dia = self.obtener_datos_dia(fecha_str)
        if not datos_dia:
            return None, "El día no ha sido iniciado."

        try:
            dinero_inicial = float(datos_dia["DineroInicial"])
            base = float(datos_dia["Base"])

            movimientos = self.obtener_movimientos_dia(fecha_str)
            total_movimientos = sum(float(m["Monto"]) for m in movimientos)

            efectivo_esperado = (
                dinero_inicial + base + total_ventas_dia + total_movimientos
            ) - pagos_electronicos
            diferencia = dinero_real_caja - (efectivo_esperado - base)

            resumen = {
                "dinero_inicial": dinero_inicial,
                "base": base,
                "total_ventas": total_ventas_dia,
                "total_movimientos": total_movimientos,
                "pagos_electronicos": pagos_electronicos,
                "efectivo_esperado": efectivo_esperado,
                "dinero_real_caja": dinero_real_caja,
                "diferencia": diferencia,
            }
            return resumen, "Cálculo exitoso."
        except Exception as e:
            return None, f"Error al calcular el cuadre: {e}"

    def cerrar_dia(self, fecha_str, resumen):
        try:
            lineas_actualizadas = []
            with open(self.archivo_registros, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                lineas_actualizadas.append(header)
                for row in reader:
                    if row[0] == fecha_str:
                        row = [
                            fecha_str,
                            resumen["dinero_inicial"],
                            resumen["base"],
                            resumen["pagos_electronicos"],
                            resumen["dinero_real_caja"],
                            resumen["total_ventas"],
                            resumen["total_movimientos"],
                            resumen["efectivo_esperado"],
                            resumen["diferencia"],
                        ]
                    lineas_actualizadas.append(row)

            with open(self.archivo_registros, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lineas_actualizadas)

            return True, "Caja cerrada y registrada con éxito."
        except Exception as e:
            return False, f"Error al guardar el cierre de caja: {e}"


# ==============================================================================
# 2. CLASE GestorInventario
# ==============================================================================
class GestorInventario:
    def __init__(self, archivo_inventario=None):
        self.archivo_inventario = archivo_inventario or "bodegac.txt"
        self.archivo_ventas = "registro_ventas.csv"
        self.directorio_facturas = "facturas"
        self.crear_archivos_si_no_existen()

    def obtener_pagos_electronicos_del_dia(self, fecha_str):
        total_electronico = 0.0
        ventas_procesadas = set()  # <-- SOLUCIÓN 1: Para no duplicar ventas
        try:
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Omitir encabezado
                for row in reader:
                    if not row or not row[0].startswith(fecha_str):
                        continue

                    try:
                        id_venta = row[1]
                        if id_venta in ventas_procesadas:
                            continue  # Ya procesamos los pagos de esta venta

                        medio_pago_str = row[10]

                        # --- SOLUCIÓN 2: Lógica para manejar registros nuevos y antiguos ---
                        if ":" in medio_pago_str:  # Formato nuevo (ej: "Nequi: $10.00")
                            pagos = medio_pago_str.split(", ")
                            for pago in pagos:
                                if "Efectivo" not in pago:
                                    monto_str_part = pago.split("$")[-1].strip()
                                    monto_limpio = re.sub(
                                        r"[^\d,.]", "", monto_str_part
                                    )
                                    if not monto_limpio:
                                        continue

                                    if "," in monto_limpio and (
                                        "." not in monto_limpio
                                        or monto_limpio.rfind(",")
                                        > monto_limpio.rfind(".")
                                    ):
                                        monto_procesado = monto_limpio.replace(
                                            ".", ""
                                        ).replace(",", ".")
                                    else:
                                        monto_procesado = monto_limpio.replace(",", "")

                                    if monto_procesado:
                                        total_electronico += float(monto_procesado)

                        else:  # Formato antiguo (ej: "Nequi")
                            if medio_pago_str.strip() not in ["Efectivo", "N/A", ""]:
                                # En el formato antiguo, todo el total de la venta era electrónico
                                total_venta_item = float(row[6])
                                total_electronico += total_venta_item
                        # --- FIN DE LA SOLUCIÓN ---

                        ventas_procesadas.add(id_venta)

                    except (ValueError, IndexError, TypeError):
                        continue
            return total_electronico
        except FileNotFoundError:
            return 0.0

    def obtener_ventas_del_dia(self, fecha_str):
        total_ventas = 0.0
        try:
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Omitir encabezado
                for row in reader:
                    if row and row[0].startswith(fecha_str):
                        try:
                            total_ventas += float(row[6])  # Columna 'TotalVenta'
                        except (ValueError, IndexError):
                            continue
            return total_ventas
        except FileNotFoundError:
            return 0.0

    def crear_archivos_si_no_existen(self):
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, "w", encoding="utf-8") as f:
                pass
        if not os.path.exists(self.archivo_ventas):
            with open(self.archivo_ventas, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "Timestamp",
                        "ID_Venta",
                        "Descripcion",
                        "Cantidad",
                        "CostoUnitario",
                        "PrecioUnitario",
                        "TotalVenta",
                        "Ganancia",
                        "ArchivoOrigen",
                        "Cliente",
                        "MedioPago",
                    ]
                )
        if not os.path.exists(self.directorio_facturas):
            os.makedirs(self.directorio_facturas)

    def procesar_item_venta(
        self, id_venta, timestamp, item_details, cliente, medio_pago
    ):
        try:
            cantidad_vendida = item_details["cantidad"]
            precio_venta = item_details["precio"]
            costo = item_details["costo"]

            success, msg = self.modificar_cantidad(
                item_details["linea_num"], -cantidad_vendida
            )
            if not success:
                return (
                    False,
                    f"Error al actualizar stock para {item_details['desc']}: {msg}",
                )

            total_venta_item = cantidad_vendida * precio_venta
            ganancia_item = (precio_venta - costo) * cantidad_vendida
            archivo_origen = os.path.basename(self.archivo_inventario)

            venta_data = [
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                id_venta,
                item_details["desc"],
                cantidad_vendida,
                f"{costo:.2f}",
                f"{precio_venta:.2f}",
                f"{total_venta_item:.2f}",
                f"{ganancia_item:.2f}",
                archivo_origen,
                cliente,
                medio_pago,
            ]

            with open(self.archivo_ventas, "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow(venta_data)

            return True, "Item procesado."
        except Exception as e:
            return False, f"Error procesando item {item_details['desc']}: {e}"

    def generar_factura_consolidada_txt(
        self,
        id_venta,
        timestamp,
        carrito,
        total_general,
        cliente,
        cliente_contacto,
        pagos,
    ):
        nombre_factura = f"Factura_POS_{id_venta}.txt"
        ruta_factura = os.path.join(self.directorio_facturas, nombre_factura)
        ancho_factura = 40

        with open(ruta_factura, "w", encoding="utf-8") as f:
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
                desc_corta = (
                    (item["desc"][:20] + "..")
                    if len(item["desc"]) > 21
                    else item["desc"]
                )
                subtotal = item["cantidad"] * item["precio"]
                f.write(
                    f"{item['cantidad']:<6}{desc_corta:<22}{f'${subtotal:10.2f}':>12}\n"
                )

            f.write("=" * ancho_factura + "\n")
            f.write(f"{'TOTAL:':>28} {f'${total_general:10.2f}':>11}\n")

            if pagos:
                f.write("-" * ancho_factura + "\n")
                f.write("Medios de Pago:\n")
                for pago in pagos:
                    f.write(f"  {pago['metodo']:<15} ${pago['monto']:>10,.2f}\n")

            f.write("\n" * 2)
            f.write("¡Gracias por su compra!".center(ancho_factura) + "\n")
            f.write("\n" * 2)

        return ruta_factura

    def generar_factura_consolidada_pdf(
        self,
        id_venta,
        timestamp,
        carrito,
        total_general,
        cliente,
        cliente_contacto,
        pagos,
    ):
        nombre_factura_pdf = f"Factura_PDF_{id_venta}.pdf"
        ruta_factura = os.path.join(self.directorio_facturas, nombre_factura_pdf)

        doc = SimpleDocTemplate(
            ruta_factura,
            pagesize=(3 * inch, 6 * inch),
            leftMargin=0.2 * inch,
            rightMargin=0.2 * inch,
            topMargin=0.2 * inch,
            bottomMargin=0.2 * inch,
        )
        story = []
        styles = getSampleStyleSheet()

        styles.add(
            ParagraphStyle(
                name="CenterBold", alignment=TA_CENTER, fontName="Helvetica-Bold"
            )
        )
        styles.add(
            ParagraphStyle(
                name="Left",
                alignment=TA_LEFT,
                fontName="Helvetica",
                fontSize=8,
                leading=10,
            )
        )
        styles.add(
            ParagraphStyle(
                name="RightBold",
                alignment=TA_RIGHT,
                fontName="Helvetica-Bold",
                fontSize=10,
            )
        )
        styles.add(
            ParagraphStyle(
                name="CenterSmall",
                alignment=TA_CENTER,
                fontName="Helvetica",
                fontSize=7,
            )
        )

        story.append(Paragraph("Geek Tecnology", styles["CenterBold"]))
        story.append(Paragraph("Contacto: 304 6313 31 14", styles["CenterSmall"]))
        story.append(Paragraph(f"Recibo No: {id_venta}", styles["CenterSmall"]))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"<b>Fecha:</b> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Left"],
            )
        )
        story.append(Paragraph(f"<b>Cliente:</b> {cliente}", styles["Left"]))
        if cliente_contacto:
            story.append(
                Paragraph(f"<b>Contacto:</b> {cliente_contacto}", styles["Left"])
            )
        story.append(Spacer(1, 0.1 * inch))

        data = [["Cant", "Descripción", "Subtotal"]]
        for item in carrito:
            subtotal = item["cantidad"] * item["precio"]
            data.append(
                [
                    item["cantidad"],
                    Paragraph(item["desc"], styles["Left"]),
                    f"${subtotal:,.2f}",
                ]
            )

        table = Table(data, colWidths=[0.4 * inch, 1.5 * inch, 0.7 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph(f"TOTAL: ${total_general:,.2f}", styles["RightBold"]))

        if pagos:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("<b>Medios de Pago:</b>", styles["Left"]))
            for pago in pagos:
                pago_texto = f"{pago['metodo']}: ${pago['monto']:,.2f}"
                story.append(Paragraph(pago_texto, styles["Left"]))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("¡Gracias por su compra!", styles["CenterBold"]))

        doc.build(story)
        return ruta_factura

    def imprimir_factura_directo(self, ruta_factura):
        try:
            current_os = platform.system()
            if current_os == "Windows":
                os.startfile(ruta_factura, "print")
            elif current_os == "Darwin":
                os.system(f"lpr '{ruta_factura}'")
            elif current_os == "Linux":
                os.system(f"lp '{ruta_factura}'")
            else:
                messagebox.showwarning(
                    "Impresión no soportada",
                    "La impresión automática no está soportada en este sistema operativo.",
                )
        except Exception as e:
            messagebox.showerror(
                "Error de Impresión",
                f"No se pudo enviar la factura a la impresora.\nError: {e}",
            )

    def cambiar_archivo(self, nuevo_archivo):
        self.archivo_inventario = nuevo_archivo
        self.crear_archivos_si_no_existen()
        return f"Archivo de inventario cambiado a: {self.archivo_inventario}"

    def leer_datos(self):
        try:
            with open(self.archivo_inventario, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            datos, errores = [], []
            for i, linea in enumerate(lineas, 1):
                partes = linea.strip().rsplit(" ", 1)
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
            with open(self.archivo_inventario, "a", encoding="utf-8") as f:
                f.write(f"    {descripcion} {int(cantidad)}\n")
            return True, "Ítem agregado."
        except ValueError:
            return False, "Cantidad debe ser un número."
        except Exception as e:
            return False, f"Error: {e}"

    def modificar_linea(self, num_linea, desc, cant):
        try:
            lineas = self._leer_lineas_archivo()
            if 1 <= num_linea <= len(lineas):
                lineas[num_linea - 1] = f"    {desc} {int(cant)}\n"
                self._escribir_lineas_archivo(lineas)
                return True, "Ítem modificado."
            return False, "Número de línea fuera de rango."
        except ValueError:
            return False, "Cantidad debe ser un número."
        except Exception as e:
            return False, f"Error: {e}"

    def modificar_cantidad(self, num_linea, cambio):
        try:
            lineas = self._leer_lineas_archivo()
            if 1 <= num_linea <= len(lineas):
                partes = lineas[num_linea - 1].strip().rsplit(" ", 1)
                if len(partes) == 2:
                    desc, cant_str = partes
                    nueva_cant = int(cant_str) + int(cambio)
                    if nueva_cant < 0:
                        return False, "Stock no puede ser negativo."
                    lineas[num_linea - 1] = f"    {desc.strip()} {nueva_cant}\n"
                    self._escribir_lineas_archivo(lineas)
                    return True, "Stock actualizado."
                return False, "Formato de línea inválido."
            return False, "Número de línea fuera de rango."
        except ValueError:
            return False, "Cantidad debe ser un número."
        except Exception as e:
            return False, f"Error: {e}"

    def transferir_a_local(self, descripcion, cantidad_transferida):
        archivo_local = "local.txt"
        try:
            if not os.path.exists(archivo_local):
                with open(archivo_local, "w", encoding="utf-8") as f:
                    pass

            with open(archivo_local, "r", encoding="utf-8") as f:
                lineas = f.readlines()

            item_encontrado = False
            descripcion_stripped = descripcion.strip()

            for i, linea in enumerate(lineas):
                partes = linea.strip().rsplit(" ", 1)
                if len(partes) == 2:
                    desc_local, cant_actual_str = partes
                    if desc_local.strip() == descripcion_stripped:
                        nueva_cantidad = int(cant_actual_str) + cantidad_transferida
                        lineas[i] = f"    {descripcion_stripped} {nueva_cantidad}\n"
                        item_encontrado = True
                        break

            if not item_encontrado:
                lineas.append(f"    {descripcion_stripped} {cantidad_transferida}\n")

            with open(archivo_local, "w", encoding="utf-8") as f:
                f.writelines(lineas)

            return (
                True,
                f"Item '{descripcion_stripped}' actualizado en {archivo_local}.",
            )

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
        except Exception as e:
            return False, f"Error: {e}"

    def ordenar_alfabeticamente(self):
        try:
            lineas = self._leer_lineas_archivo()
            lineas.sort(key=str.lower)
            self._escribir_lineas_archivo(lineas)
            return True, "Inventario ordenado alfabéticamente."
        except Exception as e:
            return False, f"Error al ordenar: {e}"

    def verificar_formato(self):
        errores = []
        for i, linea in enumerate(self._leer_lineas_archivo(), 1):
            if not linea.strip():
                continue
            partes = linea.strip().rsplit(" ", 1)
            if len(partes) != 2 or not partes[1].isdigit():
                errores.append(f"Línea {i}: '{linea.strip()}'")
        return errores

    def leer_historial_ventas(self):
        try:
            if not os.path.exists(self.archivo_ventas):
                return []
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                return list(reader)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer historial de ventas: {e}")
            return []

    def _leer_lineas_archivo(self):
        with open(self.archivo_inventario, "r", encoding="utf-8") as f:
            return f.readlines()

    def _escribir_lineas_archivo(self, lineas):
        with open(self.archivo_inventario, "w", encoding="utf-8") as f:
            f.writelines(lineas)


# ==============================================================================
# 3. CLASE InventarioGUI
# ==============================================================================
class InventarioGUI:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Inventario y Ventas v4.1 - Acceso Rápido")
        master.geometry("1200x750")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.gestor = GestorInventario()
        self.gestor_caja = GestorCaja()
        self.carrito = []
        self.conteo_actual_caja = {}

        if not TKCALENDAR_AVAILABLE:
            messagebox.showwarning(
                "Librería Faltante",
                "La librería 'tkcalendar' no está instalada.\n\nEl selector de fechas no estará disponible.\nPara instalarla, abra una terminal y ejecute:\npip install tkcalendar",
            )

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.inventario_tab = ttk.Frame(self.notebook, padding="10")
        self.ventas_tab = ttk.Frame(self.notebook, padding="10")
        self.caja_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.inventario_tab, text="Gestión de Inventario")
        self.notebook.add(self.ventas_tab, text="Ventas y Análisis")
        self.notebook.add(self.caja_tab, text="Cuadre de Caja")

        self.crear_widgets_inventario()
        self.crear_widgets_ventas()
        self.crear_widgets_caja()

        self.populate_inventory_treeview()
        self.populate_sales_treeview()
        self.master.after(100, lambda: self.add_placeholder(None))
        self.cargar_estado_caja()
        self.actualizar_estado_botones_venta()

        self.sales_last_sort_col = None
        self.sales_last_sort_reverse = False

    # --- Widgets de Inventario y Ventas ---
    def crear_widgets_inventario(self):
        top_frame = ttk.Frame(self.inventario_tab)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        filter_frame = ttk.Frame(self.inventario_tab)
        filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        tree_frame = ttk.Frame(self.inventario_tab)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        action_frame = ttk.Frame(self.inventario_tab)
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.lbl_archivo = ttk.Label(
            top_frame, text=f"Archivo: {self.gestor.archivo_inventario}"
        )
        self.lbl_archivo.pack(side=tk.LEFT, padx=5)

        # --- MEJORA: Botones de acceso rápido ---
        ttk.Button(
            top_frame,
            text="Cargar Bodega C",
            command=lambda: self.cambiar_archivo_rapido("bodegac.txt"),
        ).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(
            top_frame,
            text="Cargar Local",
            command=lambda: self.cambiar_archivo_rapido("local.txt"),
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Buscar Otro...", command=self.cambiar_archivo).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        # --- FIN DE LA MEJORA ---

        self.status_label_inv = ttk.Label(top_frame, text="Listo.", anchor=tk.E)
        self.status_label_inv.pack(
            side=tk.RIGHT, padx=5, fill=tk.X, expand=True
        )  # Ajuste de layout

        ttk.Label(filter_frame, text="Filtrar por palabra clave:").pack(
            side=tk.LEFT, padx=5
        )
        self.filtro_palabra_entry = ttk.Entry(filter_frame, width=20)
        self.filtro_palabra_entry.pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry.bind("<FocusIn>", self.clear_placeholder)
        self.filtro_palabra_entry.bind("<FocusOut>", self.add_placeholder)
        ttk.Label(filter_frame, text="y por cantidad:").pack(side=tk.LEFT, padx=5)
        self.filtro_op_combo = ttk.Combobox(
            filter_frame, values=["", ">", "<", "="], width=3, state="readonly"
        )
        self.filtro_op_combo.pack(side=tk.LEFT, padx=5)
        self.filtro_cant_entry = ttk.Entry(filter_frame, width=10)
        self.filtro_cant_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Aplicar Filtro / Refrescar",
            command=self.populate_inventory_treeview,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="Limpiar", command=self.limpiar_filtros).pack(
            side=tk.LEFT, padx=5
        )

        self.inventory_tree = ttk.Treeview(
            tree_frame, columns=("Linea", "Item", "Cantidad"), show="headings"
        )
        self.inventory_tree.heading("Linea", text="Línea")
        self.inventory_tree.heading("Item", text="Item")
        self.inventory_tree.heading("Cantidad", text="Cantidad en Stock")
        self.inventory_tree.column("Linea", width=60, anchor=tk.CENTER)
        self.inventory_tree.column("Item", width=500)
        self.inventory_tree.column("Cantidad", width=120, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview
        )
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        stock_group = ttk.LabelFrame(action_frame, text="Stock")
        stock_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(
            stock_group,
            text="Sumar Unidades (+)",
            command=lambda: self.ajustar_cantidad(True),
        ).pack(pady=2, padx=5)
        ttk.Button(
            stock_group,
            text="Restar Unidades (-)",
            command=lambda: self.ajustar_cantidad(False),
        ).pack(pady=2, padx=5)

        item_group = ttk.LabelFrame(action_frame, text="Ítems")
        item_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(item_group, text="Agregar Nuevo", command=self.agregar_item).pack(
            pady=2, padx=5
        )
        ttk.Button(
            item_group, text="Modificar Seleccionado", command=self.modificar_item
        ).pack(pady=2, padx=5)
        ttk.Button(
            item_group, text="Eliminar Seleccionado", command=self.eliminar_item
        ).pack(pady=2, padx=5)

        tools_group = ttk.LabelFrame(action_frame, text="Herramientas")
        tools_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(
            tools_group,
            text="Ordenar Alfabéticamente",
            command=self.ordenar_alfabeticamente,
        ).pack(pady=2, padx=5)
        ttk.Button(
            tools_group, text="Verificar Formato", command=self.verificar_formato
        ).pack(pady=2, padx=5)

        venta_group = ttk.Frame(action_frame)
        venta_group.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        style_add = ttk.Style()
        style_add.configure(
            "Add.TButton",
            foreground="white",
            background="green",
            font=("Helvetica", 10, "bold"),
        )
        self.btn_agregar_venta = ttk.Button(
            venta_group,
            text="AGREGAR A VENTA",
            command=self.agregar_a_venta,
            style="Add.TButton",
        )
        self.btn_agregar_venta.pack(ipady=5, fill=tk.X)
        self.btn_ver_carrito = ttk.Button(
            venta_group,
            text="Ver Carrito (0)",
            command=self.mostrar_carrito,
            state="disabled",
        )
        self.btn_ver_carrito.pack(ipady=5, fill=tk.X, pady=(5, 0))

    def crear_widgets_ventas(self):
        filter_frame = ttk.LabelFrame(
            self.ventas_tab, text="Filtros de Búsqueda", padding="10"
        )
        filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        analisis_frame = ttk.LabelFrame(
            self.ventas_tab, text="Totales de la Vista Actual", padding="10"
        )
        analisis_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        historial_frame = ttk.Frame(self.ventas_tab)
        historial_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

        # Contenedor para filtros en línea
        linea_1_filtros = ttk.Frame(filter_frame)
        linea_1_filtros.pack(fill=tk.X)
        linea_2_filtros = ttk.Frame(filter_frame)
        linea_2_filtros.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(linea_1_filtros, text="Desde:").pack(side=tk.LEFT, padx=(0, 5))
        if TKCALENDAR_AVAILABLE:
            self.filtro_fecha_desde = DateEntry(
                linea_1_filtros,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=2,
                date_pattern="y-mm-dd",
            )
            self.filtro_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
            self.filtro_fecha_desde.delete(0, "end")
        else:
            self.filtro_fecha_desde = ttk.Entry(linea_1_filtros)
            self.filtro_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(linea_1_filtros, text="Hasta:").pack(side=tk.LEFT, padx=(0, 5))
        if TKCALENDAR_AVAILABLE:
            self.filtro_fecha_hasta = DateEntry(
                linea_1_filtros,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=2,
                date_pattern="y-mm-dd",
            )
            self.filtro_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
            self.filtro_fecha_hasta.delete(0, "end")
        else:
            self.filtro_fecha_hasta = ttk.Entry(linea_1_filtros)
            self.filtro_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(linea_1_filtros, text="Descripción o ID Venta:").pack(
            side=tk.LEFT, padx=(10, 5)
        )
        self.filtro_desc_venta = ttk.Entry(linea_1_filtros, width=30)
        self.filtro_desc_venta.pack(side=tk.LEFT, padx=(0, 10))

        # --- NUEVO FILTRO DE PAGO ELECTRÓNICO ---
        self.filtro_pago_electronico_var = tk.BooleanVar()
        self.filtro_pago_electronico_chk = ttk.Checkbutton(
            linea_1_filtros,
            text="Mostrar solo pagos electrónicos",
            variable=self.filtro_pago_electronico_var,
            command=self.populate_sales_treeview,
        )
        self.filtro_pago_electronico_chk.pack(side=tk.LEFT, padx=15)

        ttk.Button(
            linea_2_filtros,
            text="Filtrar Ventas",
            command=self.populate_sales_treeview,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            linea_2_filtros,
            text="Mostrar Todo",
            command=self.limpiar_filtros_ventas,
        ).pack(side=tk.LEFT, padx=5)
        self.btn_ver_recibo = ttk.Button(
            linea_2_filtros,
            text="Ver Recibo (.txt)",
            command=self.abrir_recibo_txt,
            state="disabled",
        )
        self.btn_ver_recibo.pack(side=tk.LEFT, padx=10)

        self.lbl_total_items = ttk.Label(
            analisis_frame, text="Items Vendidos: 0", font=("Helvetica", 10, "bold")
        )
        self.lbl_total_items.pack(side=tk.LEFT, padx=20)
        self.lbl_costo_total = ttk.Label(
            analisis_frame, text="Costo Total: $0.00", font=("Helvetica", 10, "bold")
        )
        self.lbl_costo_total.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ventas = ttk.Label(
            analisis_frame, text="Total Ventas: $0.00", font=("Helvetica", 10, "bold")
        )
        self.lbl_total_ventas.pack(side=tk.LEFT, padx=20)
        self.lbl_total_ganancia = ttk.Label(
            analisis_frame, text="Ganancia Total: $0.00", font=("Helvetica", 10, "bold")
        )
        self.lbl_total_ganancia.pack(side=tk.LEFT, padx=20)

        columnas = (
            "Timestamp",
            "ID_Venta",
            "Item",
            "Cantidad",
            "CostoU",
            "PrecioU",
            "Total",
            "Ganancia",
            "Origen",
            "Cliente",
            "MedioPago",
        )
        self.sales_tree = ttk.Treeview(
            historial_frame, columns=columnas, show="headings"
        )
        for col in columnas:
            self.sales_tree.heading(
                col,
                text=col.replace("_", " "),
                command=lambda _col=col: self.sort_sales_by_column(_col),
            )

        for col in columnas:
            self.sales_tree.column(col, anchor=tk.W, width=90)
        self.sales_tree.column("Timestamp", width=140)
        self.sales_tree.column("Item", width=250)
        scrollbar_s = ttk.Scrollbar(
            historial_frame, orient=tk.VERTICAL, command=self.sales_tree.yview
        )
        self.sales_tree.configure(yscrollcommand=scrollbar_s.set)
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_s.pack(side=tk.RIGHT, fill=tk.Y)
        self.sales_tree.bind("<<TreeviewSelect>>", self.on_sale_select)

    def sort_sales_by_column(self, col):
        """Función para ordenar la tabla de ventas al hacer clic en un encabezado."""
        data = [
            (self.sales_tree.set(child, col), child)
            for child in self.sales_tree.get_children("")
        ]

        # Determinar el tipo de dato para ordenar correctamente
        column_index = self.sales_tree["columns"].index(col)
        # Columnas numéricas: 3 (Cantidad) y 4 a 7 (valores monetarios)
        numeric_columns = [3, 4, 5, 6, 7]

        try:
            if column_index in numeric_columns:
                # Ordenar como números flotantes
                data.sort(
                    key=lambda t: float(t[0]), reverse=self.sales_last_sort_reverse
                )
            elif column_index == 0:  # Timestamp
                data.sort(
                    key=lambda t: datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S"),
                    reverse=self.sales_last_sort_reverse,
                )
            else:
                # Ordenar como texto (insensible a mayúsculas/minúsculas)
                data.sort(
                    key=lambda t: t[0].lower(), reverse=self.sales_last_sort_reverse
                )
        except (ValueError, IndexError):
            # Si hay un error de conversión (ej. celda vacía), ordenar como texto
            data.sort(key=lambda t: t[0].lower(), reverse=self.sales_last_sort_reverse)

        for index, (val, child) in enumerate(data):
            self.sales_tree.move(child, "", index)

        # Invertir la dirección del orden para el próximo clic
        self.sales_last_sort_reverse = not self.sales_last_sort_reverse

    def actualizar_estado_botones_venta(self):
        """Habilita o deshabilita el botón de venta según el archivo de inventario actual."""
        es_local = os.path.basename(self.gestor.archivo_inventario) == "local.txt"
        estado = "normal" if es_local else "disabled"
        # Se usa hasattr para evitar errores si el botón aún no ha sido creado.
        if hasattr(self, "btn_agregar_venta"):
            self.btn_agregar_venta.config(state=estado)

    # --- Widgets de Cuadre de Caja ---
    def crear_widgets_caja(self):
        main_frame = ttk.Frame(self.caja_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        inicio_frame = ttk.LabelFrame(left_frame, text="1. Inicio del Día", padding=10)
        inicio_frame.pack(fill=tk.X, pady=5)
        ttk.Label(inicio_frame, text="Dinero Inicial (Vueltos):").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.caja_inicial_entry = ttk.Entry(inicio_frame)
        self.caja_inicial_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(inicio_frame, text="Base:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.caja_base_entry = ttk.Entry(inicio_frame)
        self.caja_base_entry.grid(row=1, column=1, padx=5, pady=5)
        self.btn_iniciar_dia = ttk.Button(
            inicio_frame, text="Iniciar Día", command=self.iniciar_dia
        )
        self.btn_iniciar_dia.grid(row=2, column=0, columnspan=2, pady=10)

        movimientos_frame = ttk.LabelFrame(
            left_frame, text="2. Movimientos de Caja (No Ventas)", padding=10
        )
        movimientos_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(movimientos_frame, text="Tipo:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.mov_tipo_combo = ttk.Combobox(
            movimientos_frame,
            values=["Gasto", "Préstamo/Retiro", "Abono/Ingreso"],
            state="readonly",
        )
        self.mov_tipo_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(movimientos_frame, text="Descripción:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.mov_desc_entry = ttk.Entry(movimientos_frame)
        self.mov_desc_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(movimientos_frame, text="Monto:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        self.mov_monto_entry = ttk.Entry(movimientos_frame)
        self.mov_monto_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.btn_registrar_mov = ttk.Button(
            movimientos_frame,
            text="Registrar Movimiento",
            command=self.registrar_movimiento,
        )
        self.btn_registrar_mov.grid(row=3, column=0, columnspan=2, pady=10)

        self.mov_tree = ttk.Treeview(
            movimientos_frame,
            columns=("Tipo", "Desc", "Monto"),
            show="headings",
            height=5,
        )
        self.mov_tree.heading("Tipo", text="Tipo")
        self.mov_tree.heading("Desc", text="Descripción")
        self.mov_tree.heading("Monto", text="Monto")
        self.mov_tree.column("Tipo", width=100)
        self.mov_tree.column("Desc", width=200)
        self.mov_tree.column("Monto", width=80, anchor=tk.E)
        self.mov_tree.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        movimientos_frame.rowconfigure(4, weight=1)
        movimientos_frame.columnconfigure(1, weight=1)

        cierre_frame = ttk.LabelFrame(right_frame, text="3. Cierre del Día", padding=10)
        cierre_frame.pack(fill=tk.X, pady=5)
        ttk.Label(cierre_frame, text="Total Pagos Electrónicos:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.pagos_electronicos_entry = ttk.Entry(cierre_frame)
        self.pagos_electronicos_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(cierre_frame, text="Dinero Real Contado en Caja:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        dinero_real_frame = ttk.Frame(cierre_frame)
        dinero_real_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.dinero_real_entry = ttk.Entry(dinero_real_frame, state="readonly")
        self.dinero_real_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(
            dinero_real_frame, text="Contar...", command=self.abrir_ventana_conteo_caja
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(
            dinero_real_frame, text="Historial", command=self.ver_historial_conteos
        ).pack(side=tk.LEFT, padx=(5, 0))

        btn_cierre_frame = ttk.Frame(cierre_frame)
        btn_cierre_frame.grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_cuadre_parcial = ttk.Button(
            btn_cierre_frame,
            text="Calcular Cuadre Parcial",
            command=self.calcular_cuadre_parcial,
        )
        self.btn_cuadre_parcial.pack(side=tk.LEFT, padx=5)
        self.btn_cerrar_caja = ttk.Button(
            btn_cierre_frame,
            text="Cerrar Caja y Guardar",
            command=self.realizar_cuadre_final,
        )
        self.btn_cerrar_caja.pack(side=tk.LEFT, padx=5)

        resumen_frame = ttk.LabelFrame(
            right_frame, text="4. Resumen del Cuadre", padding=10
        )
        resumen_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.resumen_labels = {}
        labels_info = {
            "Total Ventas del Día:": "total_ventas",
            "Total Otros Movimientos:": "total_movimientos",
            "Efectivo Esperado en Caja:": "efectivo_esperado",
            "Dinero Real en Caja:": "dinero_real_caja",
            "Diferencia (Sobrante/Faltante):": "diferencia",
        }

        row_idx = 0
        for label_text, key in labels_info.items():
            ttk.Label(resumen_frame, text=label_text, font=("Helvetica", 10)).grid(
                row=row_idx, column=0, sticky="w", padx=5, pady=3
            )
            label_var = tk.StringVar(value="$0.00")
            label_widget = ttk.Label(
                resumen_frame, textvariable=label_var, font=("Helvetica", 10, "bold")
            )
            label_widget.grid(row=row_idx, column=1, sticky="e", padx=5, pady=3)
            self.resumen_labels[key] = {"var": label_var, "widget": label_widget}
            row_idx += 1

        resumen_frame.columnconfigure(1, weight=1)

    # --- Lógica de Cuadre de Caja ---
    def abrir_ventana_conteo_caja(self):
        win_conteo = tk.Toplevel(self.master)
        win_conteo.title("Conteo de Dinero Físico")
        win_conteo.grab_set()
        win_conteo.resizable(False, False)

        main_frame = ttk.Frame(win_conteo, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        denominaciones_billetes = {
            100000: "Billetes de $100.000:",
            50000: "Billetes de $50.000:",
            20000: "Billetes de $20.000:",
            10000: "Billetes de $10.000:",
            5000: "Billetes de $5.000:",
            2000: "Billetes de $2.000:",
            1000: "Billetes de $1.000:",
        }

        entries = {}
        subtotal_labels = {}

        def actualizar_totales(event=None):
            total = 0
            for value, label_text in denominaciones_billetes.items():
                try:
                    cantidad = int(entries[value].get() or 0)
                    subtotal = cantidad * value
                    subtotal_labels[value].config(text=f"= ${subtotal:,.0f}")
                    total += subtotal
                except (ValueError, KeyError):
                    subtotal_labels[value].config(text="= $0")

            try:
                total_monedas = float(entries["monedas"].get() or 0)
                total += total_monedas
            except (ValueError, KeyError):
                pass

            total_general_label.config(text=f"Total: ${total:,.0f}")
            return total

        row = 0
        for value, label_text in denominaciones_billetes.items():
            ttk.Label(main_frame, text=label_text).grid(
                row=row, column=0, sticky="w", pady=4
            )
            entry = ttk.Entry(main_frame, width=8, justify="right")
            entry.grid(row=row, column=1, pady=4)
            entry.bind("<KeyRelease>", actualizar_totales)
            entries[value] = entry

            sub_label = ttk.Label(main_frame, text="= $0", width=15)
            sub_label.grid(row=row, column=2, sticky="w", padx=5)
            subtotal_labels[value] = sub_label
            row += 1

        ttk.Separator(main_frame).grid(row=row, columnspan=3, sticky="ew", pady=5)
        row += 1

        ttk.Label(main_frame, text="Total en Monedas:").grid(
            row=row, column=0, sticky="w", pady=4
        )
        monedas_entry = ttk.Entry(main_frame, width=15, justify="right")
        monedas_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        monedas_entry.bind("<KeyRelease>", actualizar_totales)
        entries["monedas"] = monedas_entry
        row += 1

        ttk.Separator(main_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=3, pady=10, sticky="ew"
        )
        row += 1

        total_general_label = ttk.Label(
            main_frame, text="Total: $0", font=("Helvetica", 14, "bold")
        )
        total_general_label.grid(row=row, column=0, columnspan=3, pady=5)
        row += 1

        # Poblar con valores guardados en la sesión
        for value, entry in entries.items():
            if value in self.conteo_actual_caja:
                entry.insert(0, self.conteo_actual_caja[value])
        actualizar_totales()

        def guardar_y_cerrar():
            try:
                # Diccionarios para guardar los datos
                self.conteo_actual_caja.clear()
                detalle_dict = {}
                total_final = 0.0

                # --- LÓGICA CORREGIDA Y ROBUSTA ---
                # 1. Procesar billetes, validando cada entrada
                for value, entry in entries.items():
                    if value == "monedas":
                        continue  # Procesar monedas por separado

                    cantidad_str = entry.get() or "0"
                    cantidad_num = int(
                        cantidad_str
                    )  # Esto lanzará ValueError si la entrada es inválida

                    self.conteo_actual_caja[value] = cantidad_str
                    if cantidad_num > 0:
                        detalle_dict[value] = cantidad_num
                    total_final += cantidad_num * value

                # 2. Procesar monedas, validando la entrada
                monedas_str = entries["monedas"].get() or "0"
                monedas_num = float(
                    monedas_str
                )  # Esto lanzará ValueError si la entrada es inválida

                self.conteo_actual_caja["monedas"] = monedas_str
                if monedas_num > 0:
                    detalle_dict["monedas"] = monedas_num
                total_final += monedas_num

                # 3. Formatear el string de detalles para el historial
                detalle_str = ", ".join(
                    [
                        f"${k:,.0f}: {v}" if k != "monedas" else f"Monedas: ${v:,.2f}"
                        for k, v in detalle_dict.items()
                    ]
                )

                # 4. Guardar en el archivo de historial
                self.gestor_caja.guardar_conteo_historial(total_final, detalle_str)

                # 5. Actualizar el campo en la ventana principal
                self.dinero_real_entry.config(state="normal")
                self.dinero_real_entry.delete(0, tk.END)
                self.dinero_real_entry.insert(0, f"{total_final:.2f}")
                self.dinero_real_entry.config(state="readonly")

                # 6. Cerrar la ventana de conteo
                win_conteo.destroy()

            except ValueError:
                # 7. Si cualquier conversión a número falla, mostrar este error
                messagebox.showerror(
                    "Error de Entrada",
                    "Por favor, ingrese solo números en los campos de conteo.\nNo use puntos, comas o símbolos.",
                    parent=win_conteo,
                )

        ttk.Button(main_frame, text="Guardar Conteo", command=guardar_y_cerrar).grid(
            row=row, column=0, columnspan=3, pady=10, ipady=5
        )

    def ver_historial_conteos(self):
        win_hist = tk.Toplevel(self.master)
        win_hist.title("Historial de Conteos de Caja")
        win_hist.geometry("700x450")
        win_hist.grab_set()

        frame = ttk.Frame(win_hist, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(
            frame, columns=("Timestamp", "Total", "Detalle"), show="headings"
        )
        tree.heading("Timestamp", text="Fecha y Hora")
        tree.heading("Total", text="Total Contado")
        tree.heading("Detalle", text="Detalle del Conteo")
        tree.column("Timestamp", width=150, anchor=tk.W)
        tree.column("Total", width=120, anchor=tk.E)
        tree.column("Detalle", width=400, anchor=tk.W)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        historial = self.gestor_caja.obtener_historial_conteos()
        for row in reversed(historial):  # Mostrar el más reciente primero
            try:
                if len(row) >= 3:
                    total_formateado = f"${float(row[1]):,.2f}"
                    tree.insert("", tk.END, values=(row[0], total_formateado, row[2]))
            except (ValueError, IndexError):
                continue

    def cargar_estado_caja(self):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        datos_dia = self.gestor_caja.obtener_datos_dia(fecha_hoy)

        if datos_dia:
            self.caja_inicial_entry.insert(0, datos_dia["DineroInicial"])
            self.caja_base_entry.insert(0, datos_dia["Base"])
            self.caja_inicial_entry.config(state="disabled")
            self.caja_base_entry.config(state="disabled")
            self.btn_iniciar_dia.config(state="disabled")
            self.cargar_movimientos_hoy()
        else:
            self.btn_registrar_mov.config(state="disabled")
            self.btn_cerrar_caja.config(state="disabled")
            self.btn_cuadre_parcial.config(state="disabled")

    def iniciar_dia(self):
        try:
            dinero_inicial = float(self.caja_inicial_entry.get())
            base = float(self.caja_base_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Dinero inicial y base deben ser números.")
            return

        success, msg = self.gestor_caja.iniciar_dia(dinero_inicial, base)
        if success:
            self.conteo_actual_caja.clear()  # Limpiar conteo al iniciar nuevo día
            messagebox.showinfo("Éxito", msg)
            self.caja_inicial_entry.config(state="disabled")
            self.caja_base_entry.config(state="disabled")
            self.btn_iniciar_dia.config(state="disabled")
            self.btn_registrar_mov.config(state="normal")
            self.btn_cerrar_caja.config(state="normal")
            self.btn_cuadre_parcial.config(state="normal")
        else:
            messagebox.showerror("Error", msg)

    def registrar_movimiento(self):
        tipo = self.mov_tipo_combo.get()
        desc = self.mov_desc_entry.get()
        monto = self.mov_monto_entry.get()

        if not all([tipo, desc, monto]):
            messagebox.showerror(
                "Error", "Todos los campos de movimiento son obligatorios."
            )
            return

        success, msg = self.gestor_caja.registrar_movimiento(tipo, desc, monto)
        if success:
            self.mov_desc_entry.delete(0, tk.END)
            self.mov_monto_entry.delete(0, tk.END)
            self.cargar_movimientos_hoy()
        else:
            messagebox.showerror("Error", msg)

    def cargar_movimientos_hoy(self):
        for i in self.mov_tree.get_children():
            self.mov_tree.delete(i)

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        movimientos = self.gestor_caja.obtener_movimientos_dia(fecha_hoy)

        for mov in movimientos:
            monto = float(mov["Monto"])
            self.mov_tree.insert(
                "", tk.END, values=(mov["Tipo"], mov["Descripcion"], f"${monto:,.2f}")
            )

    def _ejecutar_logica_cuadre(self):
        try:
            # El dinero real sigue viniendo del conteo manual
            dinero_real = float(self.dinero_real_entry.get() or 0)
        except ValueError:
            messagebox.showerror(
                "Error", "El valor de dinero real en caja debe ser un número."
            )
            return None

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

        # --- CAMBIO CLAVE: Recalcular totales desde los registros para mayor precisión ---
        total_ventas_dia = self.gestor.obtener_ventas_del_dia(fecha_hoy)
        pagos_electronicos = self.gestor.obtener_pagos_electronicos_del_dia(fecha_hoy)

        # Actualizar la GUI con el valor recalculado y ponerlo como solo lectura
        self.pagos_electronicos_entry.config(state="normal")
        self.pagos_electronicos_entry.delete(0, tk.END)
        self.pagos_electronicos_entry.insert(0, f"{pagos_electronicos:.2f}")
        self.pagos_electronicos_entry.config(state="readonly")
        # --- FIN DEL CAMBIO ---

        resumen, msg = self.gestor_caja.calcular_cuadre(
            fecha_hoy, pagos_electronicos, dinero_real, total_ventas_dia
        )

        if resumen:
            self.resumen_labels["total_ventas"]["var"].set(
                f"${resumen['total_ventas']:,.2f}"
            )
            self.resumen_labels["total_movimientos"]["var"].set(
                f"${resumen['total_movimientos']:,.2f}"
            )
            self.resumen_labels["efectivo_esperado"]["var"].set(
                f"${resumen['efectivo_esperado']:,.2f}"
            )
            self.resumen_labels["dinero_real_caja"]["var"].set(
                f"${resumen['dinero_real_caja']:,.2f}"
            )

            diferencia = resumen["diferencia"]
            self.resumen_labels["diferencia"]["var"].set(f"${diferencia:,.2f}")

            resumen_widget = self.resumen_labels["diferencia"]["widget"]
            if diferencia < 0:
                resumen_widget.config(foreground="red")
            elif diferencia > 0:
                resumen_widget.config(foreground="green")
            else:
                resumen_widget.config(foreground="black")

            return resumen
        else:
            messagebox.showerror("Error", msg)
            return None

    def calcular_cuadre_parcial(self):
        self._ejecutar_logica_cuadre()

    def realizar_cuadre_final(self):
        resumen = self._ejecutar_logica_cuadre()
        if resumen:
            if messagebox.askyesno(
                "Confirmar Cierre",
                "¿Está seguro de que desea cerrar la caja y guardar los resultados? Esta acción no se puede deshacer.",
            ):
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                success, msg = self.gestor_caja.cerrar_dia(fecha_hoy, resumen)
                if success:
                    messagebox.showinfo("Éxito", msg)
                    self.btn_cerrar_caja.config(state="disabled")
                    self.btn_cuadre_parcial.config(state="disabled")
                    self.btn_registrar_mov.config(state="disabled")
                else:
                    messagebox.showerror("Error al Guardar", msg)

    # --- Resto de métodos de la GUI ---
    def populate_inventory_treeview(self):
        for i in self.inventory_tree.get_children():
            self.inventory_tree.delete(i)
        datos, errores = self.gestor.leer_datos()
        if errores:
            messagebox.showwarning("Aviso", "\n".join(errores))
        palabra_clave = self.filtro_palabra_entry.get()
        operador = self.filtro_op_combo.get()
        cant_str = self.filtro_cant_entry.get()
        if palabra_clave == "Palabra clave...":
            palabra_clave = ""
        cant_filtro = None
        if operador and cant_str:
            try:
                cant_filtro = int(cant_str)
            except ValueError:
                messagebox.showerror("Error", "Cantidad de filtro debe ser un número.")
                return
        count = 0
        for linea_num, desc, cant in datos:
            mostrar = True
            if palabra_clave and palabra_clave.lower() not in desc.lower():
                mostrar = False
            if mostrar and cant_filtro is not None:
                if (
                    (operador == ">" and not cant > cant_filtro)
                    or (operador == "<" and not cant < cant_filtro)
                    or (operador == "=" and not cant == cant_filtro)
                ):
                    mostrar = False
            if mostrar:
                self.inventory_tree.insert("", tk.END, values=(linea_num, desc, cant))
                count += 1
        self.status_label_inv.config(text=f"Mostrando {count} de {len(datos)} ítems.")

    def populate_sales_treeview(self):
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        historial = self.gestor.leer_historial_ventas()

        desde_str = self.filtro_fecha_desde.get()
        hasta_str = self.filtro_fecha_hasta.get()
        filtro_texto = self.filtro_desc_venta.get().lower()
        mostrar_solo_electronicos = self.filtro_pago_electronico_var.get()

        total_items, costo_total, total_ventas, total_ganancia = 0, 0.0, 0.0, 0.0

        for venta_original in historial:
            venta = list(venta_original)
            if len(venta) < 8:
                continue
            if len(venta) == 8:
                venta.insert(1, "N/A")
                venta.append("N/A")
            elif len(venta) == 9:
                venta.insert(1, "N/A")
            if len(venta) == 10:
                venta.append("N/A")
            if len(venta) != 11:
                continue

            fecha_valida = True
            if desde_str or hasta_str:
                try:
                    fecha_venta = datetime.strptime(
                        venta[0], "%Y-%m-%d %H:%M:%S"
                    ).date()
                    if (
                        desde_str
                        and fecha_venta
                        < datetime.strptime(desde_str, "%Y-%m-%d").date()
                    ):
                        fecha_valida = False
                    if (
                        hasta_str
                        and fecha_venta
                        > datetime.strptime(hasta_str, "%Y-%m-%d").date()
                    ):
                        fecha_valida = False
                except (ValueError, IndexError):
                    fecha_valida = False
            if not fecha_valida:
                continue

            id_venta_csv = venta[1].lower()
            desc_csv = venta[2].lower()
            if filtro_texto and not (
                filtro_texto in desc_csv or filtro_texto in id_venta_csv
            ):
                continue

            if mostrar_solo_electronicos:
                medio_pago = venta[10]
                pagos = medio_pago.split(", ")
                es_electronico = any("Efectivo" not in p for p in pagos if p.strip())
                if not es_electronico:
                    continue

            try:
                total_items += int(venta[3])
                costo_total += int(venta[3]) * float(venta[4])
                total_ventas += float(venta[6])
                total_ganancia += float(venta[7])
                self.sales_tree.insert("", tk.END, values=tuple(venta))
            except (ValueError, IndexError):
                continue

        self.lbl_total_items.config(text=f"Items Vendidos: {total_items}")
        self.lbl_costo_total.config(text=f"Costo Total: ${costo_total:.2f}")
        self.lbl_total_ventas.config(text=f"Total Ventas: ${total_ventas:.2f}")
        self.lbl_total_ganancia.config(text=f"Ganancia Total: ${total_ganancia:.2f}")

    def limpiar_filtros(self):
        self.filtro_palabra_entry.delete(0, tk.END)
        self.add_placeholder(None)
        self.filtro_op_combo.set("")
        self.filtro_cant_entry.delete(0, tk.END)
        self.populate_inventory_treeview()

    def limpiar_filtros_ventas(self):
        self.filtro_fecha_desde.delete(0, tk.END)
        self.filtro_fecha_hasta.delete(0, tk.END)
        self.filtro_desc_venta.delete(0, tk.END)
        self.filtro_pago_electronico_var.set(False)
        self.populate_sales_treeview()

    def _get_selected_item_values(self):
        selected = self.inventory_tree.focus()
        if not selected:
            messagebox.showwarning(
                "Sin Selección", "Por favor, seleccione un ítem de la lista."
            )
            return None
        return self.inventory_tree.item(selected, "values")

    def agregar_item(self):
        win_add = tk.Toplevel(self.master)
        win_add.title("Agregar Nuevo Ítem")
        win_add.grab_set()
        win_add.resizable(False, False)
        frame = ttk.Frame(win_add, padding="10")
        frame.pack()
        ttk.Label(frame, text="Descripción:").grid(
            row=0, column=0, sticky="w", pady=2, padx=5
        )
        desc_entry = ttk.Entry(frame, width=40)
        desc_entry.grid(row=0, column=1, pady=2, padx=5)
        ttk.Label(frame, text="Cantidad Inicial:").grid(
            row=1, column=0, sticky="w", pady=2, padx=5
        )
        cant_entry = ttk.Entry(frame, width=15)
        cant_entry.grid(row=1, column=1, sticky="w", pady=2, padx=5)

        def do_add():
            desc = desc_entry.get().strip()
            cant = cant_entry.get().strip()
            if not desc or not cant:
                messagebox.showerror(
                    "Error", "Ambos campos son obligatorios.", parent=win_add
                )
                return
            success, message = self.gestor.agregar_linea(desc, cant)
            if success:
                self.populate_inventory_treeview()
                win_add.destroy()
                messagebox.showinfo("Éxito", message)
            else:
                messagebox.showerror("Error", message, parent=win_add)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Guardar Ítem", command=do_add).pack()
        desc_entry.focus_set()

    def modificar_item(self):
        values = self._get_selected_item_values()
        if not values:
            return
        linea, desc, cant = values
        win_mod = tk.Toplevel(self.master)
        win_mod.title("Modificar Ítem")
        win_mod.grab_set()
        win_mod.resizable(False, False)
        frame = ttk.Frame(win_mod, padding="10")
        frame.pack()
        ttk.Label(frame, text="Descripción:").grid(
            row=0, column=0, sticky="w", pady=2, padx=5
        )
        desc_entry = ttk.Entry(frame, width=40)
        desc_entry.grid(row=0, column=1, pady=2, padx=5)
        desc_entry.insert(0, desc)
        ttk.Label(frame, text="Cantidad:").grid(
            row=1, column=0, sticky="w", pady=2, padx=5
        )
        cant_entry = ttk.Entry(frame, width=15)
        cant_entry.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        cant_entry.insert(0, cant)

        def do_mod():
            nueva_desc = desc_entry.get().strip()
            nueva_cant = cant_entry.get().strip()
            if not nueva_desc or not nueva_cant:
                messagebox.showerror(
                    "Error", "Ambos campos son obligatorios.", parent=win_mod
                )
                return
            success, message = self.gestor.modificar_linea(
                int(linea), nueva_desc, nueva_cant
            )
            if success:
                self.populate_inventory_treeview()
                win_mod.destroy()
                messagebox.showinfo("Éxito", message)
            else:
                messagebox.showerror("Error", message, parent=win_mod)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Guardar Cambios", command=do_mod).pack()
        desc_entry.focus_set()

    def eliminar_item(self):
        values = self._get_selected_item_values()
        if not values:
            return
        linea, desc, cant = values
        if messagebox.askyesno("Confirmar", f"¿Eliminar este ítem?\n\n{desc}"):
            success, msg = self.gestor.eliminar_linea(int(linea))
            if success:
                self.populate_inventory_treeview()
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)

    def ajustar_cantidad(self, sumar):
        values = self._get_selected_item_values()
        if not values:
            return
        linea, desc, cant_actual_str = values
        accion = "sumar" if sumar else "restar"
        try:
            cambio = simpledialog.askinteger(
                "Ajustar Stock",
                f"Cantidad a {accion} para:\n{desc}",
                parent=self.master,
                minvalue=1,
            )
            if cambio is not None:
                if sumar:
                    success, msg = self.gestor.modificar_cantidad(int(linea), cambio)
                    if success:
                        messagebox.showinfo("Éxito", msg)
                    else:
                        messagebox.showerror("Error", msg)
                else:  # Restar y transferir
                    if cambio > int(cant_actual_str):
                        messagebox.showerror(
                            "Error", "No se puede restar más stock del que existe."
                        )
                        return
                    success, msg = self.gestor.modificar_cantidad(int(linea), -cambio)
                    if success:
                        success_local, msg_local = self.gestor.transferir_a_local(
                            desc, cambio
                        )
                        if success_local:
                            messagebox.showinfo(
                                "Operación Completa",
                                f"{msg}\n{cambio} unidad(es) transferida(s) a 'local.txt'.",
                            )
                        else:
                            messagebox.showwarning(
                                "Error de Transferencia",
                                f"{msg}\nPero hubo un error al transferir a 'local.txt':\n{msg_local}",
                            )
                    else:
                        messagebox.showerror("Error", msg)
                self.populate_inventory_treeview()
        except ValueError:
            messagebox.showerror("Error", "Debe ser un número.")

    def ordenar_alfabeticamente(self):
        if messagebox.askyesno(
            "Confirmar", "¿Desea ordenar el inventario alfabéticamente?"
        ):
            success, msg = self.gestor.ordenar_alfabeticamente()
            if success:
                self.populate_inventory_treeview()
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)

    def verificar_formato(self):
        errores = self.gestor.verificar_formato()
        if not errores:
            messagebox.showinfo(
                "Verificación", "¡El formato de todas las líneas es correcto!"
            )
        else:
            messagebox.showwarning(
                "Verificación",
                "Líneas con formato incorrecto:\n\n" + "\n".join(errores),
            )

    def agregar_a_venta(self):
        if os.path.basename(self.gestor.archivo_inventario) != "local.txt":
            messagebox.showerror(
                "Archivo Incorrecto para Venta",
                "Las ventas solo pueden realizarse desde el inventario 'local.txt'.\n\n"
                "Por favor, cambie al archivo 'local.txt' para proceder a vender.",
            )
            return
        values = self._get_selected_item_values()
        if not values:
            return
        linea_num, desc, stock_actual = values

        win_add_cart = tk.Toplevel(self.master)
        win_add_cart.title("Agregar Item a Venta")
        win_add_cart.grab_set()
        frame = ttk.Frame(win_add_cart, padding="15")
        frame.pack()

        ttk.Label(frame, text=f"Item: {desc}", font=("Helvetica", 11, "bold")).grid(
            row=0, columnspan=2, pady=(0, 10)
        )
        ttk.Label(frame, text=f"Stock Actual: {stock_actual}").grid(
            row=1, columnspan=2, pady=(0, 15)
        )

        ttk.Label(frame, text="Cantidad a Vender:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        cant_entry = ttk.Entry(frame, width=15)
        cant_entry.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Costo Unitario ($):").grid(
            row=3, column=0, sticky="w", pady=5
        )
        costo_entry = ttk.Entry(frame, width=15)
        costo_entry.grid(row=3, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Precio de Venta ($):").grid(
            row=4, column=0, sticky="w", pady=5
        )
        precio_entry = ttk.Entry(frame, width=15)
        precio_entry.grid(row=4, column=1, sticky="w", pady=5)

        def do_add_to_cart():
            try:
                cantidad = int(cant_entry.get())
                costo = float(costo_entry.get())
                precio = float(precio_entry.get())
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser positiva.")
                if cantidad > int(stock_actual):
                    messagebox.showerror(
                        "Stock Insuficiente",
                        "La cantidad a vender supera el stock actual.",
                        parent=win_add_cart,
                    )
                    return
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Datos Inválidos",
                    "Por favor, ingrese números válidos en todos los campos.",
                    parent=win_add_cart,
                )
                return

            item_data = {
                "linea_num": int(linea_num),
                "desc": desc,
                "stock_actual": int(stock_actual),
                "cantidad": cantidad,
                "costo": costo,
                "precio": precio,
            }
            self.carrito.append(item_data)
            self.actualizar_vista_carrito()
            win_add_cart.destroy()

        ttk.Button(frame, text="Agregar al Carrito", command=do_add_to_cart).grid(
            row=5, columnspan=2, pady=(20, 0)
        )
        cant_entry.focus_set()

    def actualizar_vista_carrito(self):
        num_items = len(self.carrito)
        self.btn_ver_carrito.config(text=f"Ver Carrito ({num_items})")
        self.btn_ver_carrito.config(state="normal" if num_items > 0 else "disabled")

    def mostrar_carrito(self):
        win_cart = tk.Toplevel(self.master)
        win_cart.title("Carrito de Venta y Pagos")
        win_cart.grab_set()
        win_cart.geometry("1050x650")
        win_cart.minsize(1000, 550)

        self.pagos_actuales = []
        total_general = sum(item["cantidad"] * item["precio"] for item in self.carrito)

        left_panel = ttk.Frame(win_cart, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_panel = ttk.Frame(win_cart, padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        tree_panel = ttk.Frame(left_panel)
        tree_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        client_panel = ttk.LabelFrame(
            left_panel, text="Datos del Cliente", padding="10"
        )
        client_panel.pack(fill=tk.X, pady=10)

        top_controls_frame = ttk.Frame(tree_panel)
        top_controls_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(
            top_controls_frame,
            text="Eliminar Item",
            command=lambda: eliminar_item_carrito(),
        ).pack(side=tk.LEFT)

        cart_tree = ttk.Treeview(
            tree_panel, columns=("Desc", "Cant", "PrecioU", "Subtotal"), show="headings"
        )
        cart_tree.heading("Desc", text="Descripción")
        cart_tree.heading("Cant", text="Cantidad")
        cart_tree.heading("PrecioU", text="Precio Unit.")
        cart_tree.heading("Subtotal", text="Subtotal")
        cart_tree.column("Desc", width=200)
        cart_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(
            tree_panel, orient=tk.VERTICAL, command=cart_tree.yview
        )
        cart_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(client_panel, text="Nombre:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        cliente_entry = ttk.Entry(client_panel, width=30)
        cliente_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(client_panel, text="Contacto (Opcional):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        cliente_contacto_entry = ttk.Entry(client_panel, width=30)
        cliente_contacto_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        client_panel.columnconfigure(1, weight=1)

        payment_frame = ttk.LabelFrame(right_panel, text="Añadir Pago", padding="10")
        payment_frame.pack(fill=tk.X)
        pagos_registrados_frame = ttk.LabelFrame(
            right_panel, text="Pagos Registrados", padding="10"
        )
        pagos_registrados_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        summary_frame = ttk.Frame(right_panel, padding="10")
        summary_frame.pack(fill=tk.X)

        ttk.Label(payment_frame, text="Método:").pack(fill=tk.X)
        payment_methods = [
            "Efectivo",
            "Nequi",
            "Bancolombia",
            "Daviplata",
            "Datafono",
            "Sistecredito",
        ]
        medio_pago_combo = ttk.Combobox(
            payment_frame, values=payment_methods, state="readonly"
        )
        medio_pago_combo.pack(fill=tk.X, pady=(0, 5))
        medio_pago_combo.set("Efectivo")
        ttk.Label(payment_frame, text="Monto $:").pack(fill=tk.X)
        monto_pago_entry = ttk.Entry(payment_frame)
        monto_pago_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(
            payment_frame, text="Agregar Pago", command=lambda: agregar_pago()
        ).pack()

        pagos_tree = ttk.Treeview(
            pagos_registrados_frame, columns=("Metodo", "Monto"), show="headings"
        )
        pagos_tree.heading("Metodo", text="Método")
        pagos_tree.heading("Monto", text="Monto")
        # --- AJUSTE: Ancho de columnas para estabilizar el panel ---
        pagos_tree.column("Metodo", width=120)
        pagos_tree.column("Monto", width=80, anchor=tk.E)
        # --- FIN DEL AJUSTE ---
        pagos_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar_pagos = ttk.Scrollbar(
            pagos_registrados_frame, orient=tk.VERTICAL, command=pagos_tree.yview
        )
        pagos_tree.configure(yscrollcommand=scrollbar_pagos.set)
        scrollbar_pagos.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(
            pagos_registrados_frame,
            text="X",
            command=lambda: eliminar_pago_registrado(),
            width=2,
        ).pack(side=tk.RIGHT, anchor="n")

        lbl_total_venta = ttk.Label(
            summary_frame,
            text=f"Total Venta: ${total_general:,.2f}",
            font=("Helvetica", 11, "bold"),
        )
        lbl_total_venta.pack(fill=tk.X, pady=2)
        lbl_total_pagado = ttk.Label(
            summary_frame,
            text="Total Pagado: $0.00",
            font=("Helvetica", 11, "bold"),
            foreground="blue",
        )
        lbl_total_pagado.pack(fill=tk.X, pady=2)
        lbl_faltante = ttk.Label(
            summary_frame,
            text=f"Faltante: ${total_general:,.2f}",
            font=("Helvetica", 12, "bold"),
            foreground="red",
        )
        lbl_faltante.pack(fill=tk.X, pady=2)

        style_confirm = ttk.Style()
        style_confirm.configure(
            "Confirm.TButton",
            foreground="white",
            background="navy",
            font=("Helvetica", 10, "bold"),
        )
        btn_confirmar = ttk.Button(
            summary_frame,
            text="CONFIRMAR VENTA",
            style="Confirm.TButton",
            command=lambda: finalizar_venta(),
            state="disabled",
        )
        btn_confirmar.pack(fill=tk.X, ipady=8, pady=(10, 0))

        def populate_cart_tree():
            for i in cart_tree.get_children():
                cart_tree.delete(i)
            for i, item in enumerate(self.carrito):
                subtotal = item["cantidad"] * item["precio"]
                cart_tree.insert(
                    "",
                    tk.END,
                    iid=i,
                    values=(
                        item["desc"],
                        item["cantidad"],
                        f"${item['precio']:.2f}",
                        f"${subtotal:.2f}",
                    ),
                )

        def actualizar_totales_pago():
            total_pagado = sum(pago["monto"] for pago in self.pagos_actuales)
            faltante = total_general - total_pagado
            lbl_total_pagado.config(text=f"Total Pagado: ${total_pagado:,.2f}")
            if faltante > 0:
                lbl_faltante.config(
                    text=f"Faltante: ${faltante:,.2f}", foreground="red"
                )
                btn_confirmar.config(state="disabled")
            else:
                lbl_faltante.config(
                    text=f"Cambio: ${-faltante:,.2f}", foreground="green"
                )
                btn_confirmar.config(state="normal")

        def populate_pagos_tree():
            for i in pagos_tree.get_children():
                pagos_tree.delete(i)
            for i, pago in enumerate(self.pagos_actuales):
                pagos_tree.insert(
                    "", tk.END, iid=i, values=(pago["metodo"], f"${pago['monto']:,.2f}")
                )
            actualizar_totales_pago()

        def agregar_pago():
            metodo = medio_pago_combo.get()
            try:
                monto = float(monto_pago_entry.get())
                if monto <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error", "El monto debe ser un número positivo.", parent=win_cart
                )
                return
            self.pagos_actuales.append({"metodo": metodo, "monto": monto})
            monto_pago_entry.delete(0, tk.END)
            populate_pagos_tree()

        def eliminar_pago_registrado():
            selected_iid = pagos_tree.focus()
            if not selected_iid:
                messagebox.showwarning(
                    "Sin Selección",
                    "Seleccione un pago para eliminar.",
                    parent=win_cart,
                )
                return
            del self.pagos_actuales[int(selected_iid)]
            populate_pagos_tree()

        populate_cart_tree()

        def eliminar_item_carrito():
            selected_iid = cart_tree.focus()
            if not selected_iid:
                messagebox.showwarning(
                    "Sin Selección",
                    "Seleccione un item del carrito para eliminar.",
                    parent=win_cart,
                )
                return
            del self.carrito[int(selected_iid)]
            nonlocal total_general
            total_general = sum(
                item["cantidad"] * item["precio"] for item in self.carrito
            )
            lbl_total_venta.config(text=f"Total Venta: ${total_general:,.2f}")
            populate_cart_tree()
            actualizar_totales_pago()
            self.actualizar_vista_carrito()

        def finalizar_venta():
            cliente = cliente_entry.get().strip() or "Cliente General"
            cliente_contacto = cliente_contacto_entry.get().strip()

            total_pagado = sum(p["monto"] for p in self.pagos_actuales)
            if total_pagado < total_general:
                messagebox.showerror(
                    "Pago Incompleto",
                    "El monto pagado es menor al total de la venta.",
                    parent=win_cart,
                )
                return
            if not self.carrito:
                messagebox.showerror(
                    "Carrito Vacío", "No hay items para vender.", parent=win_cart
                )
                return

            timestamp = datetime.now()
            id_venta = timestamp.strftime("%Y%m%d%H%M%S")

            medio_pago_str = ", ".join(
                [f"{p['metodo']}: ${p['monto']:.2f}" for p in self.pagos_actuales]
            )

            carrito_copia = list(self.carrito)

            for item in carrito_copia:
                success, msg = self.gestor.procesar_item_venta(
                    id_venta, timestamp, item, cliente, medio_pago_str
                )
                if not success:
                    messagebox.showerror("Error en Venta", msg, parent=win_cart)
                    self.populate_inventory_treeview()
                    return

            ruta_txt = self.gestor.generar_factura_consolidada_txt(
                id_venta,
                timestamp,
                carrito_copia,
                total_general,
                cliente,
                cliente_contacto,
                self.pagos_actuales,
            )

            total_electronico_venta = sum(
                p["monto"] for p in self.pagos_actuales if p["metodo"] != "Efectivo"
            )

            win_cart.destroy()
            self.show_output_options_dialog(
                ruta_txt,
                id_venta,
                timestamp,
                carrito_copia,
                total_general,
                cliente,
                cliente_contacto,
                self.pagos_actuales,
            )

            self.carrito.clear()
            self.actualizar_vista_carrito()
            self.populate_inventory_treeview()
            self.populate_sales_treeview()
            self.notebook.select(self.ventas_tab)

    def show_output_options_dialog(
        self,
        ruta_factura_txt,
        id_venta,
        timestamp,
        carrito,
        total_general,
        cliente,
        cliente_contacto,
        pagos,
    ):
        win_options = tk.Toplevel(self.master)
        win_options.title("Venta Exitosa")
        win_options.grab_set()
        frame = ttk.Frame(win_options, padding="20")
        frame.pack()
        ttk.Label(
            frame,
            text="Venta registrada con éxito.\n¿Qué desea hacer ahora?",
            justify=tk.CENTER,
            font=("Helvetica", 10),
        ).pack(pady=(0, 15))
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        def on_print():
            self.gestor.imprimir_factura_directo(ruta_factura_txt)
            win_options.destroy()

        def on_pdf():
            if not REPORTLAB_AVAILABLE:
                messagebox.showerror(
                    "Librería Faltante",
                    "Para generar PDF, necesita instalar 'reportlab'.\n\nAbra una terminal y ejecute:\npip install reportlab",
                    parent=win_options,
                )
                return
            try:
                pdf_path = self.gestor.generar_factura_consolidada_pdf(
                    id_venta,
                    timestamp,
                    carrito,
                    total_general,
                    cliente,
                    cliente_contacto,
                    pagos,
                )
                messagebox.showinfo(
                    "Éxito",
                    f"Factura guardada como PDF en:\n{pdf_path}",
                    parent=self.master,
                )
                win_options.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Error al crear PDF",
                    f"No se pudo generar el archivo PDF.\nError: {e}",
                    parent=win_options,
                )

        ttk.Button(btn_frame, text="Imprimir Recibo", command=on_print).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn_frame, text="Guardar como PDF", command=on_pdf).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(btn_frame, text="Finalizar", command=win_options.destroy).pack(
            side=tk.LEFT, padx=10
        )

    def cambiar_archivo_rapido(self, nombre_base):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        nuevo_archivo = os.path.join(script_dir, nombre_base)

        if os.path.exists(nuevo_archivo):
            mensaje = self.gestor.cambiar_archivo(nuevo_archivo)
            self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")
            self.populate_inventory_treeview()
            self.actualizar_estado_botones_venta()
            self.status_label_inv.config(text=f"Cargado: {nombre_base}")
        else:
            messagebox.showerror(
                "Archivo no Encontrado",
                f"No se pudo encontrar '{nuevo_archivo}'.\nAsegúrese de que esté en el mismo directorio que el script.",
            )

    def cambiar_archivo(self):
        nuevo_archivo = filedialog.askopenfilename(
            title="Seleccionar nuevo archivo de inventario",
            filetypes=(("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")),
        )
        if nuevo_archivo:
            mensaje = self.gestor.cambiar_archivo(nuevo_archivo)
            self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")
            self.populate_inventory_treeview()
            self.actualizar_estado_botones_venta()
            messagebox.showinfo("Éxito", mensaje)

    def clear_placeholder(self, event):
        if self.filtro_palabra_entry.get() == "Palabra clave...":
            self.filtro_palabra_entry.delete(0, tk.END)
            self.filtro_palabra_entry.config(foreground="black")

    def add_placeholder(self, event):
        if not self.filtro_palabra_entry.get():
            self.filtro_palabra_entry.insert(0, "Palabra clave...")
            self.filtro_palabra_entry.config(foreground="grey")

    def on_sale_select(self, event):
        if len(self.sales_tree.selection()) == 1:
            self.btn_ver_recibo.config(state="normal")
        else:
            self.btn_ver_recibo.config(state="disabled")

    def abrir_recibo_txt(self):
        if not self.sales_tree.selection():
            return

        selected_item = self.sales_tree.selection()[0]
        id_venta = self.sales_tree.item(selected_item, "values")[1]

        nombre_archivo = f"Factura_POS_{id_venta}.txt"
        ruta_archivo = os.path.join(self.gestor.directorio_facturas, nombre_archivo)

        if os.path.exists(ruta_archivo):
            try:
                current_os = platform.system()
                if current_os == "Windows":
                    os.startfile(ruta_archivo)
                elif current_os == "Darwin":  # macOS
                    subprocess.call(("open", ruta_archivo))
                else:  # Linux
                    subprocess.call(("xdg-open", ruta_archivo))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
        else:
            messagebox.showinfo(
                "No Encontrado",
                f"No se encontró el archivo de recibo:\n{nombre_archivo}\n\n(Es posible que sea de una venta anterior al sistema de recibos).",
            )


# ==============================================================================
# 4. BLOQUE DE EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()
