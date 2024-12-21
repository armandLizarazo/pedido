import sqlite3
from datetime import datetime
import os

class SistemaVentas:
    def __init__(self, db_name='ventas.db'):
        self.conn = sqlite3.connect(db_name)
        self.crear_tablas()
    
    def crear_tablas(self):
        cursor = self.conn.cursor()
        
        # Tabla de Clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                direccion TEXT
            )
        ''')
        
        # Tabla de Productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')
        
        # Tabla de Ventas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                fecha_venta TEXT NOT NULL,
                total REAL NOT NULL,
                saldo_pendiente REAL NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        # Tabla de Detalles de Venta
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER,
                producto_id INTEGER,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        # Tabla de Abonos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abonos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER,
                fecha_abono TEXT NOT NULL,
                monto REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id)
            )
        ''')
        
        self.conn.commit()

    def fecha_actual(self):
        """Retorna la fecha actual en formato YYYY-MM-DD"""
        return datetime.now().strftime('%Y-%m-%d')

    def registrar_cliente(self, nombre, telefono, direccion):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO clientes (nombre, telefono, direccion)
            VALUES (?, ?, ?)
        ''', (nombre, telefono, direccion))
        self.conn.commit()
        return cursor.lastrowid

    def registrar_producto(self, nombre, precio, stock):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO productos (nombre, precio, stock)
            VALUES (?, ?, ?)
        ''', (nombre, precio, stock))
        self.conn.commit()
        return cursor.lastrowid

    def listar_productos(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, nombre, precio, stock
            FROM productos
            ORDER BY nombre
        ''')
        return cursor.fetchall()

    def buscar_cliente(self, termino_busqueda):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, nombre, telefono, direccion
            FROM clientes
            WHERE nombre LIKE ? OR telefono LIKE ?
        ''', (f'%{termino_busqueda}%', f'%{termino_busqueda}%'))
        return cursor.fetchall()

    def realizar_venta(self, cliente_id, productos_cantidades):
        cursor = self.conn.cursor()
        fecha_venta = self.fecha_actual()
        total = 0
        
        # Calcular total y verificar stock
        for producto_id, cantidad in productos_cantidades:
            cursor.execute('SELECT precio, stock FROM productos WHERE id = ?', (producto_id,))
            precio, stock = cursor.fetchone()
            if stock < cantidad:
                raise ValueError(f"Stock insuficiente para el producto {producto_id}")
            total += precio * cantidad
        
        # Registrar venta
        cursor.execute('''
            INSERT INTO ventas (cliente_id, fecha_venta, total, saldo_pendiente)
            VALUES (?, ?, ?, ?)
        ''', (cliente_id, fecha_venta, total, total))
        venta_id = cursor.lastrowid
        
        # Registrar detalles y actualizar stock
        for producto_id, cantidad in productos_cantidades:
            cursor.execute('SELECT precio FROM productos WHERE id = ?', (producto_id,))
            precio = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO detalles_venta (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            ''', (venta_id, producto_id, cantidad, precio))
            
            cursor.execute('''
                UPDATE productos
                SET stock = stock - ?
                WHERE id = ?
            ''', (cantidad, producto_id))
        
        self.conn.commit()
        return venta_id

    def registrar_abono(self, venta_id, monto):
        cursor = self.conn.cursor()
        fecha_abono = self.fecha_actual()
        
        # Verificar que el monto no exceda el saldo pendiente
        cursor.execute('SELECT saldo_pendiente FROM ventas WHERE id = ?', (venta_id,))
        saldo_pendiente = cursor.fetchone()[0]
        
        if monto > saldo_pendiente:
            raise ValueError("El monto del abono excede el saldo pendiente")
        
        # Registrar abono
        cursor.execute('''
            INSERT INTO abonos (venta_id, fecha_abono, monto)
            VALUES (?, ?, ?)
        ''', (venta_id, fecha_abono, monto))
        
        # Actualizar saldo pendiente
        cursor.execute('''
            UPDATE ventas
            SET saldo_pendiente = saldo_pendiente - ?
            WHERE id = ?
        ''', (monto, venta_id))
        
        self.conn.commit()

    def consultar_estado_cuenta(self, venta_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT v.id, v.fecha_venta, v.total, v.saldo_pendiente,
                   c.nombre as cliente
            FROM ventas v
            JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        ''', (venta_id,))
        venta = cursor.fetchone()
        
        if not venta:
            return None
        
        cursor.execute('''
            SELECT fecha_abono, monto
            FROM abonos
            WHERE venta_id = ?
            ORDER BY fecha_abono
        ''', (venta_id,))
        abonos = cursor.fetchall()
        
        return {
            'venta_id': venta[0],
            'fecha_venta': venta[1],
            'cliente': venta[4],
            'total': venta[2],
            'saldo_pendiente': venta[3],
            'abonos': abonos
        }

    def clientes_con_deuda(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.id, c.nombre, c.telefono,
                   SUM(v.saldo_pendiente) as deuda_total
            FROM clientes c
            JOIN ventas v ON c.id = v.cliente_id
            WHERE v.saldo_pendiente > 0
            GROUP BY c.id
            ORDER BY deuda_total DESC
        ''')
        return cursor.fetchall()

    def clientes_al_dia(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT c.id, c.nombre, c.telefono
            FROM clientes c
            WHERE NOT EXISTS (
                SELECT 1 FROM ventas v
                WHERE v.cliente_id = c.id
                AND v.saldo_pendiente > 0
            )
        ''')
        return cursor.fetchall()

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_menu_principal():
    limpiar_pantalla()
    print("\n=== SISTEMA DE VENTAS A CRÉDITO ===")
    print("1. Gestión de Clientes")
    print("2. Gestión de Productos")
    print("3. Realizar Venta")
    print("4. Registrar Abono")
    print("5. Consultas")
    print("0. Salir")
    return input("\nSeleccione una opción: ")

