import os
import datetime

CLIENTES_FILE = "clientes_cr.txt"
VENTAS_FILE = "ventas_cr.txt"
ABONOS_FILE = "registro_abcr.txt"
PRODUCTOS_FILE = "local.txt"

def buscar_clientes(nombre):
    """Busca clientes por nombre parcial."""
    coincidencias = []
    if not os.path.exists(CLIENTES_FILE):
        return coincidencias
    
    try:
        with open(CLIENTES_FILE, "r", encoding='utf-8') as file:
            for linea in file:
                if nombre.lower() in linea.lower():
                    coincidencias.append(linea.strip())
    except FileNotFoundError:
        print(f"Error: Archivo {CLIENTES_FILE} no encontrado.")
    except IOError as e:
        print(f"Error al leer el archivo: {e}")
    
    return coincidencias

def seleccionar_cliente():
    """Permite seleccionar un cliente existente o agregar uno nuevo."""
    while True:
        nombre = input("Ingrese parte del nombre del cliente: ").strip()
        
        if not nombre:
            print("El nombre no puede estar vacío.")
            continue
        
        coincidencias = buscar_clientes(nombre)
        
        if not coincidencias:
            opcion = input("No se encontraron coincidencias. ¿Desea agregarlo? (s/n): ")
            if opcion.lower() == "s":
                return agregar_cliente(nombre)
            elif opcion.lower() == "n":
                return None
        
        print("Clientes encontrados:")
        for i, cliente in enumerate(coincidencias, 1):
            print(f"{i}. {cliente}")
        
        seleccion = input("Seleccione un número o presione Enter para agregar nuevo: ")
        
        if not seleccion:
            return agregar_cliente(nombre)
        
        if seleccion.isdigit() and 1 <= int(seleccion) <= len(coincidencias):
            return coincidencias[int(seleccion) - 1]

def agregar_cliente(nombre):
    """Agrega un nuevo cliente al archivo."""
    try:
        with open(CLIENTES_FILE, "a", encoding='utf-8') as file:
            file.write(nombre + "\n")
        print(f"Cliente {nombre} agregado exitosamente.")
        return nombre
    except IOError as e:
        print(f"Error al agregar cliente: {e}")
        return None

def registrar_abono():
    """Registra un abono para un cliente."""
    cliente = seleccionar_cliente()
    if not cliente:
        return
    
    try:
        monto = float(input("Ingrese el monto del abono: "))
        fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        abono_id = int(datetime.datetime.now().timestamp())
        
        with open(ABONOS_FILE, "a", encoding='utf-8') as file:
            file.write(f"{abono_id}, {fecha}, {cliente}, {monto}\n")
        
        print("Abono registrado exitosamente.")
    except ValueError:
        print("Monto inválido. Por favor, ingrese un número.")
    except IOError as e:
        print(f"Error al registrar abono: {e}")

def buscar_productos(nombre):
    """Busca productos por nombre parcial."""
    coincidencias = []
    try:
        with open(PRODUCTOS_FILE, "r", encoding='utf-8') as file:
            for linea in file:
                partes = linea.rsplit(" ", 1)
                if nombre.lower() in partes[0].lower():
                    coincidencias.append((partes[0], int(partes[1])))  # Producto y stock
    except FileNotFoundError:
        print(f"Error: Archivo {PRODUCTOS_FILE} no encontrado.")
    except IOError as e:
        print(f"Error al leer el archivo: {e}")
    
    return coincidencias

def seleccionar_producto():
    """Permite seleccionar un producto existente o agregar uno nuevo."""
    while True:
        nombre = input("Ingrese parte del nombre del producto: ").strip()
        
        if not nombre:
            print("El nombre no puede estar vacío.")
            continue
        
        coincidencias = buscar_productos(nombre)
        
        if not coincidencias:
            opcion = input("No se encontraron coincidencias. ¿Desea agregarlo? (s/n): ")
            if opcion.lower() == "s":
                stock = int(input("Ingrese el stock inicial del producto: "))
                return agregar_producto(nombre, stock), stock
            elif opcion.lower() == "n":
                return None, 0
        
        print("Productos encontrados:")
        for i, (producto, stock) in enumerate(coincidencias, 1):
            print(f"{i}. {producto} (Stock: {stock})")
        
        seleccion = input("Seleccione un número o presione Enter para cancelar: ")
        
        if not seleccion:
            return None, 0
        
        if seleccion.isdigit() and 1 <= int(seleccion) <= len(coincidencias):
            return coincidencias[int(seleccion) - 1]

