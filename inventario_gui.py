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
        ventas_procesadas = set()
        try:
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if not row or not row[0].startswith(fecha_str):
                        continue
                    try:
                        id_venta = row[1]
                        if id_venta in ventas_procesadas:
                            continue
                        medio_pago_str = row[10]
                        if ":" in medio_pago_str:
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
                        else:
                            if medio_pago_str.strip() not in ["Efectivo", "N/A", ""]:
                                total_venta_item = float(row[6])
                                total_electronico += total_venta_item
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
                next(reader, None)
                for row in reader:
                    if row and row[0].startswith(fecha_str):
                        try:
                            total_ventas += float(row[6])
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
        master.title("Gestor de Inventario y Ventas v4.3 - Carrito Integrado")
        master.geometry("1400x800")
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
        self.show_action_panel()  # Mostrar panel inicial

        self.sales_last_sort_col = None
        self.sales_last_sort_reverse = False

    def crear_widgets_inventario(self):
        top_frame = ttk.Frame(self.inventario_tab)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        filter_frame = ttk.Frame(self.inventario_tab)
        filter_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        content_pane = ttk.PanedWindow(self.inventario_tab, orient=tk.HORIZONTAL)
        content_pane.pack(fill=tk.BOTH, expand=True, pady=5)

        left_pane = ttk.Frame(content_pane)
        self.action_panel = ttk.LabelFrame(
            content_pane, text="Panel de Acciones", width=400
        )

        content_pane.add(left_pane, weight=3)
        content_pane.add(self.action_panel, weight=1)

        action_frame_bottom = ttk.Frame(self.inventario_tab)
        action_frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        self.lbl_archivo = ttk.Label(
            top_frame, text=f"Archivo: {self.gestor.archivo_inventario}"
        )
        self.lbl_archivo.pack(side=tk.LEFT, padx=5)
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
        self.status_label_inv = ttk.Label(top_frame, text="Listo.", anchor=tk.E)
        self.status_label_inv.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)

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
            left_pane, columns=("Linea", "Item", "Cantidad"), show="headings"
        )
        self.inventory_tree.heading("Linea", text="Línea")
        self.inventory_tree.heading("Item", text="Item")
        self.inventory_tree.heading("Cantidad", text="Cantidad en Stock")
        self.inventory_tree.column("Linea", width=60, anchor=tk.CENTER)
        self.inventory_tree.column("Item", width=500)
        self.inventory_tree.column("Cantidad", width=120, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(
            left_pane, orient=tk.VERTICAL, command=self.inventory_tree.yview
        )
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inventory_tree.bind("<<TreeviewSelect>>", self.on_inventory_select)

        self._build_action_panels()

        stock_group = ttk.LabelFrame(action_frame_bottom, text="Stock")
        stock_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(
            stock_group, text="Sumar/Restar Unidades", command=self.show_adjust_panel
        ).pack(pady=2, padx=5)

        item_group = ttk.LabelFrame(action_frame_bottom, text="Ítems")
        item_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(item_group, text="Agregar Nuevo", command=self.show_add_panel).pack(
            pady=2, padx=5
        )
        ttk.Button(
            item_group, text="Modificar Seleccionado", command=self.show_modify_panel
        ).pack(pady=2, padx=5)
        ttk.Button(
            item_group, text="Eliminar Seleccionado", command=self.eliminar_item
        ).pack(pady=2, padx=5)

        tools_group = ttk.LabelFrame(action_frame_bottom, text="Herramientas")
        tools_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(
            tools_group,
            text="Ordenar Alfabéticamente",
            command=self.ordenar_alfabeticamente,
        ).pack(pady=2, padx=5)
        ttk.Button(
            tools_group, text="Verificar Formato", command=self.verificar_formato
        ).pack(pady=2, padx=5)

        venta_group = ttk.Frame(action_frame_bottom)
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
            command=self.show_sale_panel,
            style="Add.TButton",
        )
        self.btn_agregar_venta.pack(ipady=5, fill=tk.X)
        self.btn_ver_carrito = ttk.Button(
            venta_group,
            text="Ver Carrito (0)",
            command=self.show_cart_panel,
            state="disabled",
        )
        self.btn_ver_carrito.pack(ipady=5, fill=tk.X, pady=(5, 0))

    def _build_action_panels(self):
        self.placeholder_panel = ttk.Frame(self.action_panel, padding=10)
        ttk.Label(
            self.placeholder_panel,
            text="Seleccione un ítem o una acción.",
            justify=tk.CENTER,
            wraplength=250,
        ).pack(pady=20)

        self.add_panel = ttk.Frame(self.action_panel, padding=10)
        self.modify_panel = ttk.Frame(self.action_panel, padding=10)
        self.adjust_panel = ttk.Frame(self.action_panel, padding=10)
        self.sale_panel = ttk.Frame(self.action_panel, padding=10)
        self.cart_panel = ttk.Frame(self.action_panel, padding=10)
        self.all_panels = [
            self.placeholder_panel,
            self.add_panel,
            self.modify_panel,
            self.adjust_panel,
            self.sale_panel,
            self.cart_panel,
        ]

        # Build Add Panel
        ttk.Label(self.add_panel, text="Descripción:").pack(fill=tk.X)
        self.add_desc_entry = ttk.Entry(self.add_panel)
        self.add_desc_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(self.add_panel, text="Cantidad Inicial:").pack(fill=tk.X)
        self.add_cant_entry = ttk.Entry(self.add_panel)
        self.add_cant_entry.pack(fill=tk.X, pady=(0, 10))
        btn_frame_add = ttk.Frame(self.add_panel)
        btn_frame_add.pack(fill=tk.X)
        ttk.Button(btn_frame_add, text="Guardar", command=self._do_add_from_panel).pack(
            side=tk.LEFT, expand=True
        )
        ttk.Button(btn_frame_add, text="Cancelar", command=self.show_action_panel).pack(
            side=tk.LEFT, expand=True
        )

        # Build Modify Panel
        ttk.Label(self.modify_panel, text="Descripción:").pack(fill=tk.X)
        self.modify_desc_entry = ttk.Entry(self.modify_panel)
        self.modify_desc_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(self.modify_panel, text="Cantidad:").pack(fill=tk.X)
        self.modify_cant_entry = ttk.Entry(self.modify_panel)
        self.modify_cant_entry.pack(fill=tk.X, pady=(0, 10))
        btn_frame_mod = ttk.Frame(self.modify_panel)
        btn_frame_mod.pack(fill=tk.X)
        ttk.Button(
            btn_frame_mod, text="Guardar Cambios", command=self._do_modify_from_panel
        ).pack(side=tk.LEFT, expand=True)
        ttk.Button(btn_frame_mod, text="Cancelar", command=self.show_action_panel).pack(
            side=tk.LEFT, expand=True
        )

        # Build Adjust Panel
        self.adjust_label = ttk.Label(self.adjust_panel, text="Ajustar stock para:")
        self.adjust_label.pack(fill=tk.X, pady=5)
        ttk.Label(self.adjust_panel, text="Cantidad a sumar(+) o restar(-):").pack(
            fill=tk.X
        )
        self.adjust_cant_entry = ttk.Entry(self.adjust_panel)
        self.adjust_cant_entry.pack(fill=tk.X, pady=(0, 10))
        btn_frame_adj = ttk.Frame(self.adjust_panel)
        btn_frame_adj.pack(fill=tk.X)
        ttk.Button(
            btn_frame_adj, text="Confirmar Ajuste", command=self._do_adjust_from_panel
        ).pack(side=tk.LEFT, expand=True)
        ttk.Button(btn_frame_adj, text="Cancelar", command=self.show_action_panel).pack(
            side=tk.LEFT, expand=True
        )

        # Build Sale Panel
        self.sale_label = ttk.Label(
            self.sale_panel, text="Vender item:", wraplength=280, justify=tk.LEFT
        )
        self.sale_label.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(self.sale_panel, text="Cantidad a Vender:").pack(fill=tk.X)
        self.sale_cant_entry = ttk.Entry(self.sale_panel)
        self.sale_cant_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(self.sale_panel, text="Costo Unitario ($):").pack(fill=tk.X)
        self.sale_costo_entry = ttk.Entry(self.sale_panel)
        self.sale_costo_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(self.sale_panel, text="Precio de Venta ($):").pack(fill=tk.X)
        self.sale_precio_entry = ttk.Entry(self.sale_panel)
        self.sale_precio_entry.pack(fill=tk.X, pady=(0, 10))
        btn_frame_sale = ttk.Frame(self.sale_panel)
        btn_frame_sale.pack(fill=tk.X)
        ttk.Button(
            btn_frame_sale,
            text="Agregar al Carrito",
            command=self._do_add_to_cart_from_panel,
        ).pack(side=tk.LEFT, expand=True)
        ttk.Button(
            btn_frame_sale, text="Cancelar", command=self.show_action_panel
        ).pack(side=tk.LEFT, expand=True)

        # Build Cart Panel Widgets
        self._build_cart_panel_widgets()

    def _build_cart_panel_widgets(self):
        cart_items_frame = ttk.LabelFrame(self.cart_panel, text="Items en Carrito")
        cart_items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        client_frame = ttk.LabelFrame(self.cart_panel, text="Datos del Cliente")
        client_frame.pack(fill=tk.X, pady=5)
        payment_main_frame = ttk.Frame(self.cart_panel)
        payment_main_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        payment_add_frame = ttk.LabelFrame(payment_main_frame, text="Añadir Pago")
        payment_add_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        payment_list_frame = ttk.LabelFrame(
            payment_main_frame, text="Pagos Registrados"
        )
        payment_list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        summary_frame = ttk.Frame(self.cart_panel)
        summary_frame.pack(fill=tk.X, pady=5)

        self.cart_tree = ttk.Treeview(
            cart_items_frame,
            columns=("Desc", "Cant", "Subtotal"),
            show="headings",
            height=5,
        )
        self.cart_tree.heading("Desc", text="Descripción")
        self.cart_tree.heading("Cant", text="Cant.")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.column("Desc", width=150)
        self.cart_tree.column("Cant", width=40, anchor=tk.CENTER)
        self.cart_tree.column("Subtotal", width=80, anchor=tk.E)
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Button(
            cart_items_frame, text="X", command=self._cart_remove_item, width=2
        ).pack(side=tk.RIGHT, anchor="n")

        ttk.Label(client_frame, text="Nombre:").grid(row=0, column=0, sticky="w")
        self.cart_cliente_entry = ttk.Entry(client_frame)
        self.cart_cliente_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(client_frame, text="Contacto:").grid(row=1, column=0, sticky="w")
        self.cart_contacto_entry = ttk.Entry(client_frame)
        self.cart_contacto_entry.grid(row=1, column=1, sticky="ew")
        client_frame.columnconfigure(1, weight=1)

        ttk.Label(payment_add_frame, text="Método:").pack()
        payment_methods = [
            "Efectivo",
            "Nequi",
            "Bancolombia",
            "Daviplata",
            "Datafono",
            "Sistecredito",
        ]
        self.cart_medio_pago_combo = ttk.Combobox(
            payment_add_frame, values=payment_methods, state="readonly"
        )
        self.cart_medio_pago_combo.pack(fill=tk.X)
        self.cart_medio_pago_combo.set("Efectivo")
        ttk.Label(payment_add_frame, text="Monto $:").pack()
        self.cart_monto_pago_entry = ttk.Entry(payment_add_frame)
        self.cart_monto_pago_entry.pack(fill=tk.X)
        ttk.Button(
            payment_add_frame, text="Agregar Pago", command=self._cart_add_pago
        ).pack(pady=5)

        self.cart_pagos_tree = ttk.Treeview(
            payment_list_frame, columns=("Metodo", "Monto"), show="headings", height=4
        )
        self.cart_pagos_tree.heading("Metodo", text="Método")
        self.cart_pagos_tree.heading("Monto", text="Monto")
        self.cart_pagos_tree.column("Metodo", width=80)
        self.cart_pagos_tree.column("Monto", width=70, anchor=tk.E)
        self.cart_pagos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Button(
            payment_list_frame, text="X", command=self._cart_remove_pago, width=2
        ).pack(side=tk.RIGHT, anchor="n")

        self.cart_lbl_total_venta = ttk.Label(
            summary_frame, text="Total Venta: $0.00", font=("Helvetica", 10, "bold")
        )
        self.cart_lbl_total_venta.pack(fill=tk.X)
        self.cart_lbl_total_pagado = ttk.Label(
            summary_frame,
            text="Total Pagado: $0.00",
            font=("Helvetica", 10, "bold"),
            foreground="blue",
        )
        self.cart_lbl_total_pagado.pack(fill=tk.X)
        self.cart_lbl_faltante = ttk.Label(
            summary_frame,
            text="Faltante: $0.00",
            font=("Helvetica", 11, "bold"),
            foreground="red",
        )
        self.cart_lbl_faltante.pack(fill=tk.X)

        style_confirm = ttk.Style()
        style_confirm.configure(
            "Confirm.TButton",
            foreground="white",
            background="navy",
            font=("Helvetica", 10, "bold"),
        )
        self.cart_btn_confirmar = ttk.Button(
            summary_frame,
            text="CONFIRMAR VENTA",
            style="Confirm.TButton",
            command=self._finalizar_venta_from_panel,
            state="disabled",
        )
        self.cart_btn_confirmar.pack(fill=tk.X, ipady=5, pady=(5, 0))

        bottom_btn_frame = ttk.Frame(self.cart_panel)
        bottom_btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        ttk.Button(
            bottom_btn_frame, text="Vaciar Carrito", command=self._cart_vaciar
        ).pack(side=tk.LEFT, expand=True)
        ttk.Button(
            bottom_btn_frame, text="Seguir Comprando", command=self.show_action_panel
        ).pack(side=tk.LEFT, expand=True)

    def on_inventory_select(self, event):
        self.show_action_panel()

    def _switch_action_panel(self, panel_to_show, new_title="Panel de Acciones"):
        self.action_panel.config(text=new_title)
        for panel in self.all_panels:
            panel.pack_forget()
        panel_to_show.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def show_action_panel(self, panel_type=None, data=None):
        if panel_type == "add":
            self.add_desc_entry.delete(0, tk.END)
            self.add_cant_entry.delete(0, tk.END)
            self._switch_action_panel(self.add_panel, "Agregar Nuevo Ítem")
            self.add_desc_entry.focus_set()
        elif panel_type == "modify":
            self.modify_desc_entry.delete(0, tk.END)
            self.modify_cant_entry.delete(0, tk.END)
            self.modify_desc_entry.insert(0, data[1])
            self.modify_cant_entry.insert(0, data[2])
            self._switch_action_panel(self.modify_panel, "Modificar Ítem")
            self.modify_desc_entry.focus_set()
        elif panel_type == "adjust":
            self.adjust_label.config(text=f"Ajustar stock para:\n{data[1]}")
            self.adjust_cant_entry.delete(0, tk.END)
            self._switch_action_panel(self.adjust_panel, "Ajustar Stock")
            self.adjust_cant_entry.focus_set()
        elif panel_type == "sale":
            self.sale_label.config(text=f"Vender item:\n{data[1]}\n(Stock: {data[2]})")
            self.sale_cant_entry.delete(0, tk.END)
            self.sale_costo_entry.delete(0, tk.END)
            self.sale_precio_entry.delete(0, tk.END)
            self._switch_action_panel(self.sale_panel, "Agregar a Venta")
            self.sale_cant_entry.focus_set()
        else:
            self._switch_action_panel(self.placeholder_panel, "Panel de Acciones")

    def show_add_panel(self):
        self.show_action_panel("add")

    def show_modify_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return
        self.show_action_panel("modify", data=values)

    def show_adjust_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return
        self.show_action_panel("adjust", data=values)

    def show_sale_panel(self):
        if os.path.basename(self.gestor.archivo_inventario) != "local.txt":
            messagebox.showerror(
                "Archivo Incorrecto", "Las ventas solo se realizan desde 'local.txt'."
            )
            return
        values = self._get_selected_item_values()
        if not values:
            return
        self.show_action_panel("sale", data=values)

    def show_cart_panel(self):
        if not self.carrito:
            messagebox.showinfo("Carrito Vacío", "No hay items en el carrito de venta.")
            return

        self._switch_action_panel(self.cart_panel, "Carrito de Venta")
        self.pagos_actuales = []
        self.cart_cliente_entry.delete(0, tk.END)
        self.cart_contacto_entry.delete(0, tk.END)
        self.cart_monto_pago_entry.delete(0, tk.END)
        self._cart_populate_items()
        self._cart_populate_pagos()

    def _do_add_from_panel(self):
        desc = self.add_desc_entry.get().strip()
        cant = self.add_cant_entry.get().strip()
        if not desc or not cant:
            messagebox.showerror("Error", "Ambos campos son obligatorios.")
            return
        success, message = self.gestor.agregar_linea(desc, cant)
        if success:
            self.populate_inventory_treeview()
            self.show_action_panel()
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

    def _do_modify_from_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return
        linea = int(values[0])
        nueva_desc = self.modify_desc_entry.get().strip()
        nueva_cant = self.modify_cant_entry.get().strip()
        if not nueva_desc or not nueva_cant:
            messagebox.showerror("Error", "Ambos campos son obligatorios.")
            return
        success, message = self.gestor.modificar_linea(linea, nueva_desc, nueva_cant)
        if success:
            self.populate_inventory_treeview()
            self.show_action_panel()
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)

    def _do_adjust_from_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return
        linea, desc, cant_actual_str = values

        try:
            cambio = int(self.adjust_cant_entry.get())
        except (ValueError, TypeError):
            messagebox.showerror(
                "Error", "La cantidad a ajustar debe ser un número entero."
            )
            return

        if cambio == 0:
            return

        if cambio > 0:  # Sumar
            success, msg = self.gestor.modificar_cantidad(int(linea), cambio)
        else:  # Restar
            if abs(cambio) > int(cant_actual_str):
                messagebox.showerror(
                    "Error", "No se puede restar más stock del que existe."
                )
                return
            success, msg = self.gestor.modificar_cantidad(int(linea), cambio)
            if success:
                success_local, msg_local = self.gestor.transferir_a_local(
                    desc, abs(cambio)
                )
                msg = f"{msg}\n{abs(cambio)} unidad(es) transferida(s) a 'local.txt'."
                if not success_local:
                    msg += f"\nADVERTENCIA: {msg_local}"

        if success:
            messagebox.showinfo("Éxito", msg)
            self.populate_inventory_treeview()
            self.show_action_panel()
        else:
            messagebox.showerror("Error", msg)

    def _do_add_to_cart_from_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return
        linea_num, desc, stock_actual = values

        try:
            cantidad = int(self.sale_cant_entry.get())
            costo = float(self.sale_costo_entry.get())
            precio = float(self.sale_precio_entry.get())
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser positiva.")
            if cantidad > int(stock_actual):
                messagebox.showerror(
                    "Stock Insuficiente", "La cantidad a vender supera el stock actual."
                )
                return
        except (ValueError, TypeError):
            messagebox.showerror(
                "Datos Inválidos",
                "Por favor, ingrese números válidos en todos los campos.",
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
        self.show_action_panel()
        self.status_label_inv.config(text=f"'{desc}' agregado al carrito.")

    def _cart_populate_items(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)

        total_general = 0
        for i, item in enumerate(self.carrito):
            subtotal = item["cantidad"] * item["precio"]
            total_general += subtotal
            self.cart_tree.insert(
                "",
                tk.END,
                iid=i,
                values=(item["desc"], item["cantidad"], f"${subtotal:,.2f}"),
            )

        self.cart_total_general = total_general
        self.cart_lbl_total_venta.config(text=f"Total Venta: ${total_general:,.2f}")

    def _cart_populate_pagos(self):
        for i in self.cart_pagos_tree.get_children():
            self.cart_pagos_tree.delete(i)

        for i, pago in enumerate(self.pagos_actuales):
            self.cart_pagos_tree.insert(
                "", tk.END, iid=i, values=(pago["metodo"], f"${pago['monto']:,.2f}")
            )

        self._cart_update_summary()

    def _cart_update_summary(self):
        total_pagado = sum(pago["monto"] for pago in self.pagos_actuales)
        faltante = self.cart_total_general - total_pagado

        self.cart_lbl_total_pagado.config(text=f"Total Pagado: ${total_pagado:,.2f}")

        if faltante > 0:
            self.cart_lbl_faltante.config(
                text=f"Faltante: ${faltante:,.2f}", foreground="red"
            )
            self.cart_btn_confirmar.config(state="disabled")
        else:
            self.cart_lbl_faltante.config(
                text=f"Cambio: ${-faltante:,.2f}", foreground="green"
            )
            self.cart_btn_confirmar.config(state="normal")

    def _cart_add_pago(self):
        metodo = self.cart_medio_pago_combo.get()
        try:
            monto = float(self.cart_monto_pago_entry.get())
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número positivo.")
            return

        self.pagos_actuales.append({"metodo": metodo, "monto": monto})
        self.cart_monto_pago_entry.delete(0, tk.END)
        self._cart_populate_pagos()

    def _cart_remove_item(self):
        selected_iid = self.cart_tree.focus()
        if not selected_iid:
            messagebox.showwarning(
                "Sin Selección", "Seleccione un item del carrito para eliminar."
            )
            return

        del self.carrito[int(selected_iid)]

        if not self.carrito:
            self._cart_vaciar()
        else:
            self._cart_populate_items()
            self._cart_populate_pagos()

        self.actualizar_vista_carrito()

    def _cart_remove_pago(self):
        selected_iid = self.cart_pagos_tree.focus()
        if not selected_iid:
            messagebox.showwarning("Sin Selección", "Seleccione un pago para eliminar.")
            return
        del self.pagos_actuales[int(selected_iid)]
        self._cart_populate_pagos()

    def _cart_vaciar(self):
        if self.carrito and messagebox.askyesno(
            "Confirmar", "¿Desea vaciar el carrito?"
        ):
            self.carrito.clear()
            self.actualizar_vista_carrito()
            self.show_action_panel()
            self.status_label_inv.config(text="Carrito vaciado.")
        elif not self.carrito:
            self.actualizar_vista_carrito()
            self.show_action_panel()

    def _finalizar_venta_from_panel(self):
        cliente = self.cart_cliente_entry.get().strip() or "Cliente General"
        cliente_contacto = self.cart_contacto_entry.get().strip()

        total_pagado = sum(p["monto"] for p in self.pagos_actuales)
        if total_pagado < self.cart_total_general:
            messagebox.showerror(
                "Pago Incompleto", "El monto pagado es menor al total de la venta."
            )
            return
        if not self.carrito:
            messagebox.showerror("Carrito Vacío", "No hay items para vender.")
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
                messagebox.showerror("Error en Venta", msg)
                self.populate_inventory_treeview()
                return

        ruta_txt = self.gestor.generar_factura_consolidada_txt(
            id_venta,
            timestamp,
            carrito_copia,
            self.cart_total_general,
            cliente,
            cliente_contacto,
            self.pagos_actuales,
        )

        self.show_output_options_dialog(
            ruta_txt,
            id_venta,
            timestamp,
            carrito_copia,
            self.cart_total_general,
            cliente,
            cliente_contacto,
            self.pagos_actuales,
        )

        self.carrito.clear()
        self.actualizar_vista_carrito()
        self.populate_inventory_treeview()
        self.populate_sales_treeview()
        self.notebook.select(self.ventas_tab)
        self.show_action_panel()

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

        self.filtro_pago_electronico_var = tk.BooleanVar()
        self.filtro_pago_electronico_chk = ttk.Checkbutton(
            linea_1_filtros,
            text="Mostrar solo pagos electrónicos",
            variable=self.filtro_pago_electronico_var,
            command=self.populate_sales_treeview,
        )
        self.filtro_pago_electronico_chk.pack(side=tk.LEFT, padx=15)

        ttk.Button(
            linea_2_filtros, text="Filtrar Ventas", command=self.populate_sales_treeview
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(
            linea_2_filtros, text="Mostrar Todo", command=self.limpiar_filtros_ventas
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
        data = [
            (self.sales_tree.set(child, col), child)
            for child in self.sales_tree.get_children("")
        ]
        column_index = self.sales_tree["columns"].index(col)
        numeric_columns = [3, 4, 5, 6, 7]
        try:
            if column_index in numeric_columns:
                data.sort(
                    key=lambda t: float(t[0]), reverse=self.sales_last_sort_reverse
                )
            elif column_index == 0:
                data.sort(
                    key=lambda t: datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S"),
                    reverse=self.sales_last_sort_reverse,
                )
            else:
                data.sort(
                    key=lambda t: t[0].lower(), reverse=self.sales_last_sort_reverse
                )
        except (ValueError, IndexError):
            data.sort(key=lambda t: t[0].lower(), reverse=self.sales_last_sort_reverse)
        for index, (val, child) in enumerate(data):
            self.sales_tree.move(child, "", index)
        self.sales_last_sort_reverse = not self.sales_last_sort_reverse

    def actualizar_estado_botones_venta(self):
        es_local = os.path.basename(self.gestor.archivo_inventario) == "local.txt"
        estado = "normal" if es_local else "disabled"
        if hasattr(self, "btn_agregar_venta"):
            self.btn_agregar_venta.config(state=estado)

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
        for value, entry in entries.items():
            if value in self.conteo_actual_caja:
                entry.insert(0, self.conteo_actual_caja[value])
        actualizar_totales()

        def guardar_y_cerrar():
            try:
                self.conteo_actual_caja.clear()
                detalle_dict = {}
                total_final = 0.0
                for value, entry in entries.items():
                    if value == "monedas":
                        continue
                    cantidad_str = entry.get() or "0"
                    cantidad_num = int(cantidad_str)
                    self.conteo_actual_caja[value] = cantidad_str
                    if cantidad_num > 0:
                        detalle_dict[value] = cantidad_num
                    total_final += cantidad_num * value
                monedas_str = entries["monedas"].get() or "0"
                monedas_num = float(monedas_str)
                self.conteo_actual_caja["monedas"] = monedas_str
                if monedas_num > 0:
                    detalle_dict["monedas"] = monedas_num
                total_final += monedas_num
                detalle_str = ", ".join(
                    [
                        f"${k:,.0f}: {v}" if k != "monedas" else f"Monedas: ${v:,.2f}"
                        for k, v in detalle_dict.items()
                    ]
                )
                self.gestor_caja.guardar_conteo_historial(total_final, detalle_str)
                self.dinero_real_entry.config(state="normal")
                self.dinero_real_entry.delete(0, tk.END)
                self.dinero_real_entry.insert(0, f"{total_final:.2f}")
                self.dinero_real_entry.config(state="readonly")
                win_conteo.destroy()
            except ValueError:
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
        for row in reversed(historial):
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
            self.conteo_actual_caja.clear()
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
            dinero_real = float(self.dinero_real_entry.get() or 0)
        except ValueError:
            messagebox.showerror(
                "Error", "El valor de dinero real en caja debe ser un número."
            )
            return None
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        total_ventas_dia = self.gestor.obtener_ventas_del_dia(fecha_hoy)
        pagos_electronicos = self.gestor.obtener_pagos_electronicos_del_dia(fecha_hoy)
        self.pagos_electronicos_entry.config(state="normal")
        self.pagos_electronicos_entry.delete(0, tk.END)
        self.pagos_electronicos_entry.insert(0, f"{pagos_electronicos:.2f}")
        self.pagos_electronicos_entry.config(state="readonly")
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
        self.show_action_panel()

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
        self.lbl_costo_total.config(text=f"Costo Total: ${costo_total:,.2f}")
        self.lbl_total_ventas.config(text=f"Total Ventas: ${total_ventas:,.2f}")
        self.lbl_total_ganancia.config(text=f"Ganancia Total: ${total_ganancia:,.2f}")

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

    def actualizar_vista_carrito(self):
        num_items = len(self.carrito)
        self.btn_ver_carrito.config(text=f"Ver Carrito ({num_items})")
        self.btn_ver_carrito.config(state="normal" if num_items > 0 else "disabled")

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
                elif current_os == "Darwin":
                    subprocess.call(("open", ruta_archivo))
                else:
                    subprocess.call(("xdg-open", ruta_archivo))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
        else:
            messagebox.showinfo(
                "No Encontrado",
                f"No se encontró el archivo de recibo:\n{nombre_archivo}\n\n(Es posible que sea de una venta anterior al sistema de recibos).",
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()
