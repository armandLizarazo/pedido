import http.server
import socketserver
import socket
import sys
import json
import os
import csv
import re
from datetime import datetime
import urllib.parse

PORT = 8000
ADMIN_PIN = "1234"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- HELPER DATABASE FUNCTIONS ---

def parse_stock_file(filename):
    stock = {}
    if not os.path.exists(filename):
        return stock
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                partes = line_stripped.rsplit(' ', 1)
                if len(partes) == 2:
                    desc, qty_str = partes
                    try:
                        stock[desc.strip()] = int(qty_str)
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error parseando {filename}: {e}")
    return stock

def parse_cost_file(filename="dbcst.txt"):
    costs = {}
    if not os.path.exists(filename):
        return costs
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                partes = line_stripped.rsplit(' ', 1)
                if len(partes) == 2:
                    desc, cost_str = partes
                    try:
                        costs[desc.strip()] = float(cost_str)
                    except ValueError:
                        continue
    except Exception as e:
        print(f"Error parseando costos: {e}")
    return costs

def obtener_ultimos_precios():
    precios = {}
    archivo_ventas = "registro_ventas.csv"
    if os.path.exists(archivo_ventas):
        try:
            with open(archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    desc_idx = header.index("Descripcion") if "Descripcion" in header else 2
                    precio_idx = header.index("PrecioUnitario") if "PrecioUnitario" in header else 5
                    estado_idx = header.index("Estado") if "Estado" in header else -1
                    for row in reader:
                        if row and len(row) > max(desc_idx, precio_idx):
                            if estado_idx != -1 and len(row) > estado_idx and row[estado_idx] == "Anulada":
                                continue
                            try:
                                precios[row[desc_idx].strip()] = float(row[precio_idx])
                            except ValueError:
                                continue
        except Exception as e:
            print(f"Error al obtener últimos precios: {e}")
    return precios

def deduct_stock(archivo_origen, items):
    if not os.path.exists(archivo_origen):
        return False, f"El archivo de stock {archivo_origen} no existe."
    
    try:
        with open(archivo_origen, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
        stock_map = {}
        for idx, line in enumerate(lineas):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            partes = line_stripped.rsplit(' ', 1)
            if len(partes) == 2:
                desc, qty_str = partes
                try:
                    stock_map[desc.strip()] = {
                        "index": idx,
                        "qty": int(qty_str)
                    }
                except ValueError:
                    continue
                    
        # Verificar stock disponible para todos los items antes de modificar nada
        for item in items:
            desc = item["descripcion"].strip()
            cant = int(item["cantidad"])
            if desc not in stock_map:
                return False, f"El producto '{desc}' no se encuentra en el stock de {archivo_origen}."
            if stock_map[desc]["qty"] < cant:
                return False, f"Stock insuficiente para '{desc}' en {archivo_origen}. Disponible: {stock_map[desc]['qty']}, requerido: {cant}."
                
        # Realizar deducción
        for item in items:
            desc = item["descripcion"].strip()
            cant = int(item["cantidad"])
            idx = stock_map[desc]["index"]
            new_qty = stock_map[desc]["qty"] - cant
            lineas[idx] = f"    {desc} {new_qty}\n"
            
        with open(archivo_origen, 'w', encoding='utf-8') as f:
            f.writelines(lineas)
            
        return True, "Stock actualizado correctamente."
    except Exception as e:
        return False, f"Error al actualizar stock: {e}"

def restore_stock(archivo_origen, desc, cant):
    return adjust_product_stock(archivo_origen, desc, cant)

def adjust_product_stock(filename, desc, cambio):
    desc_stripped = desc.strip()
    try:
        lineas = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
                
        item_encontrado = False
        for idx, line in enumerate(lineas):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            partes = line_stripped.rsplit(' ', 1)
            if len(partes) == 2 and partes[0].strip() == desc_stripped:
                try:
                    current_qty = int(partes[1])
                    new_qty = current_qty + cambio
                    if new_qty < 0:
                        return False, "La cantidad de existencias no puede ser menor a cero."
                    lineas[idx] = f"    {desc_stripped} {new_qty}\n"
                    item_encontrado = True
                    break
                except ValueError:
                    continue
                    
        if not item_encontrado:
            if cambio < 0:
                return False, "El producto no existe y no se pueden restar unidades."
            lineas.append(f"    {desc_stripped} {cambio}\n")
            
        # Re-filtrar y limpiar líneas vacías o rotas
        formatted_lines = []
        for line in lineas:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            partes = line_stripped.rsplit(' ', 1)
            if len(partes) == 2:
                try:
                    int(partes[1])
                    formatted_lines.append(line)
                except ValueError:
                    continue
                    
        # Ordenar alfabéticamente por descripción
        formatted_lines.sort(key=lambda x: x.strip().rsplit(' ', 1)[0].lower())
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(formatted_lines)
            
        return True, "Stock ajustado correctamente."
    except Exception as e:
        return False, f"Error al ajustar stock en archivo: {e}"

def transfer_product_stock(producto, origen, destino, cantidad):
    producto_stripped = producto.strip()
    if cantidad <= 0:
        return False, "La cantidad a trasladar debe ser mayor a cero."
        
    if origen == destino:
        return False, "El origen y el destino no pueden ser la misma ubicación."
        
    allowed_sources = ["local.txt", "local_2.txt", "bodegac.txt"]
    if origen not in allowed_sources or destino not in allowed_sources:
        return False, "Ubicaciones de origen o destino no válidas."
        
    try:
        # 1. Leer stock de origen y verificar disponibilidad
        origen_stock = parse_stock_file(origen)
        if producto_stripped not in origen_stock:
            return False, f"El producto '{producto_stripped}' no existe en la ubicación de origen: {origen}."
        if origen_stock[producto_stripped] < cantidad:
            return False, f"Stock insuficiente en la ubicación de origen: {origen}. Disponible: {origen_stock[producto_stripped]}, requerido: {cantidad}."
            
        # 2. Restar en origen
        success_orig, msg_orig = adjust_product_stock(origen, producto_stripped, -cantidad)
        if not success_orig:
            return False, f"Error al restar del origen: {msg_orig}"
            
        # 3. Sumar en destino
        success_dest, msg_dest = adjust_product_stock(destino, producto_stripped, cantidad)
        if not success_dest:
            # Revertir resta en origen si falla la suma
            adjust_product_stock(origen, producto_stripped, cantidad)
            return False, f"Error al sumar al destino: {msg_dest}"
            
        return True, "Traslado realizado con éxito."
    except Exception as e:
        return False, f"Error al procesar traslado: {e}"

def save_customer(nombre, contacto):
    nombre = nombre.strip()
    contacto = contacto.strip()
    if not nombre or nombre.lower() == "cliente general":
        return True
    
    archivo_clientes = "clientes.csv"
    clientes = {}
    try:
        if os.path.exists(archivo_clientes):
            with open(archivo_clientes, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # header
                for row in reader:
                    if row and len(row) >= 1:
                        clientes[row[0].strip()] = row[1].strip() if len(row) > 1 else ""
                        
        if nombre not in clientes or clientes[nombre] != contacto:
            clientes[nombre] = contacto
            with open(archivo_clientes, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Nombre", "Contacto"])
                for n, c in clientes.items():
                    writer.writerow([n, c])
        return True
    except Exception as e:
        print(f"Error al guardar cliente: {e}")
        return False

def get_caja_filenames(local_file):
    if not local_file or local_file == "local.txt":
        return "caja_registros.csv", "movimientos_caja.csv"
    elif local_file == "local_2.txt":
        return "caja_registros_local_2.csv", "movimientos_caja_local_2.csv"
    elif local_file == "bodegac.txt":
        return "caja_registros_bodegac.csv", "movimientos_caja_bodegac.csv"
    else:
        # Sanitizar nombre para cualquier otro local inesperado
        name_clean = "".join(c for c in local_file if c.isalnum() or c in "._-").replace(".txt", "")
        return f"caja_registros_{name_clean}.csv", f"movimientos_caja_{name_clean}.csv"

def get_conteo_filename(local_file):
    if not local_file or local_file == "local.txt":
        return "conteo_caja_historial.csv"
    elif local_file == "local_2.txt":
        return "conteo_caja_historial_local_2.csv"
    elif local_file == "bodegac.txt":
        return "conteo_caja_historial_bodegac.csv"
    else:
        name_clean = "".join(c for c in local_file if c.isalnum() or c in "._-").replace(".txt", "")
        return f"conteo_caja_historial_{name_clean}.csv"

def obtener_pagos_electronicos_del_dia(fecha_str, local_file=None):
    total_electronico = 0.0
    ventas_procesadas = set()
    archivo_ventas = "registro_ventas.csv"
    if not os.path.exists(archivo_ventas):
        return 0.0
    try:
        with open(archivo_ventas, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return 0.0
            
            estado_idx = header.index("Estado") if "Estado" in header else -1
            medio_pago_idx = header.index("MedioPago") if "MedioPago" in header else 10
            id_venta_idx = header.index("ID_Venta") if "ID_Venta" in header else 1
            total_venta_idx = header.index("TotalVenta") if "TotalVenta" in header else 6
            timestamp_idx = header.index("Timestamp") if "Timestamp" in header else 0
            archivo_origen_idx = header.index("ArchivoOrigen") if "ArchivoOrigen" in header else -1

            for row in reader:
                if not row or len(row) <= max(timestamp_idx, id_venta_idx, medio_pago_idx):
                    continue
                if not row[timestamp_idx].startswith(fecha_str):
                    continue

                if estado_idx != -1 and len(row) > estado_idx and row[estado_idx] == "Anulada":
                    continue

                if local_file and archivo_origen_idx != -1 and len(row) > archivo_origen_idx and row[archivo_origen_idx] != local_file:
                    continue

                try:
                    id_venta = row[id_venta_idx]
                    if id_venta in ventas_procesadas:
                        continue

                    medio_pago_str = row[medio_pago_idx]
                    if ":" in medio_pago_str:
                        pagos = medio_pago_str.split(", ")
                        for pago in pagos:
                            if "Efectivo" not in pago:
                                monto_str_part = pago.split("$")[-1].strip()
                                monto_limpio = re.sub(r"[^\d,.]", "", monto_str_part)
                                if not monto_limpio:
                                    continue
                                if "," in monto_limpio and ("." not in monto_limpio or monto_limpio.rfind(",") > monto_limpio.rfind(".")):
                                    monto_procesado = monto_limpio.replace(".", "").replace(",", ".")
                                else:
                                    monto_procesado = monto_limpio.replace(",", "")
                                if monto_procesado:
                                    total_electronico += float(monto_procesado)
                    else:
                        if medio_pago_str.strip() not in ["Efectivo", "N/A", ""]:
                            total_venta_item = float(row[total_venta_idx])
                            total_electronico += total_venta_item
                    ventas_procesadas.add(id_venta)
                except (ValueError, IndexError, TypeError):
                    continue
        return total_electronico
    except Exception as e:
        print(f"Error obteniendo pagos electrónicos: {e}")
        return 0.0

def get_caja_status(fecha_str, local_file=None):
    archivo_registros, archivo_movimientos = get_caja_filenames(local_file)
    
    # Valores por defecto si no está iniciado
    caja_data = {
        "iniciado": False,
        "cerrado": False,
        "dinero_inicial": 0.0,
        "base": 0.0,
        "pagos_electronicos": 0.0,
        "dinero_en_caja": 0.0,
        "total_ventas": 0.0,
        "total_movimientos": 0.0,
        "efectivo_esperado": 0.0,
        "diferencia": 0.0
    }
    
    # 1. Buscar si hay registro de caja para esta fecha
    if os.path.exists(archivo_registros):
        try:
            with open(archivo_registros, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Fecha") == fecha_str:
                        caja_data["iniciado"] = True
                        caja_data["dinero_inicial"] = float(row.get("DineroInicial") or 0.0)
                        caja_data["base"] = float(row.get("Base") or 0.0)
                        caja_data["pagos_electronicos"] = float(row.get("PagosElectronicos") or 0.0)
                        caja_data["dinero_en_caja"] = float(row.get("DineroEnCaja") or 0.0)
                        caja_data["total_ventas"] = float(row.get("TotalVentas") or 0.0)
                        caja_data["total_movimientos"] = float(row.get("TotalMovimientos") or 0.0)
                        caja_data["efectivo_esperado"] = float(row.get("EfectivoEsperado") or 0.0)
                        caja_data["diferencia"] = float(row.get("Diferencia") or 0.0)
                        
                        if float(row.get("DineroEnCaja") or 0.0) > 0.0 or float(row.get("Diferencia") or 0.0) != 0.0:
                            caja_data["cerrado"] = True
                        break
        except Exception as e:
            print(f"Error leyendo {archivo_registros}: {e}")
 
    # 2. Obtener movimientos del día
    movimientos = []
    total_movimientos = 0.0
    if os.path.exists(archivo_movimientos):
        try:
            with open(archivo_movimientos, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Timestamp", "").startswith(fecha_str):
                        try:
                            monto = float(row.get("Monto") or 0.0)
                            total_movimientos += monto
                            movimientos.append({
                                "timestamp": row["Timestamp"],
                                "tipo": row["Tipo"],
                                "descripcion": row["Descripcion"],
                                "monto": monto
                            })
                        except ValueError:
                            continue
        except Exception as e:
            print(f"Error leyendo {archivo_movimientos}: {e}")
            
    # 3. Obtener ventas del día (completadas)
    total_ventas = 0.0
    ventas_del_dia = []
    archivo_ventas = "registro_ventas.csv"
    if os.path.exists(archivo_ventas):
        try:
            with open(archivo_ventas, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Timestamp", "").startswith(fecha_str):
                        estado = row.get("Estado", "Completada")
                        if estado == "Completada":
                            if local_file and row.get("ArchivoOrigen") != local_file:
                                continue
                            try:
                                total_ventas += float(row.get("TotalVenta") or 0.0)
                                hora = row.get("Timestamp", "").split(" ")[1] if " " in row.get("Timestamp", "") else ""
                                ventas_del_dia.append({
                                    "hora": hora,
                                    "id_venta": row.get("ID_Venta", ""),
                                    "descripcion": row.get("Descripcion", ""),
                                    "cantidad": int(row.get("Cantidad") or 0),
                                    "precio_unitario": float(row.get("PrecioUnitario") or 0.0),
                                    "total": float(row.get("TotalVenta") or 0.0),
                                    "medio_pago": row.get("MedioPago", ""),
                                    "cliente": row.get("Cliente", "")
                                })
                            except ValueError:
                                continue
        except Exception as e:
            print(f"Error leyendo registro_ventas.csv: {e}")
 
    if caja_data["iniciado"] and not caja_data["cerrado"]:
        caja_data["total_ventas"] = total_ventas
        caja_data["total_movimientos"] = total_movimientos
        caja_data["pagos_electronicos"] = obtener_pagos_electronicos_del_dia(fecha_str, local_file)
        caja_data["efectivo_esperado"] = (caja_data["dinero_inicial"] + caja_data["base"] + total_ventas + total_movimientos) - caja_data["pagos_electronicos"]
        
    return {
        "status": caja_data,
        "movimientos": movimientos,
        "ventas": ventas_del_dia
    }


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-PIN')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path == '/' or path == '':
            self.send_response(301)
            self.send_header('Location', '/ventas.html')
            self.end_headers()
            return

        allowed_files = [
            '/existencias.html',
            '/ventas.html',
            '/Logo1.PNG',
            '/bodegac.txt',
            '/local.txt',
            '/local_2.txt'
        ]

        if not path.startswith('/api/'):
            if path not in allowed_files:
                self.send_error(403, "Acceso prohibido por políticas de seguridad")
                return
            super().do_GET()
            return

        # --- RUTAS DE LA API (GET) ---
        
        if path == '/api/status':
            self.send_json({
                "status": "ok",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files": ["bodegac.txt", "local.txt", "local_2.txt"]
            })
            return

        elif path == '/api/productos':
            local_stock = parse_stock_file("local.txt")
            local_2_stock = parse_stock_file("local_2.txt")
            bodega_stock = parse_stock_file("bodegac.txt")
            costs = parse_cost_file("dbcst.txt")
            last_prices = obtener_ultimos_precios()
            
            all_descs = sorted(list(set(local_stock.keys()) | set(local_2_stock.keys()) | set(bodega_stock.keys()) | set(costs.keys())))
            
            productos = []
            for desc in all_descs:
                productos.append({
                    "descripcion": desc,
                    "costo": costs.get(desc, 0.0),
                    "precio_sugerido": last_prices.get(desc, 0.0),
                    "stock": {
                        "local.txt": local_stock.get(desc, 0),
                        "local_2.txt": local_2_stock.get(desc, 0),
                        "bodegac.txt": bodega_stock.get(desc, 0)
                    }
                })
            self.send_json({"productos": productos})
            return

        elif path == '/api/clientes':
            clientes = []
            archivo_clientes = "clientes.csv"
            if os.path.exists(archivo_clientes):
                try:
                    with open(archivo_clientes, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get("Nombre"):
                                clientes.append({
                                    "nombre": row["Nombre"].strip(),
                                    "contacto": row.get("Contacto", "").strip()
                                })
                except Exception as e:
                    print(f"Error leyendo clientes: {e}")
            self.send_json({"clientes": clientes})
            return

        elif path == '/api/caja/status':
            fecha = query_params.get("fecha", [datetime.now().strftime("%Y-%m-%d")])[0]
            local_file = query_params.get("local", [None])[0]
            status_data = get_caja_status(fecha, local_file)
            self.send_json(status_data)
            return

        elif path == '/api/reportes':
            client_pin = self.headers.get('X-Admin-PIN') or query_params.get("pin", [""])[0]
            if client_pin != ADMIN_PIN:
                self.send_json({"error": "No autorizado. PIN de administrador inválido."}, 401)
                return
                
            fecha_inicio = query_params.get("fecha_inicio", [datetime.now().strftime("%Y-%m-%d")])[0]
            fecha_fin = query_params.get("fecha_fin", [datetime.now().strftime("%Y-%m-%d")])[0]
            
            total_ventas = 0.0
            total_ganancia = 0.0
            sales_count = 0
            ventas_por_local = {}
            ventas_por_pago = {}
            lista_ventas = []
            
            archivo_ventas = "registro_ventas.csv"
            if os.path.exists(archivo_ventas):
                try:
                    with open(archivo_ventas, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            ts = row.get("Timestamp", "")
                            if not ts:
                                continue
                            date_part = ts.split(" ")[0]
                            if fecha_inicio <= date_part <= fecha_fin:
                                estado = row.get("Estado", "Completada")
                                try:
                                    cant = int(row.get("Cantidad") or 0)
                                    precio = float(row.get("PrecioUnitario") or 0.0)
                                    total_item = float(row.get("TotalVenta") or 0.0)
                                    ganancia_item = float(row.get("Ganancia") or 0.0)
                                    origen = row.get("ArchivoOrigen", "Desconocido")
                                    pago = row.get("MedioPago", "Efectivo")
                                    
                                    sale_obj = {
                                        "timestamp": ts,
                                        "id_venta": row.get("ID_Venta"),
                                        "descripcion": row.get("Descripcion"),
                                        "cantidad": cant,
                                        "costo": float(row.get("CostoUnitario") or 0.0),
                                        "precio": precio,
                                        "total": total_item,
                                        "ganancia": ganancia_item,
                                        "origen": origen,
                                        "cliente": row.get("Cliente"),
                                        "medio_pago": pago,
                                        "estado": estado
                                    }
                                    lista_ventas.append(sale_obj)
                                    
                                    if estado == "Completada":
                                        total_ventas += total_item
                                        total_ganancia += ganancia_item
                                        sales_count += 1
                                        
                                        ventas_por_local[origen] = ventas_por_local.get(origen, 0.0) + total_item
                                        ventas_por_pago[pago] = ventas_por_pago.get(pago, 0.0) + total_item
                                except ValueError:
                                    continue
                except Exception as e:
                    print(f"Error generando reporte: {e}")
                    
            lista_ventas.reverse()
            
            self.send_json({
                "rango": {"inicio": fecha_inicio, "fin": fecha_fin},
                "total_ventas": total_ventas,
                "total_ganancia": total_ganancia,
                "sales_count": sales_count,
                "por_local": ventas_por_local,
                "por_medio_pago": ventas_por_pago,
                "ventas": lista_ventas
            })
            return

        else:
            self.send_error(404, "Endpoint no encontrado")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if not path.startswith('/api/'):
            self.send_error(403, "Acceso prohibido")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body_data) if body_data else {}
        except json.JSONDecodeError:
            self.send_json({"error": "JSON con formato inválido"}, 400)
            return

        # --- RUTAS DE LA API (POST) ---

        if path == '/api/clientes':
            nombre = data.get("nombre", "").strip()
            contacto = data.get("contacto", "").strip()
            if not nombre:
                self.send_json({"error": "El nombre del cliente es requerido."}, 400)
                return
            success = save_customer(nombre, contacto)
            if success:
                self.send_json({"message": "Cliente registrado correctamente."})
            else:
                self.send_json({"error": "No se pudo guardar el cliente."}, 500)

        elif path == '/api/ventas':
            items = data.get("items", [])
            cliente = data.get("cliente", "Regular").strip()
            medio_pago = data.get("medio_pago", "Efectivo").strip()
            archivo_origen = data.get("archivo_origen", "local.txt").strip()
            id_venta = data.get("id_venta", "").strip()

            if not items:
                self.send_json({"error": "La venta debe contener al menos un producto."}, 400)
                return
                
            allowed_sources = ["local.txt", "local_2.txt", "bodegac.txt"]
            if archivo_origen not in allowed_sources:
                self.send_json({"error": f"Origen de inventario no válido: {archivo_origen}"}, 400)
                return

            success, msg = deduct_stock(archivo_origen, items)
            if not success:
                self.send_json({"error": msg}, 400)
                return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not id_venta:
                id_venta = datetime.now().strftime("%Y%m%d%H%M%S")

            archivo_ventas = "registro_ventas.csv"
            if not os.path.exists(archivo_ventas):
                try:
                    with open(archivo_ventas, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            "Timestamp", "ID_Venta", "Descripcion", "Cantidad",
                            "CostoUnitario", "PrecioUnitario", "TotalVenta", "Ganancia",
                            "ArchivoOrigen", "Cliente", "MedioPago", "Estado"
                        ])
                except Exception as e:
                    print(f"Error creando registro_ventas: {e}")

            try:
                with open(archivo_ventas, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    for item in items:
                        desc = item["descripcion"].strip()
                        cant = int(item["cantidad"])
                        precio = float(item["precio"])
                        costo = float(item["costo"])
                        total_item = cant * precio
                        ganancia_item = total_item - (cant * costo)
                        
                        writer.writerow([
                            timestamp,
                            id_venta,
                            desc,
                            cant,
                            f"{costo:.2f}",
                            f"{precio:.2f}",
                            f"{total_item:.2f}",
                            f"{ganancia_item:.2f}",
                            archivo_origen,
                            cliente,
                            medio_pago,
                            "Completada"
                        ])
                        
                if cliente and cliente != "Regular" and cliente != "Cliente General":
                    save_customer(cliente, "")
                    
                self.send_json({
                    "message": "Venta registrada con éxito.",
                    "id_venta": id_venta,
                    "timestamp": timestamp
                })
            except Exception as e:
                self.send_json({"error": f"Error al registrar la venta en archivo: {e}"}, 500)

        elif path == '/api/ventas/anular':
            client_pin = self.headers.get('X-Admin-PIN') or data.get("pin", "")
            if client_pin != ADMIN_PIN:
                self.send_json({"error": "No autorizado. PIN de administrador inválido."}, 401)
                return
                
            id_venta = data.get("id_venta", "").strip()
            if not id_venta:
                self.send_json({"error": "ID de venta requerido para anulación."}, 400)
                return

            archivo_ventas = "registro_ventas.csv"
            if not os.path.exists(archivo_ventas):
                self.send_json({"error": "El registro de ventas no existe."}, 400)
                return

            try:
                with open(archivo_ventas, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    rows = list(reader)

                updated_rows = []
                matching_found = False
                items_restaurados = []

                for row in rows:
                    if not row or len(row) < 12:
                        updated_rows.append(row)
                        continue
                        
                    if row[1] == id_venta:
                        matching_found = True
                        desc = row[2]
                        try:
                            cant = int(row[3])
                        except ValueError:
                            cant = 0
                        archivo_origen = row[8]
                        
                        success, msg = restore_stock(archivo_origen, desc, cant)
                        if success:
                            items_restaurados.append(f"{desc} ({cant} unds) -> {archivo_origen}")
                        else:
                            print(f"Error restaurando stock de {desc}: {msg}")
                    else:
                        updated_rows.append(row)

                if not matching_found:
                    self.send_json({"error": "No se encontró la venta o ya fue anulada."}, 404)
                    return

                with open(archivo_ventas, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if header:
                        writer.writerow(header)
                    writer.writerows(updated_rows)

                self.send_json({
                    "message": "Venta anulada y stock devuelto con éxito.",
                    "detalles": items_restaurados
                })
            except Exception as e:
                self.send_json({"error": f"Error inesperado al anular la venta: {e}"}, 500)

        elif path == '/api/caja/iniciar':
            fecha = data.get("fecha", "").strip()
            local_file = data.get("local", "").strip() or "local.txt"
            try:
                dinero_inicial = float(data.get("dinero_inicial", 0.0))
                base = float(data.get("base", 0.0))
            except ValueError:
                self.send_json({"error": "Dinero inicial y base deben ser números válidos."}, 400)
                return

            if not fecha:
                self.send_json({"error": "La fecha es requerida."}, 400)
                return

            archivo_registros, _ = get_caja_filenames(local_file)
            if os.path.exists(archivo_registros):
                try:
                    with open(archivo_registros, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get("Fecha") == fecha:
                                self.send_json({"error": f"La caja para el día {fecha} ya ha sido iniciada."}, 400)
                                return
                except Exception as e:
                    print(f"Error verificando caja existente: {e}")

            if not os.path.exists(archivo_registros):
                try:
                    with open(archivo_registros, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            "Fecha", "DineroInicial", "Base", "PagosElectronicos",
                            "DineroEnCaja", "TotalVentas", "TotalMovimientos",
                            "EfectivoEsperado", "Diferencia"
                        ])
                except Exception as e:
                    print(f"Error creando {archivo_registros}: {e}")

            try:
                with open(archivo_registros, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([fecha, dinero_inicial, base, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                self.send_json({"message": "Día de caja iniciado correctamente."})
            except Exception as e:
                self.send_json({"error": f"Error al iniciar caja: {e}"}, 500)

        elif path == '/api/caja/movimiento':
            tipo = data.get("tipo", "").strip()
            descripcion = data.get("descripcion", "").strip()
            local_file = data.get("local", "").strip() or "local.txt"
            try:
                monto = float(data.get("monto", 0.0))
            except ValueError:
                self.send_json({"error": "El monto debe ser un número válido."}, 400)
                return

            if not tipo or not descripcion:
                self.send_json({"error": "Tipo y descripción son requeridos."}, 400)
                return

            if tipo in ["Gasto", "Préstamo/Retiro"]:
                monto = -abs(monto)
            elif tipo in ["Abono/Ingreso", "Abono Préstamo"]:
                monto = abs(monto)

            _, archivo_movimientos = get_caja_filenames(local_file)
            if not os.path.exists(archivo_movimientos):
                try:
                    with open(archivo_movimientos, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Timestamp", "Tipo", "Descripcion", "Monto"])
                except Exception as e:
                    print(f"Error creando {archivo_movimientos}: {e}")

            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(archivo_movimientos, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, tipo, descripcion, monto])
                self.send_json({
                    "message": "Movimiento registrado con éxito.",
                    "movimiento": {
                        "timestamp": timestamp,
                        "tipo": tipo,
                        "descripcion": descripcion,
                        "monto": monto
                    }
                })
            except Exception as e:
                self.send_json({"error": f"Error al registrar movimiento: {e}"}, 500)

        elif path == '/api/caja/movimiento/eliminar':
            timestamp = data.get("timestamp", "").strip()
            local_file = data.get("local", "").strip() or "local.txt"
            if not timestamp:
                self.send_json({"error": "Timestamp del movimiento requerido."}, 400)
                return

            _, archivo_movimientos = get_caja_filenames(local_file)
            if not os.path.exists(archivo_movimientos):
                self.send_json({"error": "No existen movimientos registrados."}, 400)
                return

            try:
                with open(archivo_movimientos, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    rows = list(reader)

                updated_rows = []
                eliminado = False
                for row in rows:
                    if row and row[0] == timestamp:
                        eliminado = True
                        continue
                    updated_rows.append(row)

                if not eliminado:
                    self.send_json({"error": "Movimiento no encontrado."}, 404)
                    return

                with open(archivo_movimientos, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if header:
                        writer.writerow(header)
                    writer.writerows(updated_rows)

                self.send_json({"message": "Movimiento eliminado con éxito."})
            except Exception as e:
                self.send_json({"error": f"Error al eliminar movimiento: {e}"}, 500)

        elif path == '/api/caja/cerrar':
            fecha = data.get("fecha", "").strip()
            local_file = data.get("local", "").strip() or "local.txt"
            try:
                dinero_real_caja = float(data.get("dinero_real_caja", 0.0))
                pagos_electronicos = float(data.get("pagos_electronicos", 0.0))
            except ValueError:
                self.send_json({"error": "Dinero real y pagos electrónicos deben ser números."}, 400)
                return

            if not fecha:
                self.send_json({"error": "La fecha es requerida."}, 400)
                return

            archivo_registros, archivo_movimientos = get_caja_filenames(local_file)
            if not os.path.exists(archivo_registros):
                self.send_json({"error": f"El archivo de registros de caja no existe para este local ({local_file})."}, 400)
                return

            try:
                dinero_inicial = 0.0
                base = 0.0
                dia_encontrado = False

                with open(archivo_registros, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                for row in rows:
                    if row.get("Fecha") == fecha:
                        dinero_inicial = float(row.get("DineroInicial") or 0.0)
                        base = float(row.get("Base") or 0.0)
                        dia_encontrado = True
                        break

                if not dia_encontrado:
                    self.send_json({"error": f"No se encontró un inicio de día registrado para la fecha {fecha}."}, 404)
                    return

                total_movimientos = 0.0
                if os.path.exists(archivo_movimientos):
                    with open(archivo_movimientos, "r", encoding="utf-8") as f:
                        m_reader = csv.DictReader(f)
                        for m_row in m_reader:
                            if m_row.get("Timestamp", "").startswith(fecha):
                                try:
                                    total_movimientos += float(m_row.get("Monto") or 0.0)
                                except ValueError:
                                    continue

                total_ventas = 0.0
                archivo_ventas = "registro_ventas.csv"
                if os.path.exists(archivo_ventas):
                    with open(archivo_ventas, "r", encoding="utf-8") as f:
                        v_reader = csv.DictReader(f)
                        for v_row in v_reader:
                            if v_row.get("Timestamp", "").startswith(fecha):
                                estado = v_row.get("Estado", "Completada")
                                if estado == "Completada":
                                    if local_file and v_row.get("ArchivoOrigen") != local_file:
                                        continue
                                    try:
                                        total_ventas += float(v_row.get("TotalVenta") or 0.0)
                                    except ValueError:
                                        continue

                efectivo_esperado = (dinero_inicial + base + total_ventas + total_movimientos) - pagos_electronicos
                diferencia = dinero_real_caja - (efectivo_esperado - base)

                lineas_nuevas = []
                with open(archivo_registros, "r", encoding="utf-8") as f:
                    csv_reader = csv.reader(f)
                    header = next(csv_reader, None)
                    lineas_nuevas.append(header)
                    for row in csv_reader:
                        if row and row[0] == fecha:
                            row = [
                                fecha,
                                f"{dinero_inicial:.2f}",
                                f"{base:.2f}",
                                f"{pagos_electronicos:.2f}",
                                f"{dinero_real_caja:.2f}",
                                f"{total_ventas:.2f}",
                                f"{total_movimientos:.2f}",
                                f"{efectivo_esperado:.2f}",
                                f"{diferencia:.2f}"
                            ]
                        lineas_nuevas.append(row)

                with open(archivo_registros, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(lineas_nuevas)

                self.send_json({
                    "message": "Cierre de caja guardado con éxito.",
                    "cuadre": {
                        "dinero_inicial": dinero_inicial,
                        "base": base,
                        "total_ventas": total_ventas,
                        "total_movimientos": total_movimientos,
                        "pagos_electronicos": pagos_electronicos,
                        "efectivo_esperado": efectivo_esperado,
                        "dinero_real_caja": dinero_real_caja,
                        "diferencia": diferencia
                    }
                })
            except Exception as e:
                self.send_json({"error": f"Error al procesar el cierre de caja: {e}"}, 500)

        elif path == '/api/caja/conteo':
            local_file = data.get("local", "").strip() or "local.txt"
            try:
                total = float(data.get("total", 0.0))
            except ValueError:
                self.send_json({"error": "El total debe ser un número válido."}, 400)
                return
            detalle = data.get("detalle", "").strip()
            
            archivo_conteo = get_conteo_filename(local_file)
            if not os.path.exists(archivo_conteo):
                try:
                    with open(archivo_conteo, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Timestamp", "TotalContado", "DetalleConteo"])
                except Exception as e:
                    print(f"Error creando {archivo_conteo}: {e}")
                    
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(archivo_conteo, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, total, detalle])
                self.send_json({"message": "Conteo de efectivo registrado con éxito."})
            except Exception as e:
                self.send_json({"error": f"Error al registrar el conteo: {e}"}, 500)

        elif path == '/api/inventario/ajustar':
            client_pin = self.headers.get('X-Admin-PIN') or data.get("pin", "")
            if client_pin != ADMIN_PIN:
                self.send_json({"error": "No autorizado. PIN de administrador inválido."}, 401)
                return
            
            producto = data.get("producto", "").strip()
            archivo = data.get("archivo", "").strip()
            try:
                cambio = int(data.get("cambio", 0))
            except ValueError:
                self.send_json({"error": "El valor de cambio debe ser un número entero."}, 400)
                return
                
            allowed_files = ["local.txt", "local_2.txt", "bodegac.txt"]
            if archivo not in allowed_files:
                self.send_json({"error": f"Archivo de stock no permitido: {archivo}"}, 400)
                return
                
            if not producto:
                self.send_json({"error": "El producto es requerido."}, 400)
                return
                
            success, msg = adjust_product_stock(archivo, producto, cambio)
            if success:
                self.send_json({"message": msg})
            else:
                self.send_json({"error": msg}, 400)

        elif path == '/api/inventario/trasladar':
            client_pin = self.headers.get('X-Admin-PIN') or data.get("pin", "")
            if client_pin != ADMIN_PIN:
                self.send_json({"error": "No autorizado. PIN de administrador inválido."}, 401)
                return
                
            producto = data.get("producto", "").strip()
            origen = data.get("origen", "").strip()
            destino = data.get("destino", "").strip()
            try:
                cantidad = int(data.get("cantidad", 0))
            except ValueError:
                self.send_json({"error": "La cantidad debe ser un número entero."}, 400)
                return
                
            if not producto:
                self.send_json({"error": "El producto es requerido."}, 400)
                return
                
            success, msg = transfer_product_stock(producto, origen, destino, cantidad)
            if success:
                self.send_json({"message": msg})
            else:
                self.send_json({"error": msg}, 400)

        else:
            self.send_error(404, "Endpoint no encontrado")


def run_server():
    global PORT
    local_ip = get_local_ip()
    socketserver.TCPServer.allow_reuse_address = True
    
    httpd = None
    while PORT < 8100:
        try:
            server_address = ("", PORT)
            httpd = socketserver.TCPServer(server_address, CustomHandler)
            break
        except OSError as e:
            if e.errno == 48:  # Address already in use
                PORT += 1
            else:
                print(f"\n[!] Error inesperado al iniciar el servidor: {e}")
                sys.exit(1)
                
    if not httpd:
        print("[!] No se encontró ningún puerto libre en el rango 8000-8100.")
        sys.exit(1)
        
    try:
        with httpd:
            print("=" * 70)
            print(" 🚀 SERVIDOR DE INVENTARIO Y POS INICIADO CORRECTAMENTE")
            print("=" * 70)
            print(f"💻 En esta computadora accede aquí:")
            print(f"   👉 http://localhost:{PORT}/ventas.html  (Punto de Venta)")
            print(f"   👉 http://localhost:{PORT}/existencias.html  (Visor de Stock)")
            print()
            print(f"📱 En tu CELULAR o en otras computadoras de la red Wi-Fi accede aquí:")
            if local_ip != '127.0.0.1':
                print(f"   👉 http://{local_ip}:{PORT}/ventas.html")
            else:
                print("   [!] No se detectó IP local activa. Asegúrate de estar conectado a Wi-Fi.")
            print("=" * 70)
            print("Presiona Ctrl + C en esta terminal para detener el servidor.")
            print("-" * 70)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[i] Deteniendo servidor de inventario. ¡Hasta luego!")
        sys.exit(0)

if __name__ == "__main__":
    run_server()