def menu_clientes(sistema):
    while True:
        limpiar_pantalla()
        print("\n=== GESTIÓN DE CLIENTES ===")
        print("1. Registrar nuevo cliente")
        print("2. Buscar cliente")
        print("3. Ver clientes con deuda")
        print("4. Ver clientes al día")
        print("0. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            nombre = input("Nombre del cliente: ")
            telefono = input("Teléfono: ")
            direccion = input("Dirección: ")
            cliente_id = sistema.registrar_cliente(nombre, telefono, direccion)
            print(f"\nCliente registrado con ID: {cliente_id}")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "2":
            termino = input("Ingrese nombre o teléfono a buscar: ")
            clientes = sistema.buscar_cliente(termino)
            if clientes:
                print("\nClientes encontrados:")
                for c in clientes:
                    print(f"ID: {c[0]}, Nombre: {c[1]}, Teléfono: {c[2]}, Dirección: {c[3]}")
            else:
                print("\nNo se encontraron clientes")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "3":
            deudores = sistema.clientes_con_deuda()
            if deudores:
                print("\nClientes con deuda:")
                for d in deudores:
                    print(f"ID: {d[0]}, Nombre: {d[1]}, Teléfono: {d[2]}, Deuda total: ${d[3]:.2f}")
            else:
                print("\nNo hay clientes con deuda")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "4":
            al_dia = sistema.clientes_al_dia()
            if al_dia:
                print("\nClientes al día:")
                for c in al_dia:
                    print(f"ID: {c[0]}, Nombre: {c[1]}, Teléfono: {c[2]}")
            else:
                print("\nNo hay clientes al día")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "0":
            break

def menu_productos(sistema):
    while True:
        limpiar_pantalla()
        print("\n=== GESTIÓN DE PRODUCTOS ===")
        print("1. Registrar nuevo producto")
        print("2. Ver lista de productos")
        print("0. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            nombre = input("Nombre del producto: ")
            while True:
                try:
                    precio = float(input("Precio: $"))
                    stock = int(input("Stock inicial: "))
                    break
                except ValueError:
                    print("Por favor, ingrese valores numéricos válidos")
            
            producto_id = sistema.registrar_producto(nombre, precio, stock)
            print(f"\nProducto registrado con ID: {producto_id}")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "2":
            productos = sistema.listar_productos()
            if productos:
                print("\nLista de productos:")
                for p in productos:
                    print(f"ID: {p[0]}, Nombre: {p[1]}, Precio: ${p[2]:.2f}, Stock: {p[3]}")
            else:
                print("\nNo hay productos registrados")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "0":
            break

def realizar_venta(sistema):
    limpiar_pantalla()
    print("\n=== REALIZAR VENTA ===")
    
    # Buscar cliente
    cliente_id = input("ID del cliente: ")
    if not cliente_id.isdigit():
        print("ID de cliente inválido")
        input("\nPresione Enter para continuar...")
        return
    
    productos_cantidades = []
    while True:
        print("\nProductos actuales en la venta:", productos_cantidades)
        print("\n1. Agregar producto")
        print("2. Finalizar venta")
        print("0. Cancelar venta")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            producto_id = input("ID del producto: ")
            if not producto_id.isdigit():
                print("ID de producto inválido")
                continue
            
            try:
                cantidad = int(input("Cantidad: "))
                productos_cantidades.append((int(producto_id), cantidad))
            except ValueError:
                print("Cantidad inválida")
                continue
        
        elif opcion == "2":
            if not productos_cantidades:
                print("Debe agregar al menos un producto")
                continue
            
            try:
                venta_id = sistema.realizar_venta(int(cliente_id), productos_cantidades)
                print(f"\nVenta registrada con ID: {venta_id}")
                estado = sistema.consultar_estado_cuenta(venta_id)
                print(f"Total de la venta: ${estado['total']:.2f}")
                input("\nPresione Enter para continuar...")
                break
            except ValueError as e:
                print(f"\nError al realizar la venta: {e}")
                input("\nPresione Enter para continuar...")
                break
        
        elif opcion == "0":
            break

def registrar_abono(sistema):
    limpiar_pantalla()
    print("\n=== REGISTRAR ABONO ===")
    
    venta_id = input("ID de la venta: ")
    if not venta_id.isdigit():
        print("ID de venta inválido")
        input("\nPresione Enter para continuar...")
        return
    
    estado = sistema.consultar_estado_cuenta(int(venta_id))
    if not estado:
        print("Venta no encontrada")
        input("\nPresione Enter para continuar...")
        return
    
    print(f"\nCliente: {estado['cliente']}")
    print(f"Total de la venta: ${estado['total']:.2f}")
    print(f"Saldo pendiente: ${estado['saldo_pendiente']:.2f}")
    
    try:
        monto = float(input("\nMonto del abono: $"))
        sistema.registrar_abono(int(venta_id), monto)
        print("\nAbono registrado exitosamente")
    except ValueError as e:
        print(f"\nError al registrar el abono: {e}")
    
    input("\nPresione Enter para continuar...")

def menu_consultas(sistema):
    while True:
        limpiar_pantalla()
        print("\n=== CONSULTAS ===")
        print("1. Consultar estado de cuenta")
        print("2. Ver clientes con deuda")
        print("3. Ver clientes al día")
        print("0. Volver al menú principal")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            venta_id = input("ID de la venta: ")
            if not venta_id.isdigit():
                print("ID de venta inválido")
                input("\nPresione Enter para continuar...")
                continue
            
            estado = sistema.consultar_estado_cuenta(int(venta_id))
            if estado:
                print(f"\nCliente: {estado['cliente']}")
                print(f"Fecha de venta: {estado['fecha_venta']}")
                print(f"Total: ${estado['total']:.2f}")
                print(f"Saldo pendiente: ${estado['saldo_pendiente']:.2f}")
                print("\nHistorial de abonos:")
                for fecha, monto in estado['abonos']:
                    print(f"Fecha: {fecha}, Monto: ${monto:.2f}")
            else:
                print("\nVenta no encontrada")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "2":
            deudores = sistema.clientes_con_deuda()
            if deudores:
                print("\nClientes con deuda:")
                for d in deudores:
                    print(f"ID: {d[0]}, Nombre: {d[1]}, Teléfono: {d[2]}, Deuda total: ${d[3]:.2f}")
            else:
                print("\nNo hay clientes con deuda")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "3":
            al_dia = sistema.clientes_al_dia()
            if al_dia:
                print("\nClientes al día:")
                for c in al_dia:
                    print(f"ID: {c[0]}, Nombre: {c[1]}, Teléfono: {c[2]}")
            else:
                print("\nNo hay clientes al día")
            input("\nPresione Enter para continuar...")
        
        elif opcion == "0":
            break

def main():
    sistema = SistemaVentas()
    
    while True:
        opcion = mostrar_menu_principal()
        
        if opcion == "1":
            menu_clientes(sistema)
        elif opcion == "2":
            menu_productos(sistema)
        elif opcion == "3":
            realizar_venta(sistema)
        elif opcion == "4":
            registrar_abono(sistema)
        elif opcion == "5":
            menu_consultas(sistema)
        elif opcion == "0":
            print("\n¡Gracias por usar el sistema!")
            break
        else:
            print("\nOpción inválida")
            input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()