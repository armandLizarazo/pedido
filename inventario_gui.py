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
            # Préstamos y Gastos son salidas (negativo)
            if tipo in ["Gasto", "Préstamo/Retiro"]:
                monto_float = -abs(monto_float)
            # Abonos a préstamos e Ingresos son entradas (positivo)
            elif tipo in ["Abono/Ingreso", "Abono Préstamo"]:
                monto_float = abs(monto_float)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.archivo_movimientos, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, tipo, descripcion, monto_float])
            return True, "Movimiento registrado."
        except ValueError:
            return False, "El monto debe ser un número válido."
        except Exception as e:
            return False, f"Error al registrar movimiento: {e}"

    def eliminar_movimiento(self, timestamp_a_eliminar):
        try:
            with open(self.archivo_movimientos, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                lineas = list(reader)

            header = lineas[0]
            lineas_actualizadas = [header]
            eliminado = False

            for linea in lineas[1:]:
                if linea and linea[0] == timestamp_a_eliminar:
                    eliminado = True
                    continue  # No agregar esta línea
                lineas_actualizadas.append(linea)

            if not eliminado:
                return False, "No se encontró el movimiento para eliminar."

            with open(self.archivo_movimientos, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(lineas_actualizadas)
            return True, "Movimiento eliminado con éxito."
        except FileNotFoundError:
            return False, "El archivo de movimientos no existe."
        except Exception as e:
            return False, f"Error al eliminar el movimiento: {e}"

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
                return list(
                    reversed(list(reader))
                )  # Devolver los más recientes primero
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

    def obtener_resumen_prestamos(self):
        """
        Analiza todos los movimientos para calcular saldos de préstamos por persona (descripción).
        """
        resumen = {}
        try:
            with open(self.archivo_movimientos, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row or not row.get("Monto"):
                        continue
                    try:
                        tipo = row.get("Tipo", "")
                        persona = row.get("Descripcion", "").strip()
                        monto = float(row.get("Monto", 0))
                    except ValueError:
                        continue

                    if tipo == "Préstamo/Retiro" and monto < 0:
                        if persona not in resumen:
                            resumen[persona] = {
                                "prestado": 0.0,
                                "abonado": 0.0,
                                "saldo": 0.0,
                            }
                        resumen[persona]["prestado"] += abs(monto)
                    elif tipo == "Abono Préstamo":
                        if persona not in resumen:
                            resumen[persona] = {
                                "prestado": 0.0,
                                "abonado": 0.0,
                                "saldo": 0.0,
                            }
                        resumen[persona]["abonado"] += abs(monto)

            final = {}
            for persona, datos in resumen.items():
                saldo = datos["prestado"] - datos["abonado"]
                datos["saldo"] = saldo
                final[persona] = datos

            return final
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Error calculando préstamos: {e}")
            return {}

    def obtener_historial_persona(self, nombre_persona):
        historial = []
        try:
            with open(self.archivo_movimientos, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row or not row.get("Descripcion") or not row.get("Monto"):
                        continue
                    if (
                        row["Descripcion"].strip().lower()
                        == nombre_persona.strip().lower()
                    ):
                        if row["Tipo"] in ["Préstamo/Retiro", "Abono Préstamo"]:
                            historial.append(row)
            return historial
        except:
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
        self.archivo_costos = "dbcst.txt"
        self.directorio_facturas = "facturas"
        self.crear_archivos_si_no_existen()

    def obtener_stock_dict(self, nombre_archivo):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        ruta_archivo = os.path.join(script_dir, nombre_archivo)
        stock_dict = {}
        if not os.path.exists(ruta_archivo):
            return stock_dict
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    partes = linea.strip().rsplit(" ", 1)
                    if len(partes) == 2:
                        desc, cant_str = partes
                        try:
                            stock_dict[desc.strip()] = int(cant_str)
                        except ValueError:
                            continue
            return stock_dict
        except Exception:
            return stock_dict

    def obtener_costos_dict(self):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        ruta_archivo = os.path.join(script_dir, self.archivo_costos)
        costos_dict = {}
        if not os.path.exists(ruta_archivo):
            return costos_dict
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    partes = linea.strip().rsplit(" ", 1)
                    if len(partes) == 2:
                        desc, costo_str = partes
                        try:
                            costos_dict[desc.strip()] = float(costo_str)
                        except ValueError:
                            continue
            return costos_dict
        except Exception:
            return costos_dict

    def actualizar_costo(self, descripcion, nuevo_costo):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        ruta_archivo = os.path.join(script_dir, self.archivo_costos)
        if not os.path.exists(ruta_archivo):
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                pass
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                lineas = f.readlines()

            item_encontrado = False
            descripcion_stripped = descripcion.strip()
            for i, linea in enumerate(lineas):
                partes = linea.strip().rsplit(" ", 1)
                if len(partes) == 2:
                    desc_archivo = partes[0].strip()
                    if desc_archivo == descripcion_stripped:
                        lineas[i] = f"    {descripcion_stripped} {nuevo_costo}\n"
                        item_encontrado = True
                        break
            if not item_encontrado:
                lineas.append(f"    {descripcion_stripped} {nuevo_costo}\n")

            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.writelines(lineas)
            return True
        except Exception as e:
            print(f"Error actualizando costos: {e}")
            return False

    def obtener_ultimo_precio(self, descripcion):
        """Busca en el historial de ventas el último precio de venta unitario usado para este item."""
        try:
            if not os.path.exists(self.archivo_ventas):
                return None
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                all_rows = list(reader)

            for row in reversed(all_rows):
                if (
                    len(row) > 5
                    and row[2].strip().lower() == descripcion.strip().lower()
                ):
                    if row[5] == "PrecioUnitario":
                        continue
                    return row[5]
            return None
        except Exception as e:
            print(f"Error buscando precio sugerido: {e}")
            return None

    def obtener_pagos_electronicos_del_dia(self, fecha_str):
        total_electronico = 0.0
        ventas_procesadas = set()
        try:
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                estado_idx = header.index("Estado") if "Estado" in header else -1

                for row in reader:
                    if not row or not row[0].startswith(fecha_str):
                        continue

                    if (
                        estado_idx != -1
                        and len(row) > estado_idx
                        and row[estado_idx] == "Anulada"
                    ):
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
                header = next(reader)
                estado_idx = header.index("Estado") if "Estado" in header else -1

                for row in reader:
                    if not row or not row[0].startswith(fecha_str):
                        continue
                    if (
                        estado_idx != -1
                        and len(row) > estado_idx
                        and row[estado_idx] == "Anulada"
                    ):
                        continue
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
        if not os.path.exists(self.archivo_costos):
            with open(self.archivo_costos, "w", encoding="utf-8") as f:
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
                        "Estado",
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
                "Completada",  # Nuevo estado
            ]

            with open(self.archivo_ventas, "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow(venta_data)

            return True, "Item procesado."
        except Exception as e:
            return False, f"Error procesando item {item_details['desc']}: {e}"

    def _restaurar_stock_item(self, descripcion, cantidad):
        archivo_local = "local.txt"
        if not os.path.exists(archivo_local):
            return False, f"El archivo '{archivo_local}' no existe."

        try:
            with open(archivo_local, "r", encoding="utf-8") as f:
                lineas = f.readlines()

            item_encontrado = False
            descripcion_stripped = descripcion.strip()
            for i, linea in enumerate(lineas):
                partes = linea.strip().rsplit(" ", 1)
                if len(partes) == 2 and partes[0].strip() == descripcion_stripped:
                    nueva_cantidad = int(partes[1]) + cantidad
                    lineas[i] = f"    {descripcion_stripped} {nueva_cantidad}\n"
                    item_encontrado = True
                    break

            if not item_encontrado:
                lineas.append(f"    {descripcion_stripped} {cantidad}\n")

            with open(archivo_local, "w", encoding="utf-8") as f:
                f.writelines(lineas)
            return (
                True,
                f"{cantidad} unidad(es) de '{descripcion_stripped}' devueltas a local.txt.",
            )
        except Exception as e:
            return False, f"Error al restaurar stock: {e}"

    def anular_venta(self, id_venta_anular):
        try:
            try:
                with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    all_lines = list(reader)
            except FileNotFoundError:
                return False, "El archivo de registro de ventas no existe."

            if not all_lines:
                return False, "El registro de ventas está vacío."

            header = all_lines[0]

            if "ID_Venta" in header:
                has_header = True
                start_index = 1
                try:
                    id_venta_idx = header.index("ID_Venta")
                    desc_idx = header.index("Descripcion")
                    cant_idx = header.index("Cantidad")

                    if "Estado" not in header:
                        header.append("Estado")
                        for i in range(start_index, len(all_lines)):
                            all_lines[i].append("Completada")

                    estado_idx = header.index("Estado")
                except ValueError as e:
                    return (
                        False,
                        f"El encabezado del archivo de ventas es incorrecto. Falta la columna: {e}",
                    )
            else:
                has_header = False
                start_index = 0
                id_venta_idx = 1
                desc_idx = 2
                cant_idx = 3
                estado_idx = 11

            items_restaurados = []
            venta_encontrada = False
            changes_made = False

            for i in range(start_index, len(all_lines)):
                row = all_lines[i]
                while len(row) <= estado_idx:
                    row.append("")
                if not row[estado_idx]:
                    row[estado_idx] = "Completada"

                if (
                    row[id_venta_idx] == id_venta_anular
                    and row[estado_idx] != "Anulada"
                ):
                    venta_encontrada = True
                    desc = row[desc_idx]
                    try:
                        cant = int(row[cant_idx])
                        success, msg = self._restaurar_stock_item(desc, cant)
                        if not success:
                            return False, f"No se pudo restaurar el stock: {msg}"
                        items_restaurados.append(msg)
                        row[estado_idx] = "Anulada"
                        changes_made = True
                    except (ValueError, IndexError):
                        return (
                            False,
                            f"Dato inválido en la venta {id_venta_anular}. No se pudo anular.",
                        )

            if not venta_encontrada:
                return False, "No se encontró la venta o ya estaba anulada."

            if changes_made:
                if not has_header:
                    new_header = [
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
                        "Estado",
                    ]
                    all_lines.insert(0, new_header)

                with open(self.archivo_ventas, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(all_lines)

            return True, "Venta anulada con éxito.\n" + "\n".join(items_restaurados)

        except Exception as e:
            return False, f"Error inesperado al anular la venta: {e}"

    def modificar_venta_completa(self, id_venta, item_match, nuevos_datos):
        try:
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                all_lines = list(reader)

            if not all_lines:
                return False, "El registro de ventas está vacío."

            # Índices por defecto
            id_venta_idx = 1
            desc_idx = 2
            cant_idx = 3
            costo_idx = 4
            precio_idx = 5
            total_idx = 6
            ganancia_idx = 7
            cliente_idx = 9
            medio_pago_idx = 10

            changes_made = False
            item_updated = False

            for i in range(1, len(all_lines)):
                row = all_lines[i]
                if len(row) > medio_pago_idx and row[id_venta_idx] == id_venta:
                    # 1. Actualizar datos generales (Cliente, MedioPago) para TODA la venta
                    row[cliente_idx] = nuevos_datos["cliente"]
                    row[medio_pago_idx] = nuevos_datos["medio_pago"]
                    changes_made = True

                    # 2. Actualizar datos específicos del ítem (si coincide la fila exacta)
                    if (
                        not item_updated
                        and row[desc_idx] == item_match["desc"]
                        and str(row[cant_idx]) == str(item_match["cant"])
                    ):
                        row[desc_idx] = nuevos_datos["desc"]
                        row[cant_idx] = str(nuevos_datos["cant"])
                        row[costo_idx] = f"{nuevos_datos['costo']:.2f}"
                        row[precio_idx] = f"{nuevos_datos['precio']:.2f}"

                        # Recalcular Total y Ganancia
                        total = nuevos_datos["cant"] * nuevos_datos["precio"]
                        ganancia = (
                            nuevos_datos["precio"] - nuevos_datos["costo"]
                        ) * nuevos_datos["cant"]
                        row[total_idx] = f"{total:.2f}"
                        row[ganancia_idx] = f"{ganancia:.2f}"

                        item_updated = True

            if changes_made:
                with open(self.archivo_ventas, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(all_lines)
                return True, "Datos de la venta actualizados correctamente."
            else:
                return False, "No se encontró la venta con ese ID."

        except Exception as e:
            return False, f"Error al modificar la venta: {e}"

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

    # --- ELIMINADO: Funciones de Ordenar y Verificar Formato ---

    def leer_historial_ventas(self):
        try:
            if not os.path.exists(self.archivo_ventas):
                return []
            with open(self.archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                first_row = next(reader, None)
                if first_row and "ID_Venta" in first_row:
                    return list(reader)
                else:
                    all_data = []
                    if first_row:
                        all_data.append(first_row)
                    all_data.extend(list(reader))
                    return all_data
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
        master.title("Gestor de Inventario y Ventas v4.8 - Flujo Optimizado")
        master.geometry("1400x800")

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # --- ESTILOS ---
        self.style.configure(
            "Add.TButton",
            foreground="white",
            background="green",
            font=("Helvetica", 10, "bold"),
        )
        self.style.configure(
            "AddUnit.TButton", foreground="white", background="#28a745"
        )  # green
        self.style.configure(
            "RemUnit.TButton", foreground="white", background="#dc3545"
        )  # red
        self.style.configure(
            "Confirm.TButton",
            foreground="white",
            background="navy",
            font=("Helvetica", 10, "bold"),
        )
        self.style.configure("Anular.TButton", foreground="white", background="red")

        self.gestor = GestorInventario()
        self.gestor_caja = GestorCaja()
        self.carrito = []
        self.conteo_actual_caja = {}
        self.historial_conteos_data = []

        # --- VARIABLES DE SEGURIDAD ---
        self.is_admin = False
        self.admin_pin = "1234"  # PIN por defecto (puedes cambiarlo aquí)

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
        self.prestamos_tab = ttk.Frame(self.notebook, padding="10")
        # --- ELIMINADO: Pestaña Consultas ---

        self.notebook.add(self.inventario_tab, text="Gestión de Inventario")
        self.notebook.add(self.ventas_tab, text="Ventas y Análisis")
        self.notebook.add(self.caja_tab, text="Cuadre de Caja")
        self.notebook.add(self.prestamos_tab, text="Gestión de Préstamos")
        # --- ELIMINADO: Añadir pestaña al notebook ---

        self.crear_widgets_inventario()
        self.crear_widgets_ventas()
        self.crear_widgets_caja()
        self.crear_widgets_prestamos()
        # --- ELIMINADO: Crear widgets consultas ---

        self.populate_inventory_treeview()
        self.populate_sales_treeview()

        self.master.after(100, lambda: self.add_placeholder(None))
        self.cargar_estado_caja()
        self.actualizar_estado_botones_venta()
        self.show_action_panel()
        self._populate_conteos_dropdown()
        self.populate_prestamos_treeview()

        self.sales_last_sort_col = None
        self.sales_last_sort_reverse = False

        # New sort variables for cons_tree
        self.cons_last_sort_col = None
        self.cons_last_sort_reverse = False

        self.actualizar_permisos()

    def toggle_admin(self):
        if self.is_admin:
            self.is_admin = False
            self.btn_auth.config(text="👤 Modo: Vendedor (Entrar Admin)")
            self.actualizar_permisos()
            messagebox.showinfo("Sesión", "Sesión de administrador cerrada.")
        else:
            pwd = simpledialog.askstring(
                "Seguridad", "Ingrese PIN de Administrador:", show="*"
            )
            if pwd == self.admin_pin:
                self.is_admin = True
                self.btn_auth.config(text="👑 Modo: ADMIN (Salir)")
                self.actualizar_permisos()
                messagebox.showinfo("Sesión", "Modo Administrador activado.")
            elif pwd is not None:
                messagebox.showerror("Acceso Denegado", "PIN incorrecto.")

    def actualizar_permisos(self):
        # Actualiza el estado de los botones sensibles según el rol
        estado_admin = "normal" if self.is_admin else "disabled"

        # 1. Botón de Eliminar Ítem en Inventario
        if hasattr(self, "btn_eliminar_item"):
            self.btn_eliminar_item.config(state=estado_admin)

        # 2. Botones de Modificar/Anular en Ventas (se actualizan forzando el evento de selección)
        if hasattr(self, "sales_tree"):
            self.on_sale_select(None)

        # 3. Botón de Cerrar Caja
        if hasattr(self, "btn_cerrar_caja"):
            self.cargar_estado_caja()

        # 4. OCULTAR DATOS SENSIBLES EN TABLA DE VENTAS
        if hasattr(self, "sales_tree"):
            if self.is_admin:
                # Muestra TODAS las columnas
                self.sales_tree["displaycolumns"] = (
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
                    "Estado",
                )
                self.lbl_costo_total.pack(
                    side=tk.LEFT, padx=20, before=self.lbl_total_ventas
                )
                self.lbl_total_ganancia.pack(side=tk.LEFT, padx=20)
            else:
                # Oculta CostoU y Ganancia
                self.sales_tree["displaycolumns"] = (
                    "Timestamp",
                    "ID_Venta",
                    "Item",
                    "Cantidad",
                    "PrecioU",
                    "Total",
                    "Origen",
                    "Cliente",
                    "MedioPago",
                    "Estado",
                )
                self.lbl_costo_total.pack_forget()
                self.lbl_total_ganancia.pack_forget()

        # 5. OCULTAR CAMPO DE COSTO AL VENDER
        if hasattr(self, "sale_costo_label"):
            if self.is_admin:
                self.sale_costo_label.pack(
                    fill=tk.X, pady=(0, 5), before=self.sale_precio_label
                )
                self.sale_costo_entry.pack(
                    fill=tk.X, pady=(0, 5), before=self.sale_precio_label
                )
            else:
                self.sale_costo_label.pack_forget()
                self.sale_costo_entry.pack_forget()

    def cambiar_archivo(self):
        filename = filedialog.askopenfilename(
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*"))
        )
        if filename:
            # 1. Guardar selección actual
            selected_desc = None
            sel = self.inventory_tree.selection()
            if sel:
                item = self.inventory_tree.item(sel[0])
                selected_desc = item["values"][1]  # Description

            # 2. Cambiar archivo
            msg = self.gestor.cambiar_archivo(filename)
            self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")

            # 3. Recargar tabla
            self.populate_inventory_treeview()
            self.actualizar_estado_botones_venta()

            # 4. Restaurar selección si existe
            if selected_desc:
                self._reselect_item_by_desc(selected_desc)

            self.status_label_inv.config(
                text=f"Cambiado a {os.path.basename(filename)}"
            )

    def cambiar_archivo_rapido(self, filename):
        # 1. Guardar selección actual
        selected_desc = None
        sel = self.inventory_tree.selection()
        if sel:
            item = self.inventory_tree.item(sel[0])
            selected_desc = item["values"][1]  # Description

        # 2. Cambiar archivo
        msg = self.gestor.cambiar_archivo(filename)
        self.lbl_archivo.config(text=f"Archivo: {self.gestor.archivo_inventario}")

        # 3. Recargar tabla
        self.populate_inventory_treeview()
        self.actualizar_estado_botones_venta()

        # 4. Restaurar selección si existe
        if selected_desc:
            self._reselect_item_by_desc(selected_desc)

        self.status_label_inv.config(text=f"Cambiado a {filename}")

    # --- HELPER PARA RE-SELECCIONAR ---
    def _reselect_item_by_desc(self, target_desc):
        # Buscar en los items actuales del treeview
        found = False
        for iid in self.inventory_tree.get_children():
            # values[1] es la descripción
            item_desc = self.inventory_tree.item(iid, "values")[1]
            if item_desc == target_desc:
                self.inventory_tree.selection_set(iid)
                self.inventory_tree.focus(iid)
                self.inventory_tree.see(iid)
                found = True
                break

        if found:
            self.inventory_tree.focus_set()  # Devolver el foco al widget

    # --- SECCIÓN ELIMINADA: crear_widgets_consultas y funciones relacionadas ---
    # Se han removido: crear_widgets_consultas, sort_cons_tree_by_column,
    # limpiar_filtros_consulta, ejecutar_consulta_analisis

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

        self.btn_auth = ttk.Button(
            top_frame,
            text="👤 Modo: Vendedor (Entrar Admin)",
            command=self.toggle_admin,
        )
        self.btn_auth.pack(side=tk.RIGHT, padx=10)

        self.status_label_inv = ttk.Label(top_frame, text="Listo.", anchor=tk.E)
        self.status_label_inv.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)

        ttk.Label(filter_frame, text="Filtrar por palabra clave:").pack(
            side=tk.LEFT, padx=5
        )
        self.filtro_palabra_entry = ttk.Entry(filter_frame, width=20)
        self.filtro_palabra_entry.pack(side=tk.LEFT, padx=5)
        self.filtro_palabra_entry.bind("<FocusIn>", self.clear_placeholder)
        self.filtro_palabra_entry.bind("<FocusOut>", self.add_placeholder)
        # BINDING ENTER KEY PARA BUSCAR RAPIDO
        self.filtro_palabra_entry.bind(
            "<Return>", lambda e: self.populate_inventory_treeview()
        )

        ttk.Label(filter_frame, text="y por cantidad:").pack(side=tk.LEFT, padx=5)
        self.filtro_op_combo = ttk.Combobox(
            filter_frame, values=["", ">", "<", "="], width=3, state="readonly"
        )
        self.filtro_op_combo.pack(side=tk.LEFT, padx=5)
        self.filtro_cant_entry = ttk.Entry(filter_frame, width=10)
        self.filtro_cant_entry.pack(side=tk.LEFT, padx=5)
        self.filtro_cant_entry.bind(
            "<Return>", lambda e: self.populate_inventory_treeview()
        )

        ttk.Button(
            filter_frame,
            text="Aplicar Filtro / Refrescar",
            command=self.populate_inventory_treeview,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="Limpiar", command=self.limpiar_filtros).pack(
            side=tk.LEFT, padx=5
        )

        self.inventory_tree = ttk.Treeview(
            left_pane,
            columns=("Linea", "Item", "Costo", "CantBodegaC", "CantLocal"),
            show="headings",
        )
        self.inventory_tree.heading("Linea", text="Línea")
        self.inventory_tree.heading("Item", text="Item")
        self.inventory_tree.heading("Costo", text="Costo")
        self.inventory_tree.heading("CantBodegaC", text="Cant. Bodega C")
        self.inventory_tree.heading("CantLocal", text="Cant. Local")

        self.inventory_tree.column("Linea", width=60, anchor=tk.CENTER)
        self.inventory_tree.column("Item", width=350)
        self.inventory_tree.column("Costo", width=100, anchor=tk.E)
        self.inventory_tree.column("CantBodegaC", width=120, anchor=tk.CENTER)
        self.inventory_tree.column("CantLocal", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(
            left_pane, orient=tk.VERTICAL, command=self.inventory_tree.yview
        )
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.inventory_tree.bind("<<TreeviewSelect>>", self.on_inventory_select)

        self._build_action_panels()

        # --- MODIFICADO: Grupo STOCK con botones directos ---
        stock_group = ttk.LabelFrame(action_frame_bottom, text="Stock")
        stock_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Botones directos para ajuste de stock
        btn_add = ttk.Button(
            stock_group,
            text="+1",
            width=5,
            command=lambda: self._do_adjust_stock_by_one(1),
            style="AddUnit.TButton",
        )
        btn_add.pack(side=tk.LEFT, pady=2, padx=5, ipady=5)

        btn_sub = ttk.Button(
            stock_group,
            text="-1",
            width=5,
            command=lambda: self._do_adjust_stock_by_one(-1),
            style="RemUnit.TButton",
        )
        btn_sub.pack(side=tk.LEFT, pady=2, padx=5, ipady=5)

        item_group = ttk.LabelFrame(action_frame_bottom, text="Ítems")
        item_group.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(item_group, text="Agregar Nuevo", command=self.show_add_panel).pack(
            pady=2, padx=5
        )
        ttk.Button(
            item_group, text="Modificar Seleccionado", command=self.show_modify_panel
        ).pack(pady=2, padx=5)
        self.btn_eliminar_item = ttk.Button(
            item_group, text="Eliminar Seleccionado", command=self.eliminar_item
        )
        self.btn_eliminar_item.pack(pady=2, padx=5)

        # --- ELIMINADO: Grupo de Herramientas (Ordenar/Verificar) ---

        venta_group = ttk.Frame(action_frame_bottom)
        venta_group.pack(side=tk.RIGHT, padx=20, fill=tk.Y)

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
        self.adjust_label = ttk.Label(
            self.adjust_panel,
            text="Ajustar stock para:",
            wraplength=280,
            font=("Helvetica", 10, "bold"),
        )
        self.adjust_label.pack(fill=tk.X, pady=5)

        self.adjust_stock_label = ttk.Label(
            self.adjust_panel, text="Stock Actual: ", font=("Helvetica", 10)
        )
        self.adjust_stock_label.pack(fill=tk.X, pady=(5, 10))

        btn_frame_adj = ttk.Frame(self.adjust_panel)
        btn_frame_adj.pack(fill=tk.X, pady=10)

        # Los botones ahora también están en el panel lateral, aunque son redundantes con los de abajo,
        # los dejamos por si el usuario prefiere usarlos desde aquí.
        ttk.Button(
            btn_frame_adj,
            text="Agregar Unidad (+1)",
            command=lambda: self._do_adjust_stock_by_one(1),
            style="AddUnit.TButton",
        ).pack(fill=tk.X, ipady=5, pady=2)

        ttk.Button(
            btn_frame_adj,
            text="Restar Unidad (-1)",
            command=lambda: self._do_adjust_stock_by_one(-1),
            style="RemUnit.TButton",
        ).pack(fill=tk.X, ipady=5, pady=2)

        ttk.Button(
            self.adjust_panel, text="Finalizar", command=self.show_action_panel
        ).pack(side=tk.BOTTOM, fill=tk.X, ipady=5, pady=(20, 0))

        # Build Sale Panel
        self.sale_label = ttk.Label(
            self.sale_panel, text="Vender item:", wraplength=280, justify=tk.LEFT
        )
        self.sale_label.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.sale_panel, text="Cantidad a Vender:").pack(fill=tk.X)
        self.sale_cant_entry = ttk.Entry(self.sale_panel)
        self.sale_cant_entry.pack(fill=tk.X, pady=(0, 5))

        # --- ASIGNADOS A VARIABLES PARA PODER OCULTARLOS ---
        self.sale_costo_label = ttk.Label(self.sale_panel, text="Costo Unitario ($):")
        self.sale_costo_label.pack(fill=tk.X, pady=(0, 5))
        self.sale_costo_entry = ttk.Entry(self.sale_panel)
        self.sale_costo_entry.pack(fill=tk.X, pady=(0, 5))

        self.sale_precio_label = ttk.Label(self.sale_panel, text="Precio de Venta ($):")
        self.sale_precio_label.pack(fill=tk.X)
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
            "Celya",
        ]
        self.cart_medio_pago_combo = ttk.Combobox(
            payment_add_frame, values=payment_methods, state="readonly"
        )
        self.cart_medio_pago_combo.pack(fill=tk.X)
        self.cart_medio_pago_combo.set("")

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

        self.cart_btn_confirmar = ttk.Button(
            summary_frame,
            text="CONFIRMAR Venta",
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
            archivo_actual = os.path.basename(self.gestor.archivo_inventario)

            if archivo_actual == "local.txt":
                qty_to_edit = data[4]
            else:
                qty_to_edit = data[3]

            self.modify_desc_entry.insert(0, data[1])
            self.modify_cant_entry.insert(0, qty_to_edit)
            self._switch_action_panel(self.modify_panel, "Modificar Ítem")
            self.modify_desc_entry.focus_set()

        elif panel_type == "adjust":
            self.adjust_label.config(text=f"{data[1]}")
            self.adjust_stock_label.config(
                text=f"Stock Bodega: {data[3]}  |  Stock Local: {data[4]}"
            )
            self._switch_action_panel(self.adjust_panel, "Ajustar Stock")

        elif panel_type == "sale":
            self.sale_label.config(
                text=f"Vender item:\n{data[1]}\n(Stock Local: {data[4]})"
            )
            self.sale_cant_entry.delete(0, tk.END)
            self.sale_cant_entry.insert(
                0, "1"
            )  # --- CAMBIO: Cantidad por defecto 1 ---
            self.sale_costo_entry.delete(0, tk.END)
            self.sale_precio_entry.delete(0, tk.END)

            # Pre-cargar costo si existe (se llena en segundo plano aunque esté oculto)
            costo_val = data[2]
            if costo_val and costo_val != "N/A":
                try:
                    costo_limpio = str(costo_val).replace("$", "").replace(",", "")
                    self.sale_costo_entry.insert(0, costo_limpio)
                except:
                    self.sale_costo_entry.insert(0, "0.00")
            else:
                self.sale_costo_entry.insert(0, "0.00")

            # --- CAMBIO: Pre-cargar precio sugerido ---
            item_desc = data[1]
            precio_sugerido = self.gestor.obtener_ultimo_precio(item_desc)
            if precio_sugerido:
                self.sale_precio_entry.insert(0, str(precio_sugerido))

            self._switch_action_panel(self.sale_panel, "Agregar a Venta")
            self.sale_cant_entry.focus_set()
        else:
            if self.inventory_tree.selection():
                # Si hay algo seleccionado pero no es una accion específica,
                # mostramos el placeholder o podriamos mostrar el adjust panel por defecto.
                # Para simplificar, lo dejamos en placeholder, ya que los botones +1/-1 están abajo.
                pass
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
        self.cart_medio_pago_combo.set("")
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

    def _do_adjust_stock_by_one(self, change):
        values = self._get_selected_item_values()
        if not values:
            return

        linea, desc, costo, cant_bodega, cant_local = values
        archivo_actual = os.path.basename(self.gestor.archivo_inventario)

        if change == -1:
            try:
                lineas = self.gestor._leer_lineas_archivo()
                partes = lineas[int(linea) - 1].strip().rsplit(" ", 1)
                cant_actual_en_archivo = int(partes[1])
                if cant_actual_en_archivo <= 0:
                    messagebox.showerror(
                        "Error", f"No hay stock en '{archivo_actual}' para restar."
                    )
                    return
            except (IndexError, ValueError):
                messagebox.showerror(
                    "Error", "No se pudo leer la cantidad actual del archivo."
                )
                return

        success = False
        msg = ""

        if archivo_actual == "bodegac.txt" and change == -1:
            s_resta, m_resta = self.gestor.modificar_cantidad(int(linea), -1)
            if s_resta:
                s_trans, m_trans = self.gestor.transferir_a_local(desc, 1)
                if s_trans:
                    success = True
                    msg = "1 unidad restada de Bodega y transferida a Local."
                else:
                    self.gestor.modificar_cantidad(int(linea), +1)
                    success = False
                    msg = f"Error al transferir a local: {m_trans}"
            else:
                success = False
                msg = m_resta
        else:
            success, msg = self.gestor.modificar_cantidad(int(linea), change)

        if success:
            yview_pos = self.inventory_tree.yview()
            self.populate_inventory_treeview()

            # --- CORRECCIÓN DE FOCO Y SELECCIÓN USANDO HELPER ---
            self._reselect_item_by_desc(desc)

            self.inventory_tree.yview_moveto(yview_pos[0])
            self.status_label_inv.config(text="Stock actualizado.")
        else:
            messagebox.showerror("Error", msg)

    def _do_add_to_cart_from_panel(self):
        values = self._get_selected_item_values()
        if not values:
            return

        linea_num, desc, costo_old, stock_bodega, stock_local = values

        try:
            cantidad = int(self.sale_cant_entry.get())
            costo = float(self.sale_costo_entry.get())
            precio = float(self.sale_precio_entry.get())

            if cantidad <= 0:
                raise ValueError("La cantidad debe ser positiva.")

            if cantidad > int(stock_local):
                messagebox.showerror(
                    "Stock Insuficiente",
                    "La cantidad a vender supera el stock del local.",
                )
                return
        except (ValueError, TypeError):
            messagebox.showerror(
                "Datos Inválidos",
                "Por favor, ingrese números válidos en todos los campos.",
            )
            return

        self.gestor.actualizar_costo(desc, costo)

        item_data = {
            "linea_num": int(linea_num),
            "desc": desc,
            "stock_actual": int(stock_local),
            "cantidad": cantidad,
            "costo": costo,
            "precio": precio,
        }

        self.carrito.append(item_data)
        self.actualizar_vista_carrito()

        # Mantiene el foco en el árbol después de añadir
        self.show_action_panel()
        self._reselect_item_by_desc(desc)

        self.status_label_inv.config(
            text=f"'{desc}' agregado al carrito. Costo actualizado."
        )

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
        if not metodo:
            messagebox.showwarning(
                "Falta Medio de Pago",
                "Por favor seleccione un medio de pago antes de agregar.",
            )
            return

        try:
            monto = float(self.cart_monto_pago_entry.get())
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número positivo.")
            return

        self.pagos_actuales.append({"metodo": metodo, "monto": monto})
        self.cart_monto_pago_entry.delete(0, tk.END)
        self.cart_medio_pago_combo.set("")
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
        # --- CAMBIO: Fecha por defecto HOY ---
        today_str = datetime.now().strftime("%Y-%m-%d")

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
            self.filtro_fecha_desde.set_date(datetime.now())  # Set default date
        else:
            self.filtro_fecha_desde = ttk.Entry(linea_1_filtros)
            self.filtro_fecha_desde.pack(side=tk.LEFT, padx=(0, 10))
            self.filtro_fecha_desde.insert(0, today_str)

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
            self.filtro_fecha_hasta.set_date(datetime.now())  # Set default date
        else:
            self.filtro_fecha_hasta = ttk.Entry(linea_1_filtros)
            self.filtro_fecha_hasta.pack(side=tk.LEFT, padx=(0, 10))
            self.filtro_fecha_hasta.insert(0, today_str)

        ttk.Label(linea_1_filtros, text="Descripción o ID Venta:").pack(
            side=tk.LEFT, padx=(10, 5)
        )
        self.filtro_desc_venta = ttk.Entry(linea_1_filtros, width=25)
        self.filtro_desc_venta.pack(side=tk.LEFT, padx=(0, 10))

        # --- CAMBIO: Reemplazo Checkbox por Combobox de Medios de Pago ---
        ttk.Label(linea_1_filtros, text="Medio Pago:").pack(side=tk.LEFT, padx=(5, 5))
        payment_methods_filter = [
            "Todos",
            "Efectivo",
            "Nequi",
            "Bancolombia",
            "Daviplata",
            "Datafono",
            "Sistecredito",
            "Celya",
        ]
        self.filtro_medio_pago_combo = ttk.Combobox(
            linea_1_filtros, values=payment_methods_filter, state="readonly", width=12
        )
        self.filtro_medio_pago_combo.pack(side=tk.LEFT, padx=5)
        self.filtro_medio_pago_combo.set("Todos")
        self.filtro_medio_pago_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.populate_sales_treeview()
        )

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

        self.btn_modificar_venta = ttk.Button(
            linea_2_filtros,
            text="Modificar Venta",
            command=self.modificar_venta_seleccionada,
            state="disabled",
        )
        self.btn_modificar_venta.pack(side=tk.LEFT, padx=5)

        self.btn_anular_venta = ttk.Button(
            linea_2_filtros,
            text="Anular Venta",
            command=self.anular_venta_seleccionada,
            state="disabled",
            style="Anular.TButton",
        )
        self.btn_anular_venta.pack(side=tk.LEFT, padx=10)

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
            "Estado",
        )
        self.sales_tree = ttk.Treeview(
            historial_frame, columns=columnas, show="headings"
        )
        self.sales_tree.tag_configure("anulada", foreground="gray")

        for col in columnas:
            self.sales_tree.heading(
                col,
                text=col.replace("_", " "),
                command=lambda _col=col: self.sort_sales_by_column(_col),
            )
        for col in columnas:
            self.sales_tree.column(col, anchor=tk.W, width=85)
        self.sales_tree.column("Timestamp", width=140)
        self.sales_tree.column("Item", width=220)
        self.sales_tree.column("MedioPago", width=150)

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
        main_pane = ttk.PanedWindow(self.caja_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_main_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(left_main_frame, weight=2)

        right_main_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(right_main_frame, weight=1)

        left_frame = ttk.Frame(left_main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        center_frame = ttk.Frame(left_main_frame)
        center_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        mov_btn_frame = ttk.Frame(movimientos_frame)
        mov_btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.btn_registrar_mov = ttk.Button(
            mov_btn_frame, text="Registrar", command=self.registrar_movimiento
        )
        self.btn_registrar_mov.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar_mov = ttk.Button(
            mov_btn_frame,
            text="Eliminar Seleccionado",
            command=self._eliminar_movimiento_seleccionado,
        )
        self.btn_eliminar_mov.pack(side=tk.LEFT, padx=5)

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

        cierre_frame = ttk.LabelFrame(
            center_frame, text="3. Cierre del Día", padding=10
        )
        cierre_frame.pack(fill=tk.X, pady=5)

        ttk.Label(cierre_frame, text="Total Pagos Electrónicos:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.pagos_electronicos_entry = ttk.Entry(cierre_frame, state="readonly")
        self.pagos_electronicos_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(cierre_frame, text="Dinero Real Contado en Caja:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.dinero_real_entry = ttk.Entry(cierre_frame, state="readonly")
        self.dinero_real_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

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
            center_frame, text="4. Resumen del Cuadre", padding=10
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

        # --- PANEL FIJO DE CONTEO DE DINERO ---
        conteo_frame = ttk.LabelFrame(
            right_main_frame, text="Conteo de Dinero Físico", padding=10
        )
        conteo_frame.pack(fill=tk.BOTH, expand=True)

        historial_frame = ttk.Frame(conteo_frame)
        historial_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(historial_frame, text="Historial de Conteos:").pack(side=tk.LEFT)
        self.historial_conteos_combo = ttk.Combobox(
            historial_frame, state="readonly", width=25
        )
        self.historial_conteos_combo.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.btn_cargar_conteo = ttk.Button(
            historial_frame, text="Cargar", command=self._cargar_conteo_seleccionado
        )
        self.btn_cargar_conteo.pack(side=tk.LEFT)

        denominaciones = {
            100000: "100.000:",
            50000: "50.000:",
            20000: "20.000:",
            10000: "10.000:",
            5000: "5.000:",
            2000: "2.000:",
            1000: "1.000:",
        }

        self.conteo_entries = {}
        billetes_frame = ttk.Frame(conteo_frame)
        billetes_frame.pack(fill=tk.X)

        row = 0
        col = 0
        for val, txt in denominaciones.items():
            ttk.Label(billetes_frame, text=txt).grid(
                row=row, column=col, sticky="w", padx=(0, 2)
            )
            entry = ttk.Entry(billetes_frame, width=7, justify="right")
            entry.grid(row=row, column=col + 1, pady=2)
            entry.bind("<KeyRelease>", self._update_conteo_total)
            self.conteo_entries[val] = entry

            col += 2
            if col >= 4:
                col = 0
                row += 1

        monedas_frame = ttk.Frame(conteo_frame)
        monedas_frame.pack(fill=tk.X, pady=5)
        ttk.Label(monedas_frame, text="Total Monedas:").pack(side=tk.LEFT)
        self.conteo_monedas_entry = ttk.Entry(monedas_frame, justify="right")
        self.conteo_monedas_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.conteo_monedas_entry.bind("<KeyRelease>", self._update_conteo_total)

        self.conteo_total_label = ttk.Label(
            conteo_frame, text="Total Contado: $0.00", font=("Helvetica", 12, "bold")
        )
        self.conteo_total_label.pack(pady=10)

        conteo_btn_frame = ttk.Frame(conteo_frame)
        conteo_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            conteo_btn_frame,
            text="Agregar al Cierre",
            command=self._aplicar_conteo_a_cierre,
        ).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(
            conteo_btn_frame, text="Guardar Conteo", command=self._guardar_conteo_actual
        ).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(
            conteo_btn_frame, text="Nuevo", command=self._limpiar_campos_conteo
        ).pack(side=tk.LEFT, expand=True, padx=2)

    def _update_conteo_total(self, event=None):
        total = 0.0
        try:
            for val, entry in self.conteo_entries.items():
                cantidad = int(entry.get() or 0)
                total += val * cantidad

            monedas = float(self.conteo_monedas_entry.get() or 0)
            total += monedas
            self.conteo_total_label.config(text=f"Total Contado: ${total:,.2f}")
            return total
        except (ValueError, TypeError):
            self.conteo_total_label.config(text="Total Contado: ¡Error!")
            return None

    def _populate_conteos_dropdown(self):
        self.historial_conteos_data = self.gestor_caja.obtener_historial_conteos()
        display_values = []
        for row in self.historial_conteos_data:
            try:
                # row[0] = Timestamp, row[1] = Total
                display_values.append(f"{row[0]} - ${float(row[1]):,.0f}")
            except (ValueError, IndexError):
                continue

        self.historial_conteos_combo["values"] = display_values
        if display_values:
            self.historial_conteos_combo.set(display_values[0])

    def _cargar_conteo_seleccionado(self):
        selected_index = self.historial_conteos_combo.current()
        if selected_index == -1:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, seleccione un conteo del historial para cargar.",
            )
            return

        try:
            conteo_data = self.historial_conteos_data[selected_index]
            detalle_str = conteo_data[
                2
            ]  # El string de detalle está en la tercera columna

            self._limpiar_campos_conteo()

            # Parsear el string de detalle
            pares = detalle_str.split(", ")
            for par in pares:
                if "Monedas" in par:
                    monto = float(re.search(r"[\d.]+", par.replace(",", "")).group())
                    self.conteo_monedas_entry.insert(0, f"{monto:.0f}")
                else:
                    partes = par.split(":")
                    denominacion_str = re.sub(r"[^\d]", "", partes[0])
                    denominacion = int(denominacion_str)
                    cantidad = int(partes[1].strip())
                    if denominacion in self.conteo_entries:
                        self.conteo_entries[denominacion].insert(0, str(cantidad))
            self._update_conteo_total()
            self.status_label_inv.config(text="Conteo histórico cargado.")
        except (IndexError, ValueError, TypeError) as e:
            messagebox.showerror(
                "Error al Cargar",
                f"No se pudo interpretar el conteo guardado.\nDetalle: {e}",
            )

    def _guardar_conteo_actual(self):
        total = self._update_conteo_total()
        if total is None:
            messagebox.showerror(
                "Error de Entrada",
                "Verifique que todos los campos de conteo contengan solo números.",
            )
            return

        detalle_dict = {}
        for val, entry in self.conteo_entries.items():
            cantidad = int(entry.get() or 0)
            if cantidad > 0:
                detalle_dict[val] = cantidad

        monedas = float(self.conteo_monedas_entry.get() or 0)
        if monedas > 0:
            detalle_dict["Monedas"] = monedas

        detalle_str = ", ".join(
            [
                f"${k:,.0f}: {v}" if k != "Monedas" else f"Monedas: ${v:,.2f}"
                for k, v in detalle_dict.items()
            ]
        )

        success, msg = self.gestor_caja.guardar_conteo_historial(total, detalle_str)
        if success:
            messagebox.showinfo("Éxito", "Conteo guardado en el historial.")
            self._populate_conteos_dropdown()
        else:
            messagebox.showerror("Error al Guardar", msg)

    def _limpiar_campos_conteo(self):
        for entry in self.conteo_entries.values():
            entry.delete(0, tk.END)
        self.conteo_monedas_entry.delete(0, tk.END)
        self._update_conteo_total()
        self.status_label_inv.config(text="Campos de conteo limpiados.")

    def _aplicar_conteo_a_cierre(self):
        total = self._update_conteo_total()
        if total is not None:
            self.dinero_real_entry.config(state="normal")
            self.dinero_real_entry.delete(0, tk.END)
            self.dinero_real_entry.insert(0, f"{total:.2f}")
            self.dinero_real_entry.config(state="readonly")
            self.status_label_inv.config(text="Total del conteo aplicado al cierre.")
        else:
            messagebox.showerror(
                "Error", "No se pudo calcular el total. Revise los campos."
            )

    def _eliminar_movimiento_seleccionado(self):
        selected_item_id = self.mov_tree.focus()
        if not selected_item_id:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, seleccione un movimiento de la lista para eliminar.",
            )
            return

        selected_values = self.mov_tree.item(selected_item_id, "values")
        tipo_sel, desc_sel, monto_sel = selected_values
        monto_sel_float = float(monto_sel.replace("$", "").replace(",", ""))

        if not messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el siguiente movimiento?\n\n{tipo_sel} - {desc_sel} - ${monto_sel_float:,.2f}",
        ):
            return

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        movimientos_hoy = self.gestor_caja.obtener_movimientos_dia(fecha_hoy)

        timestamp_a_eliminar = None
        for mov in movimientos_hoy:
            if (
                mov["Tipo"] == tipo_sel
                and mov["Descripcion"] == desc_sel
                and float(mov["Monto"]) == monto_sel_float
            ):
                timestamp_a_eliminar = mov["Timestamp"]
                break

        if timestamp_a_eliminar:
            success, msg = self.gestor_caja.eliminar_movimiento(timestamp_a_eliminar)
            if success:
                messagebox.showinfo("Éxito", msg)
                self.cargar_movimientos_hoy()
                self.populate_prestamos_treeview()  # Actualizar préstamos por si acaso
            else:
                messagebox.showerror("Error", msg)
        else:
            messagebox.showerror(
                "Error",
                "No se pudo encontrar el movimiento exacto para eliminar. Intente refrescar la aplicación.",
            )

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
            # Activar el cierre solo si es admin
            self.btn_cerrar_caja.config(state="normal" if self.is_admin else "disabled")
        else:
            self.btn_registrar_mov.config(state="disabled")
            self.btn_eliminar_mov.config(state="disabled")
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
            self._limpiar_campos_conteo()
            messagebox.showinfo("Éxito", msg)
            self.caja_inicial_entry.config(state="disabled")
            self.caja_base_entry.config(state="disabled")
            self.btn_iniciar_dia.config(state="disabled")
            self.btn_registrar_mov.config(state="normal")
            self.btn_eliminar_mov.config(state="normal")
            self.btn_cerrar_caja.config(state="normal" if self.is_admin else "disabled")
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
            if tipo == "Préstamo/Retiro" or tipo == "Abono Préstamo":
                self.populate_prestamos_treeview()
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
                "",
                tk.END,
                values=(mov["Tipo"], mov["Descripcion"], f"${monto:,.2f}"),
            )

    def _ejecutar_logica_cuadre(self):
        try:
            dinero_real = float(self.dinero_real_entry.get() or 0)
        except ValueError:
            messagebox.showerror(
                "Error",
                "El valor de dinero real en caja es inválido. Use el panel de conteo para asignarlo.",
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
                    self.btn_eliminar_mov.config(state="disabled")
                else:
                    messagebox.showerror("Error al Guardar", msg)

    # --- NUEVA FUNCIONALIDAD: GESTIÓN DE PRÉSTAMOS (Restaurada) ---
    def crear_widgets_prestamos(self):
        main_pane = ttk.PanedWindow(self.prestamos_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)

        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)

        # ---- Lado Izquierdo: Lista de Deudores ----
        ttk.Label(
            left_frame,
            text="Resumen de Préstamos Activos",
            font=("Helvetica", 12, "bold"),
        ).pack(pady=10)

        columns = ("Persona", "Prestado", "Abonado", "Saldo")
        self.prestamos_tree = ttk.Treeview(left_frame, columns=columns, show="headings")
        self.prestamos_tree.heading("Persona", text="Deudor")
        self.prestamos_tree.heading("Prestado", text="Total Prestado")
        self.prestamos_tree.heading("Abonado", text="Total Abonado")
        self.prestamos_tree.heading("Saldo", text="Saldo Pendiente")

        self.prestamos_tree.column("Persona", width=200)
        self.prestamos_tree.column("Prestado", width=100, anchor=tk.E)
        self.prestamos_tree.column("Abonado", width=100, anchor=tk.E)
        self.prestamos_tree.column("Saldo", width=100, anchor=tk.E)

        self.prestamos_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.prestamos_tree.bind("<<TreeviewSelect>>", self.on_prestamo_select)

        ttk.Button(
            left_frame,
            text="Actualizar Lista",
            command=self.populate_prestamos_treeview,
        ).pack(pady=5)

        # ---- Lado Derecho: Acciones ----
        actions_frame = ttk.LabelFrame(right_frame, text="Acciones", padding=10)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Nuevo Préstamo
        ttk.Label(
            actions_frame, text="Nuevo Préstamo:", font=("Helvetica", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(actions_frame, text="Nombre Deudor:").pack(anchor="w")
        self.nuevo_prestamo_nombre = ttk.Entry(actions_frame)
        self.nuevo_prestamo_nombre.pack(fill=tk.X, pady=2)

        ttk.Label(actions_frame, text="Monto a Prestar ($):").pack(anchor="w")
        self.nuevo_prestamo_monto = ttk.Entry(actions_frame)
        self.nuevo_prestamo_monto.pack(fill=tk.X, pady=2)

        ttk.Button(
            actions_frame,
            text="Registrar Préstamo",
            command=self.registrar_nuevo_prestamo,
        ).pack(fill=tk.X, pady=5)

        ttk.Separator(actions_frame, orient="horizontal").pack(fill="x", pady=15)

        # Registrar Abono
        self.lbl_abono_persona = ttk.Label(
            actions_frame,
            text="Abonar a: Seleccione...",
            font=("Helvetica", 10, "bold"),
        )
        self.lbl_abono_persona.pack(anchor="w", pady=(0, 5))

        ttk.Label(actions_frame, text="Monto Abono ($):").pack(anchor="w")
        self.abono_monto_entry = ttk.Entry(actions_frame)
        self.abono_monto_entry.pack(fill=tk.X, pady=2)

        self.btn_registrar_abono = ttk.Button(
            actions_frame,
            text="Registrar Abono",
            command=self.registrar_abono_prestamo,
            state="disabled",
        )
        self.btn_registrar_abono.pack(fill=tk.X, pady=5)

        ttk.Separator(actions_frame, orient="horizontal").pack(fill="x", pady=15)

        # Historial
        self.btn_ver_historial_prestamo = ttk.Button(
            actions_frame,
            text="Ver Historial Detallado",
            command=self.ver_historial_prestamo,
            state="disabled",
        )
        self.btn_ver_historial_prestamo.pack(fill=tk.X, pady=5)

    def populate_prestamos_treeview(self):
        for i in self.prestamos_tree.get_children():
            self.prestamos_tree.delete(i)
        resumen = self.gestor_caja.obtener_resumen_prestamos()

        for persona, datos in resumen.items():
            # Solo mostrar si tiene historial relevante (prestado > 0 o saldo != 0)
            if datos["prestado"] > 0 or datos["saldo"] != 0:
                self.prestamos_tree.insert(
                    "",
                    tk.END,
                    values=(
                        persona,
                        f"${datos['prestado']:,.2f}",
                        f"${datos['abonado']:,.2f}",
                        f"${datos['saldo']:,.2f}",
                    ),
                )

    def on_prestamo_select(self, event):
        selected = self.prestamos_tree.selection()
        if selected:
            item = self.prestamos_tree.item(selected[0])
            nombre = item["values"][0]
            self.lbl_abono_persona.config(text=f"Abonar a: {nombre}")
            self.btn_registrar_abono.config(state="normal")
            self.btn_ver_historial_prestamo.config(state="normal")
            self.seleccion_prestamo_actual = nombre
        else:
            self.lbl_abono_persona.config(text="Abonar a: Seleccione...")
            self.btn_registrar_abono.config(state="disabled")
            self.btn_ver_historial_prestamo.config(state="disabled")
            self.seleccion_prestamo_actual = None

    def registrar_nuevo_prestamo(self):
        nombre = self.nuevo_prestamo_nombre.get().strip()
        monto = self.nuevo_prestamo_monto.get().strip()

        if not nombre or not monto:
            messagebox.showerror("Error", "Debe ingresar nombre y monto.")
            return

        success, msg = self.gestor_caja.registrar_movimiento(
            "Préstamo/Retiro", nombre, monto
        )

        if success:
            messagebox.showinfo("Éxito", "Préstamo registrado correctamente.")
            self.nuevo_prestamo_nombre.delete(0, tk.END)
            self.nuevo_prestamo_monto.delete(0, tk.END)
            self.populate_prestamos_treeview()
            self.cargar_movimientos_hoy()  # Actualizar también la pestaña de Caja
        else:
            messagebox.showerror("Error", msg)

    def registrar_abono_prestamo(self):
        if (
            not hasattr(self, "seleccion_prestamo_actual")
            or not self.seleccion_prestamo_actual
        ):
            return

        monto = self.abono_monto_entry.get().strip()
        if not monto:
            messagebox.showerror("Error", "Debe ingresar un monto.")
            return

        success, msg = self.gestor_caja.registrar_movimiento(
            "Abono Préstamo", self.seleccion_prestamo_actual, monto
        )

        if success:
            messagebox.showinfo("Éxito", "Abono registrado correctamente.")
            self.abono_monto_entry.delete(0, tk.END)
            self.populate_prestamos_treeview()
            self.cargar_movimientos_hoy()  # Actualizar también la pestaña de Caja
        else:
            messagebox.showerror("Error", msg)

    def ver_historial_prestamo(self):
        if (
            not hasattr(self, "seleccion_prestamo_actual")
            or not self.seleccion_prestamo_actual
        ):
            return

        nombre = self.seleccion_prestamo_actual
        historial = self.gestor_caja.obtener_historial_persona(nombre)

        win = tk.Toplevel(self.master)
        win.title(f"Historial de {nombre}")
        win.geometry("500x400")

        tree = ttk.Treeview(win, columns=("Fecha", "Tipo", "Monto"), show="headings")
        tree.heading("Fecha", text="Fecha")
        tree.heading("Tipo", text="Tipo")
        tree.heading("Monto", text="Monto")

        tree.column("Fecha", width=150)
        tree.column("Tipo", width=150)
        tree.column("Monto", width=100, anchor=tk.E)
        tree.pack(fill=tk.BOTH, expand=True)

        for mov in historial:
            monto_fmt = f"${float(mov['Monto']):,.2f}"
            tree.insert("", tk.END, values=(mov["Timestamp"], mov["Tipo"], monto_fmt))

    def populate_inventory_treeview(self):
        # Limpiar
        for i in self.inventory_tree.get_children():
            self.inventory_tree.delete(i)

        datos, errores = self.gestor.leer_datos()
        costos = self.gestor.obtener_costos_dict()

        # Determine current view context for cross-referencing
        archivo_actual = os.path.basename(self.gestor.archivo_inventario)
        stock_externo = {}
        if archivo_actual == "local.txt":
            stock_externo = self.gestor.obtener_stock_dict("bodegac.txt")
        elif archivo_actual == "bodegac.txt":
            stock_externo = self.gestor.obtener_stock_dict("local.txt")

        # Filtros
        filtro_palabra = self.filtro_palabra_entry.get().lower().strip()
        if filtro_palabra == "buscar...":
            filtro_palabra = ""

        filtro_cant = self.filtro_cant_entry.get().strip()
        op = self.filtro_op_combo.get()

        for linea_num, desc, cant in datos:
            # Filtro Texto
            if filtro_palabra and filtro_palabra not in desc.lower():
                continue

            # Filtro Cantidad
            if filtro_cant and op:
                try:
                    val_filtro = int(filtro_cant)
                    if op == ">" and not (cant > val_filtro):
                        continue
                    if op == "<" and not (cant < val_filtro):
                        continue
                    if op == "=" and not (cant == val_filtro):
                        continue
                except ValueError:
                    pass  # Ignore invalid filter

            # --- CORRECCIÓN COSTO 0 vs N/A ---
            # Verificamos si la llave existe en el diccionario, sin importar si es 0
            if desc in costos:
                costo = costos[desc]
                costo_str = f"${costo:,.2f}"
            else:
                costo = 0.0
                costo_str = "N/A"

            cant_local = (
                cant if archivo_actual == "local.txt" else stock_externo.get(desc, 0)
            )
            cant_bodega = (
                cant if archivo_actual == "bodegac.txt" else stock_externo.get(desc, 0)
            )

            # Values: Linea, Item, Costo, CantBodegaC, CantLocal
            self.inventory_tree.insert(
                "", tk.END, values=(linea_num, desc, costo_str, cant_bodega, cant_local)
            )

        if errores:
            self.status_label_inv.config(
                text=f"Advertencia: {len(errores)} líneas con errores formato."
            )
        else:
            self.status_label_inv.config(text=f"Total items: {len(datos)}")

    def _get_selected_item_values(self):
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Sin selección", "Por favor seleccione un ítem de la lista."
            )
            return None
        return self.inventory_tree.item(selected[0])["values"]

    def limpiar_filtros(self):
        self.filtro_palabra_entry.delete(0, tk.END)
        self.add_placeholder(None)
        self.filtro_cant_entry.delete(0, tk.END)
        self.filtro_op_combo.set("")
        self.populate_inventory_treeview()

    def add_placeholder(self, event):
        if not self.filtro_palabra_entry.get():
            self.filtro_palabra_entry.insert(0, "Buscar...")
            self.filtro_palabra_entry.config(foreground="grey")

    def clear_placeholder(self, event):
        if self.filtro_palabra_entry.get() == "Buscar...":
            self.filtro_palabra_entry.delete(0, tk.END)
            self.filtro_palabra_entry.config(foreground="black")

    def eliminar_item(self):
        values = self._get_selected_item_values()
        if not values:
            return

        linea = int(values[0])
        desc = values[1]

        if messagebox.askyesno("Confirmar", f"¿Eliminar '{desc}' permanentemente?"):
            success, msg = self.gestor.eliminar_linea(linea)
            if success:
                self.populate_inventory_treeview()
                messagebox.showinfo("Éxito", msg)
            else:
                messagebox.showerror("Error", msg)

    def actualizar_vista_carrito(self):
        count = len(self.carrito)
        self.btn_ver_carrito.config(
            text=f"Ver Carrito ({count})", state="normal" if count > 0 else "disabled"
        )

    def populate_sales_treeview(self):
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)

        ventas = self.gestor.leer_historial_ventas()

        # Filtros
        desde = self.filtro_fecha_desde.get()
        hasta = self.filtro_fecha_hasta.get()
        txt_filtro = self.filtro_desc_venta.get().lower().strip()
        filtro_medio = (
            self.filtro_medio_pago_combo.get()
        )  # --- CAMBIO: Obtener valor del combo ---

        items_vendidos = 0
        costo_total = 0.0
        venta_total = 0.0
        ganancia_total = 0.0

        for row in ventas:
            # Asegurar longitud
            while len(row) < 12:
                row.append("")

            # row indices: 0:Timestamp, 1:ID, 2:Desc, 3:Cant, 4:Costo, 5:Precio, 6:Total, 7:Ganancia, 8:Origen, 9:Cliente, 10:Medio, 11:Estado
            fecha_str = row[0].split(" ")[0]

            # Filtro fecha (simple string compare for YYYY-MM-DD works well)
            if desde and fecha_str < desde:
                continue
            if hasta and fecha_str > hasta:
                continue

            # Filtro texto
            if txt_filtro:
                if (
                    txt_filtro not in row[1].lower()
                    and txt_filtro not in row[2].lower()
                ):
                    continue

            # --- CAMBIO: Filtro Medio de Pago Específico ---
            medio_venta = row[10].lower()
            if filtro_medio and filtro_medio != "Todos":
                # Buscamos si el medio seleccionado está dentro del string de medios de la venta
                # (útil por si hay pagos mixtos como "Efectivo, Nequi")
                if filtro_medio.lower() not in medio_venta:
                    continue

            estado = row[11]
            tags = ("anulada",) if estado == "Anulada" else ()

            self.sales_tree.insert("", tk.END, values=row, tags=tags)

            if estado != "Anulada":
                try:
                    items_vendidos += int(row[3])
                    # --- CORRECCIÓN LÓGICA DE SUMA ---
                    # Eliminada la línea duplicada que calculaba mal el costo unitario/total
                    v_total = float(row[6])
                    g_total = float(row[7])
                    venta_total += v_total
                    ganancia_total += g_total
                    costo_total += v_total - g_total
                except:
                    pass

        self.lbl_total_items.config(text=f"Items Vendidos: {items_vendidos}")
        self.lbl_costo_total.config(text=f"Costo Total: ${costo_total:,.2f}")
        self.lbl_total_ventas.config(text=f"Total Ventas: ${venta_total:,.2f}")
        self.lbl_total_ganancia.config(text=f"Ganancia Total: ${ganancia_total:,.2f}")

    def limpiar_filtros_ventas(self):
        if TKCALENDAR_AVAILABLE:
            self.filtro_fecha_desde.set_date(datetime.now())
            self.filtro_fecha_hasta.set_date(datetime.now())
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            self.filtro_fecha_desde.delete(0, tk.END)
            self.filtro_fecha_desde.insert(0, today)
            self.filtro_fecha_hasta.delete(0, tk.END)
            self.filtro_fecha_hasta.insert(0, today)

        self.filtro_desc_venta.delete(0, tk.END)
        self.filtro_medio_pago_combo.set("Todos")  # --- CAMBIO: Resetear combo ---
        self.populate_sales_treeview()

    def on_sale_select(self, event):
        selected = self.sales_tree.selection()
        if selected:
            self.btn_ver_recibo.config(state="normal")
            item = self.sales_tree.item(selected[0])
            estado = item["values"][11]
            if estado == "Anulada" or not self.is_admin:
                self.btn_anular_venta.config(state="disabled")
                self.btn_modificar_venta.config(state="disabled")
            else:
                self.btn_anular_venta.config(state="normal")
                self.btn_modificar_venta.config(state="normal")
        else:
            self.btn_ver_recibo.config(state="disabled")
            self.btn_anular_venta.config(state="disabled")
            self.btn_modificar_venta.config(state="disabled")

    def abrir_recibo_txt(self):
        selected = self.sales_tree.selection()
        if not selected:
            return
        item = self.sales_tree.item(selected[0])
        id_venta = item["values"][1]

        # Buscar archivo
        filename = f"Factura_POS_{id_venta}.txt"
        path = os.path.join(self.gestor.directorio_facturas, filename)

        if os.path.exists(path):
            try:
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", path])
                else:
                    subprocess.call(["xdg-open", path])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
        else:
            messagebox.showerror("No encontrado", "El archivo de factura no existe.")

    def anular_venta_seleccionada(self):
        selected = self.sales_tree.selection()
        if not selected:
            return
        item = self.sales_tree.item(selected[0])
        id_venta = item["values"][1]

        if messagebox.askyesno(
            "Anular Venta",
            f"¿Desea anular la venta ID {id_venta}?\nEsto devolverá el stock al inventario local.",
        ):
            success, msg = self.gestor.anular_venta(id_venta)
            if success:
                messagebox.showinfo("Éxito", msg)
                self.populate_sales_treeview()
                self.populate_inventory_treeview()
            else:
                messagebox.showerror("Error", msg)

    def modificar_venta_seleccionada(self):
        selected = self.sales_tree.selection()
        if not selected:
            return
        item = self.sales_tree.item(selected[0])

        vals = item["values"]
        id_venta = str(vals[1])
        desc_actual = str(vals[2])
        cant_actual = str(vals[3])

        # Limpiar símbolos de moneda para mostrarlos en los Entry
        def clean_money(val_str):
            return str(val_str).replace("$", "").replace(",", "").strip()

        costo_actual = clean_money(vals[4])
        precio_actual = clean_money(vals[5])
        cliente_actual = str(vals[9])
        medio_pago_actual = str(vals[10])

        win = tk.Toplevel(self.master)
        win.title("Modificar Venta")
        win.geometry("450x450")
        win.resizable(False, False)

        ttk.Label(
            win,
            text=f"Modificando ID Venta: {id_venta}",
            font=("Helvetica", 11, "bold"),
        ).pack(pady=10)

        form_frame = ttk.Frame(win, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN 1: ÍTEM ---
        lf_item = ttk.LabelFrame(
            form_frame, text="Datos del Ítem Seleccionado", padding=10
        )
        lf_item.pack(fill=tk.X, pady=5)

        ttk.Label(lf_item, text="Descripción:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        ent_desc = ttk.Entry(lf_item, width=30)
        ent_desc.insert(0, desc_actual)
        ent_desc.grid(row=0, column=1, pady=2, padx=5)

        ttk.Label(lf_item, text="Cantidad:").grid(row=1, column=0, sticky="w", pady=2)
        ent_cant = ttk.Entry(lf_item, width=15)
        ent_cant.insert(0, cant_actual)
        ent_cant.grid(row=1, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(lf_item, text="Costo Unitario ($):").grid(
            row=2, column=0, sticky="w", pady=2
        )
        ent_costo = ttk.Entry(lf_item, width=15)
        ent_costo.insert(0, costo_actual)
        ent_costo.grid(row=2, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(lf_item, text="Precio Unitario ($):").grid(
            row=3, column=0, sticky="w", pady=2
        )
        ent_precio = ttk.Entry(lf_item, width=15)
        ent_precio.insert(0, precio_actual)
        ent_precio.grid(row=3, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(
            lf_item,
            text="Nota: Cambiar cantidad aquí NO ajusta el stock físico.",
            font=("Helvetica", 8),
            foreground="red",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # --- SECCIÓN 2: DATOS GENERALES ---
        lf_gen = ttk.LabelFrame(
            form_frame, text="Datos Generales (Aplica a toda la venta)", padding=10
        )
        lf_gen.pack(fill=tk.X, pady=10)

        ttk.Label(lf_gen, text="Cliente:").grid(row=0, column=0, sticky="w", pady=2)
        ent_cliente = ttk.Entry(lf_gen, width=30)
        ent_cliente.insert(0, cliente_actual)
        ent_cliente.grid(row=0, column=1, pady=2, padx=5)

        ttk.Label(lf_gen, text="Medio de Pago:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        ent_medio = ttk.Entry(lf_gen, width=30)
        ent_medio.insert(0, medio_pago_actual)
        ent_medio.grid(row=1, column=1, pady=2, padx=5)

        def guardar():
            nuevo_cli = ent_cliente.get().strip()
            nuevo_med = ent_medio.get().strip()
            nueva_desc = ent_desc.get().strip()

            try:
                nueva_cant = int(ent_cant.get())
                nuevo_costo = float(ent_costo.get())
                nuevo_precio = float(ent_precio.get())
            except ValueError:
                messagebox.showerror(
                    "Error", "Cantidad, Costo y Precio deben ser números.", parent=win
                )
                return

            if not nuevo_cli or not nuevo_med or not nueva_desc:
                messagebox.showerror(
                    "Error", "Los campos de texto no pueden estar vacíos.", parent=win
                )
                return

            item_match = {"desc": desc_actual, "cant": cant_actual}

            nuevos_datos = {
                "desc": nueva_desc,
                "cant": nueva_cant,
                "costo": nuevo_costo,
                "precio": nuevo_precio,
                "cliente": nuevo_cli,
                "medio_pago": nuevo_med,
            }

            success, msg = self.gestor.modificar_venta_completa(
                id_venta, item_match, nuevos_datos
            )
            if success:
                messagebox.showinfo("Éxito", msg, parent=win)
                self.populate_sales_treeview()
                win.destroy()
            else:
                messagebox.showerror("Error", msg, parent=win)

        ttk.Button(
            win,
            text="Guardar Cambios y Recalcular",
            command=guardar,
            style="Confirm.TButton",
        ).pack(pady=5, ipady=5)

    def show_output_options_dialog(
        self, ruta_txt, id_venta, timestamp, carrito, total, cliente, contacto, pagos
    ):
        win = tk.Toplevel(self.master)
        win.title("Venta Finalizada")
        win.geometry("400x250")

        ttk.Label(
            win, text="¡Venta registrada con éxito!", font=("Helvetica", 12, "bold")
        ).pack(pady=10)
        ttk.Label(win, text=f"Total: ${total:,.2f}").pack(pady=5)

        def open_txt():
            self.gestor.imprimir_factura_directo(ruta_txt)

        def gen_pdf():
            ruta_pdf = self.gestor.generar_factura_consolidada_pdf(
                id_venta, timestamp, carrito, total, cliente, contacto, pagos
            )
            if platform.system() == "Windows":
                os.startfile(ruta_pdf)
            else:
                messagebox.showinfo("PDF Generado", f"Guardado en: {ruta_pdf}")

        ttk.Button(win, text="Imprimir Ticket (TXT)", command=open_txt).pack(
            fill=tk.X, padx=20, pady=5
        )
        ttk.Button(win, text="Generar y Abrir PDF", command=gen_pdf).pack(
            fill=tk.X, padx=20, pady=5
        )
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(
            fill=tk.X, padx=20, pady=10
        )

    # --- ELIMINADO: Métodos puente ordenar_alfabeticamente y verificar_formato ---


if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioGUI(root)
    root.mainloop()