def agregar_producto(nombre, stock):
    """Agrega un nuevo producto al archivo."""
    try:
        with open(PRODUCTOS_FILE, "a", encoding='utf-8') as file:
            file.write(f"{nombre} {stock}\n")
        print(f"Producto {nombre} agregado exitosamente.")
        return nombre
    except IOError as e:
        print(f"Error al agregar producto: {e}")
        return None

def actualizar_stock(producto, cantidad):
    """Actualiza el stock de un producto después de una venta."""
    try:
        with open(PRODUCTOS_FILE, "r", encoding='utf-8') as file:
            lineas = file.readlines()
        
        with open(PRODUCTOS_FILE, "w", encoding='utf-8') as file:
            for linea in lineas:
                partes = linea.rsplit(" ", 1)
                if partes[0] == producto:
                    stock_actual = int(partes[1])
                    nuevo_stock = max(0, stock_actual - cantidad)
                    file.write(f"{producto} {nuevo_stock}\n")
                else:
                    file.write(linea)
    except IOError as e:
        print(f"Error al actualizar stock: {e}")

def registrar_venta():
    """Registra una nueva venta."""
    cliente = seleccionar_cliente()
    if not cliente:
        return
    
    producto, stock = seleccionar_producto()
    if not producto or stock == 0:
        print("No se puede realizar la venta, stock insuficiente.")
        return
    
    try:
        cantidad = int(input("Ingrese la cantidad: "))
        if cantidad > stock:
            print("No hay suficiente stock disponible.")
            return
        
        valor = float(input("Ingrese el valor de la venta: "))
        fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        venta_id = int(datetime.datetime.now().timestamp())
        
        with open(VENTAS_FILE, "a", encoding='utf-8') as file:
            file.write(f"{venta_id}, {fecha}, {cliente}, Credito, {producto}, {cantidad}, {valor}\n")
        
        actualizar_stock(producto, cantidad)
        print("Venta registrada exitosamente.")
    except ValueError:
        print("Cantidad o valor inválido. Por favor, ingrese un número.")

def consultar_ventas():
    """Muestra todas las ventas registradas."""
    try:
        with open(VENTAS_FILE, "r", encoding='utf-8') as file:
            ventas = file.readlines()
        
        if not ventas:
            print("No hay registros de ventas.")
            return
        
        print("\nHistorial de Ventas:")
        for venta in ventas:
            print(venta.strip())
    except FileNotFoundError:
        print("No se encontró el archivo de ventas.")
    except IOError as e:
        print(f"Error al leer ventas: {e}")

def consultar_abonos():
    """Muestra todos los abonos registrados."""
    try:
        with open(ABONOS_FILE, "r", encoding='utf-8') as file:
            abonos = file.readlines()
        
        if not abonos:
            print("No hay registros de abonos.")
            return
        
        print("\nHistorial de Abonos:")
        for abono in abonos:
            print(abono.strip())
    except FileNotFoundError:
        print("No se encontró el archivo de abonos.")
    except IOError as e:
        print(f"Error al leer abonos: {e}")

def consultar_estado_cuentas():
    """Muestra el estado de ventas y abonos."""
    consultar_ventas()
    consultar_abonos()

def menu():
    """Menú principal del sistema."""
    while True:
        print("\n--- SISTEMA DE GESTIÓN DE CRÉDITOS ---")
        print("0. Salir")
        print("1. Registrar Venta")
        print("2. Registrar Abono")
        print("3. Consultar Ventas")
        print("4. Consultar Abonos")
        print("5. Consultar Estado de Cuentas")
        
        opcion = input("Seleccione una opción: ")
        
        menu_opciones = {
            "0": exit,
            "1": registrar_venta,
            "2": registrar_abono,
            "3": consultar_ventas,
            "4": consultar_abonos,
            "5": consultar_estado_cuentas
        }
        
        accion = menu_opciones.get(opcion)
        if accion:
            accion()
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()