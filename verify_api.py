import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import csv
import sys
from datetime import datetime

# Puerto temporal para pruebas
TEST_PORT = 8089
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

def run_test():
    print("=== INICIANDO PRUEBAS DE VERIFICACIÓN DE API CON DELTA ===")
    
    # 1. Crear copia temporal del servidor configurada en TEST_PORT
    with open("servidor.py", "r", encoding="utf-8") as f:
        original_code = f.read()
        
    test_code = original_code.replace("PORT = 8000", f"PORT = {TEST_PORT}")
    
    with open("servidor_test.py", "w", encoding="utf-8") as f:
        f.write(test_code)
        
    print(f"Iniciando servidor temporal en puerto {TEST_PORT}...")
    server_process = subprocess.Popen([sys.executable, "servidor_test.py"])
    
    # Esperar a que inicie
    time.sleep(1.5)
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    client_name = "Cliente Pruebas API"
    client_phone = "999999"
    initiated_by_test = False
    
    try:
        # Helper para hacer GET
        def get_req(path, pin=None):
            req = urllib.request.Request(f"{BASE_URL}{path}")
            if pin:
                req.add_header("X-Admin-PIN", pin)
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
                
        # Helper para hacer POST
        def post_req(path, data, pin=None):
            req = urllib.request.Request(
                f"{BASE_URL}{path}",
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            if pin:
                req.add_header("X-Admin-PIN", pin)
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))

        # Helper para esperar error HTTP POST
        def post_req_err(path, data, expected_code, pin=None):
            req = urllib.request.Request(
                f"{BASE_URL}{path}",
                data=json.dumps(data).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            if pin:
                req.add_header("X-Admin-PIN", pin)
            try:
                with urllib.request.urlopen(req) as response:
                    raise AssertionError(f"Se esperaba HTTP {expected_code} pero la petición fue exitosa.")
            except urllib.error.HTTPError as e:
                assert e.code == expected_code, f"Se esperaba HTTP {expected_code} pero se obtuvo {e.code}"
                return json.loads(e.read().decode('utf-8'))

        # --- PRUEBA 1: GET /api/status ---
        print("\nPrueba 1: Consultando status...")
        status = get_req("/api/status")
        print("Status retornado:", status)
        assert status["status"] == "ok"
        
        # --- PRUEBA 2: GET /api/productos ---
        print("\nPrueba 2: Consultando lista de productos...")
        prod_data = get_req("/api/productos")
        productos = prod_data["productos"]
        print(f"Se encontraron {len(productos)} productos únicos.")
        aceitera = next((p for p in productos if p["descripcion"] == "Aceitera El-093"), None)
        assert aceitera is not None, "No se encontró el producto 'Aceitera El-093'"
        original_stock_local = aceitera["stock"]["local.txt"]
        original_stock_local2 = aceitera["stock"]["local_2.txt"]
        original_stock_bodega = aceitera["stock"]["bodegac.txt"]
        original_cost = aceitera["costo"]
        print(f"Stock original de Aceitera El-093 en local.txt: {original_stock_local}, local_2.txt: {original_stock_local2}, bodegac.txt: {original_stock_bodega}, Costo: {original_cost}")
        
        # --- PRUEBA 3: GET /api/clientes ---
        print("\nPrueba 3: Consultando clientes...")
        clientes_data = get_req("/api/clientes")
        print(f"Se encontraron {len(clientes_data['clientes'])} clientes.")
        
        # --- PRUEBA 4: POST /api/clientes ---
        print("\nPrueba 4: Registrando cliente de prueba...")
        res_client = post_req("/api/clientes", {"nombre": client_name, "contacto": client_phone})
        print("Respuesta registro cliente:", res_client)
        
        # Verificar en clientes.csv
        with open("clientes.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            test_client_row = next((r for r in rows if r and r[0] == client_name), None)
            assert test_client_row is not None
            print("Cliente registrado guardado en CSV:", test_client_row)

        # --- PRUEBA 5: Verificar / Iniciar Caja ---
        print("\nPrueba 5: Consultando estado inicial de caja para hoy...")
        initial_caja = get_req(f"/api/caja/status?fecha={today_date}")
        initial_iniciado = initial_caja["status"]["iniciado"]
        initial_ventas = initial_caja["status"]["total_ventas"]
        initial_movimientos = initial_caja["status"]["total_movimientos"]
        print(f"Caja hoy iniciada?: {initial_iniciado}, Ventas acumuladas hoy: {initial_ventas}, Movimientos acumulados hoy: {initial_movimientos}")

        if not initial_iniciado:
            print("Iniciando caja de prueba para el día de hoy...")
            res_caja_init = post_req("/api/caja/iniciar", {
                "fecha": today_date,
                "dinero_inicial": 250000,
                "base": 100000
            })
            print("Respuesta iniciar caja:", res_caja_init)
            initiated_by_test = True
            # Recargar estado caja
            initial_caja = get_req(f"/api/caja/status?fecha={today_date}")
            initial_ventas = initial_caja["status"]["total_ventas"]
            initial_movimientos = initial_caja["status"]["total_movimientos"]

        # --- PRUEBA 6: POST /api/ventas (Registrar Venta) ---
        print("\nPrueba 6: Registrando venta de prueba...")
        sale_payload = {
            "cliente": client_name,
            "medio_pago": "Nequi",
            "archivo_origen": "local.txt",
            "items": [
                {
                    "descripcion": "Aceitera El-093",
                    "cantidad": 1,
                    "precio": 18000,
                    "costo": original_cost
                }
            ]
        }
        res_sale = post_req("/api/ventas", sale_payload)
        print("Respuesta registro venta:", res_sale)
        id_venta = res_sale["id_venta"]
        
        # Verificar reducción de stock
        prod_data_2 = get_req("/api/productos")
        aceitera_2 = next((p for p in prod_data_2["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        new_stock = aceitera_2["stock"]["local.txt"]
        print(f"Nuevo stock de Aceitera El-093: {new_stock}")
        assert new_stock == original_stock_local - 1, "El stock no se redujo correctamente"
        
        # --- PRUEBA 7: POST /api/caja/movimiento ---
        print("\nPrueba 7: Registrando gasto de prueba...")
        res_mov = post_req("/api/caja/movimiento", {
            "tipo": "Gasto",
            "descripcion": "Café de prueba",
            "monto": 4500
        })
        print("Respuesta registro movimiento:", res_mov)
        mov_timestamp = res_mov["movimiento"]["timestamp"]
        
        # Consultar estado de caja actualizado
        caja_status_2 = get_req(f"/api/caja/status?fecha={today_date}")
        print("Estado caja actualizado (ventas/movimientos):", caja_status_2["status"])
        
        # Verificar incremento relativo
        assert caja_status_2["status"]["total_ventas"] == initial_ventas + 18000.0, "La venta no se sumó al total de la caja"
        assert caja_status_2["status"]["total_movimientos"] == initial_movimientos - 4500.0, "El movimiento no se aplicó al total"
        print("Deltas de caja verificados correctamente.")

        # --- PRUEBA 8: GET /api/reportes (Admin) ---
        print("\nPrueba 8: Consultando reportes con PIN...")
        report_data = get_req(f"/api/reportes?fecha_inicio={today_date}&fecha_fin={today_date}&pin=7802")
        print("Reporte Admin cargado exitosamente. Ventas encontradas hoy:", len(report_data["ventas"]))
        test_sale_reported = next((s for s in report_data["ventas"] if s["id_venta"] == id_venta), None)
        assert test_sale_reported is not None, "La venta de prueba no figura en el reporte administrativo"
        print("Venta de prueba encontrada en reporte admin:", test_sale_reported)
        
        # --- PRUEBA 9: POST /api/ventas/anular (Anular Venta) ---
        print("\nPrueba 9: Anulando venta de prueba...")
        res_void = post_req("/api/ventas/anular", {
            "id_venta": id_venta,
            "pin": "7802"
        })
        print("Respuesta anulación:", res_void)
        
        # Verificar restauración de stock
        prod_data_3 = get_req("/api/productos")
        aceitera_3 = next((p for p in prod_data_3["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        restored_stock = aceitera_3["stock"]["local.txt"]
        print(f"Stock restaurado de Aceitera El-093: {restored_stock}")
        assert restored_stock == original_stock_local, "El stock no se restauró correctamente tras anulación"

        # --- PRUEBA 10: Eliminar movimiento de prueba ---
        print("\nPrueba 10: Eliminando movimiento de caja de prueba...")
        res_del_mov = post_req("/api/caja/movimiento/eliminar", {
            "timestamp": mov_timestamp
        })
        print("Respuesta eliminar movimiento:", res_del_mov)

        # Consultar estado de caja final
        caja_status_3 = get_req(f"/api/caja/status?fecha={today_date}")
        print("Estado caja tras deshacer operaciones de prueba:", caja_status_3["status"])
        assert caja_status_3["status"]["total_ventas"] == initial_ventas
        assert caja_status_3["status"]["total_movimientos"] == initial_movimientos

        # --- PRUEBA 11: POST /api/inventario/ajustar (Ajustes de stock) ---
        print("\nPrueba 11: Validando endpoint de ajuste de stock...")
        
        # 11.1 Ajustar sin PIN (Debe fallar 401)
        err_no_pin = post_req_err("/api/inventario/ajustar", {
            "producto": "Aceitera El-093",
            "archivo": "local.txt",
            "cambio": 5
        }, expected_code=401)
        print("Ajuste sin PIN bloqueado como se esperaba:", err_no_pin)

        # 11.2 Ajustar con PIN incorrecto (Debe fallar 401)
        err_bad_pin = post_req_err("/api/inventario/ajustar", {
            "producto": "Aceitera El-093",
            "archivo": "local.txt",
            "cambio": 5,
            "pin": "9999"
        }, expected_code=401)
        print("Ajuste con PIN incorrecto bloqueado como se esperaba:", err_bad_pin)

        # 11.3 Ajustar con PIN correcto (+5 unidades)
        res_ajuste = post_req("/api/inventario/ajustar", {
            "producto": "Aceitera El-093",
            "archivo": "local.txt",
            "cambio": 5
        }, pin="7802")
        print("Respuesta ajuste (+5):", res_ajuste)
        
        # Verificar cambio de stock
        prod_data_4 = get_req("/api/productos")
        aceitera_4 = next((p for p in prod_data_4["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        adjusted_stock = aceitera_4["stock"]["local.txt"]
        print(f"Stock de Aceitera El-093 tras ajuste (+5): {adjusted_stock}")
        assert adjusted_stock == original_stock_local + 5, "El stock no aumentó a la cantidad esperada"

        # 11.4 Ajuste que resulta en stock negativo (Debe fallar 400)
        err_neg_stock = post_req_err("/api/inventario/ajustar", {
            "producto": "Aceitera El-093",
            "archivo": "local.txt",
            "cambio": -(adjusted_stock + 1)
        }, expected_code=400, pin="7802")
        print("Ajuste a negativo bloqueado como se esperaba:", err_neg_stock)

        # 11.5 Restaurar el stock original (-5 unidades)
        res_ajuste_rest = post_req("/api/inventario/ajustar", {
            "producto": "Aceitera El-093",
            "archivo": "local.txt",
            "cambio": -5
        }, pin="7802")
        print("Respuesta restauración ajuste (-5):", res_ajuste_rest)
        
        # Verificar restauración
        prod_data_5 = get_req("/api/productos")
        aceitera_5 = next((p for p in prod_data_5["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        assert aceitera_5["stock"]["local.txt"] == original_stock_local, "El stock de local.txt no volvió a su valor original"
        print("Ajustes de stock verificados exitosamente.")

        # --- PRUEBA 12: POST /api/inventario/trasladar (Traslado de mercancía) ---
        print("\nPrueba 12: Validando endpoint de traslado de stock...")
        
        # Asegurémonos de tener suficiente stock en local.txt
        # Si el stock original es menor a 2, agregamos temporalmente para realizar el test
        temp_added = 0
        if original_stock_local < 2:
            temp_added = 2 - original_stock_local
            post_req("/api/inventario/ajustar", {
                "producto": "Aceitera El-093",
                "archivo": "local.txt",
                "cambio": temp_added
            }, pin="7802")
            print(f"Stock de origen bajo ({original_stock_local}). Añadido temporalmente: +{temp_added}")

        # 12.1 Trasladar sin PIN (Debe fallar 401)
        err_traslado_no_pin = post_req_err("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local.txt",
            "destino": "local_2.txt",
            "cantidad": 2
        }, expected_code=401)
        print("Traslado sin PIN bloqueado como se esperaba:", err_traslado_no_pin)

        # 12.2 Trasladar con PIN incorrecto (Debe fallar 401)
        err_traslado_bad_pin = post_req_err("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local.txt",
            "destino": "local_2.txt",
            "cantidad": 2,
            "pin": "0000"
        }, expected_code=401)
        print("Traslado con PIN incorrecto bloqueado como se esperaba:", err_traslado_bad_pin)

        # 12.3 Trasladar con misma ubicación de origen y destino (Debe fallar 400)
        err_same_loc = post_req_err("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local.txt",
            "destino": "local.txt",
            "cantidad": 1
        }, expected_code=400, pin="7802")
        print("Traslado a la misma ubicación bloqueado como se esperaba:", err_same_loc)

        # 12.4 Trasladar cantidad insuficiente (Debe fallar 400)
        # Obtenemos stock actual de origen para estar seguros
        prod_data_temp = get_req("/api/productos")
        aceitera_temp = next((p for p in prod_data_temp["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        curr_stock_orig = aceitera_temp["stock"]["local.txt"]
        
        err_insufficient = post_req_err("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local.txt",
            "destino": "local_2.txt",
            "cantidad": curr_stock_orig + 1000
        }, expected_code=400, pin="7802")
        print("Traslado con stock insuficiente bloqueado como se esperaba:", err_insufficient)

        # 12.5 Traslado exitoso (2 unidades de local.txt a local_2.txt)
        res_traslado = post_req("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local.txt",
            "destino": "local_2.txt",
            "cantidad": 2
        }, pin="7802")
        print("Respuesta traslado exitoso (2 unidades):", res_traslado)

        # Verificar existencias actualizadas en ambas locaciones
        prod_data_after_t = get_req("/api/productos")
        aceitera_after_t = next((p for p in prod_data_after_t["productos"] if p["descripcion"] == "Aceitera El-093"), None)
        
        print(f"Stock de Aceitera El-093 después del traslado:")
        print(f" - En local.txt: {aceitera_after_t['stock']['local.txt']} (antes: {curr_stock_orig})")
        print(f" - En local_2.txt: {aceitera_after_t['stock']['local_2.txt']} (antes: {original_stock_local2})")
        
        assert aceitera_after_t["stock"]["local.txt"] == curr_stock_orig - 2, "El origen no descontó las unidades"
        assert aceitera_after_t["stock"]["local_2.txt"] == original_stock_local2 + 2, "El destino no sumó las unidades"

        # 12.6 Revertir el traslado (2 unidades de local_2.txt a local.txt)
        res_revert_t = post_req("/api/inventario/trasladar", {
            "producto": "Aceitera El-093",
            "origen": "local_2.txt",
            "destino": "local.txt",
            "cantidad": 2
        }, pin="7802")
        print("Respuesta revertir traslado (2 unidades de regreso):", res_revert_t)

        # Limpiar stock temporal adicional si se agregó en el paso 12
        if temp_added > 0:
            post_req("/api/inventario/ajustar", {
                "producto": "Aceitera El-093",
                "archivo": "local.txt",
                "cambio": -temp_added
            }, pin="7802")
            print(f"Stock temporal removido: -{temp_added}")

        # Comprobación final de restauración absoluta de stock
        prod_data_final = get_req("/api/productos")
        # --- PRUEBA 13: POST /api/ventas con Pago Dividido (Split payment) ---
        print("\nPrueba 13: Registrando venta de prueba con Pago Dividido...")
        
        # Guardar estado actual de caja
        caja_pre_split = get_req(f"/api/caja/status?fecha={today_date}")
        pre_split_ventas = caja_pre_split["status"]["total_ventas"]
        pre_split_electronicos = caja_pre_split["status"]["pagos_electronicos"]
        pre_split_efectivo = caja_pre_split["status"]["efectivo_esperado"]

        sale_payload_split = {
            "cliente": client_name,
            "medio_pago": "Efectivo: $8000.00, Nequi: $10000.00",
            "archivo_origen": "local.txt",
            "items": [
                {
                    "descripcion": "Aceitera El-093",
                    "cantidad": 1,
                    "precio": 18000,
                    "costo": original_cost
                }
            ]
        }
        res_sale_split = post_req("/api/ventas", sale_payload_split)
        print("Respuesta registro venta dividida:", res_sale_split)
        id_venta_split = res_sale_split["id_venta"]

        # Consultar estado de caja actualizado
        caja_post_split = get_req(f"/api/caja/status?fecha={today_date}")
        print("Estado caja tras venta dividida:", caja_post_split["status"])

        # Verificar caja:
        # total_ventas aumenta en 18000
        # pagos_electronicos aumenta en 10000 (monto de Nequi)
        # efectivo_esperado aumenta en 8000 (monto de Efectivo)
        assert caja_post_split["status"]["total_ventas"] == pre_split_ventas + 18000.0, "Las ventas de la venta dividida no se sumaron correctamente"
        assert caja_post_split["status"]["pagos_electronicos"] == pre_split_electronicos + 10000.0, "Los pagos electrónicos de la venta dividida no se sumaron correctamente"
        assert caja_post_split["status"]["efectivo_esperado"] == pre_split_efectivo + 8000.0, "El efectivo esperado de la venta dividida no se calculó correctamente"
        print("Métricas de caja para pago dividido verificadas correctamente.")

        # Anular la venta dividida
        print("Anulando venta dividida de prueba...")
        res_void_split = post_req("/api/ventas/anular", {
            "id_venta": id_venta_split,
            "pin": "7802"
        })
        print("Respuesta anulación venta dividida:", res_void_split)

        # Verificar restauración final
        caja_final_split = get_req(f"/api/caja/status?fecha={today_date}")
        assert caja_final_split["status"]["total_ventas"] == pre_split_ventas, "El total de ventas no se restauró"
        assert caja_final_split["status"]["pagos_electronicos"] == pre_split_electronicos, "El total de pagos electrónicos no se restauró"
        assert caja_final_split["status"]["efectivo_esperado"] == pre_split_efectivo, "El efectivo esperado no se restauró"
        print("Caja restaurada a su estado pre-dividido con éxito.")

        # --- PRUEBA 14: POST /api/admin/request_pin ---
        print("\nPrueba 14: Solicitando PIN dinámico...")
        res_req_pin = post_req("/api/admin/request_pin", {})
        print("Respuesta solicitud PIN dinámico:", res_req_pin)
        assert res_req_pin["status"] == "ok", "No se pudo solicitar el PIN dinámico"
        print("Prueba de solicitud de PIN dinámico completada.")

        print("\n=== TODAS LAS PRUEBAS DE API DE ESTILO DELTA PASARON EXITOSAMENTE (FASES 1, 2 Y 3) ===")
        
    finally:
        # Detener el servidor
        print("\nDeteniendo servidor temporal...")
        server_process.terminate()
        server_process.wait()
        
        # Eliminar archivo de test
        if os.path.exists("servidor_test.py"):
            os.remove("servidor_test.py")
            
        # Limpieza de base de datos de test
        print("Limpiando registros de prueba de los archivos CSV...")
        
        # 1. Quitar test client de clientes.csv
        if os.path.exists("clientes.csv"):
            with open("clientes.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                rows = [r for r in reader if r and r[0] != client_name]
            with open("clientes.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(rows)
                
        # 2. Si nosotros iniciamos la caja hoy, la quitamos para dejarlo limpio
        if initiated_by_test and os.path.exists("caja_registros.csv"):
            print(f"Removiendo inicio de caja temporal de hoy ({today_date}) de caja_registros.csv...")
            with open("caja_registros.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                rows = [r for r in reader if r and r[0] != today_date]
            with open("caja_registros.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(rows)
                
        # 3. Quitar cualquier movimiento de prueba de movimientos_caja.csv por si quedó
        if os.path.exists("movimientos_caja.csv"):
            with open("movimientos_caja.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                rows = [r for r in reader if r and not r[0].startswith(today_date + " ") and r[2] != "Café de prueba"]
            with open("movimientos_caja.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(rows)
                
        print("Limpieza completa. Base de datos restaurada.")

if __name__ == "__main__":
    run_test()
