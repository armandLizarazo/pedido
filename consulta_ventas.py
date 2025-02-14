import pandas as pd
from tabulate import tabulate

# Cargar los datos desde el archivo txt
def cargar_datos():
    try:
        # Leer el archivo con el separador '|' y con nombres de columnas
        datos = pd.read_csv(
            'registro_ventas.txt',
            sep='|',
            header=0,  # La primera fila contiene los títulos
            skipinitialspace=True,
            encoding='latin-1'  # Especificar la codificación correcta
        )
        
        # Verificar que las columnas esperadas estén presentes
        columnas_esperadas = ['Fecha', 'Producto', 'Cantidad', 'Val Venta', 'Val Costo', 'Sub Venta', 'Sub Costo']
        if not all(col in datos.columns for col in columnas_esperadas):
            print("El archivo no tiene las columnas esperadas.")
            return None
        
        # Eliminar espacios en blanco adicionales en las columnas de texto
        datos['Fecha'] = datos['Fecha'].str.strip()
        datos['Producto'] = datos['Producto'].str.strip()
        
        # Convertir las columnas a los tipos correctos
        datos['Fecha'] = pd.to_datetime(datos['Fecha'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        datos['Cantidad'] = pd.to_numeric(datos['Cantidad'], errors='coerce')
        datos['Val Venta'] = pd.to_numeric(datos['Val Venta'], errors='coerce')
        datos['Val Costo'] = pd.to_numeric(datos['Val Costo'], errors='coerce')
        datos['Sub Venta'] = pd.to_numeric(datos['Sub Venta'], errors='coerce')
        datos['Sub Costo'] = pd.to_numeric(datos['Sub Costo'], errors='coerce')
        
        # Eliminar filas con valores nulos (si las conversiones fallaron)
        datos = datos.dropna()
        
        return datos
    except FileNotFoundError:
        print("El archivo 'registro_ventas.txt' no existe.")
        return None
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return None

# Función para realizar la consulta
def realizar_consulta(datos, fecha=0, producto=0, cantidad=0, val_venta=0, val_costo=0):
    try:
        if fecha != 0:
            fecha = pd.to_datetime(fecha, format='%Y-%m-%d', errors='coerce')
            if pd.isna(fecha):
                print("Formato de fecha incorrecto. No se aplicará el filtro de fecha.")
            else:
                datos = datos[datos['Fecha'].dt.date == fecha.date()]
        if producto != 0 and producto.lower() != "all":  # Ignorar filtro si producto es "all"
            palabras_clave = producto.lower().split()
            datos = datos[datos['Producto'].apply(lambda x: any(palabra in x.lower() for palabra in palabras_clave))]
        if cantidad != 0:
            datos = datos[datos['Cantidad'] == cantidad]
        if val_venta != 0:
            datos = datos[datos['Val Venta'] == val_venta]
        if val_costo != 0:
            datos = datos[datos['Val Costo'] == val_costo]
        return datos
    except Exception as e:
        print(f"Error al realizar la consulta: {e}")
        return pd.DataFrame()

# Función para mostrar los resultados en formato de tabla
def mostrar_resultados(datos):
    if datos.empty:
        print("No se encontraron resultados.")
    else:
        # Crear una copia del DataFrame para no modificar el original
        datos_tabla = datos.copy()
        
        # Calcular subtotales
        subtotal_cantidad = datos_tabla['Cantidad'].sum()
        subtotal_venta = datos_tabla['Sub Venta'].sum()
        subtotal_costo = datos_tabla['Sub Costo'].sum()
        utilidad_total = subtotal_venta - subtotal_costo
        
        # Agregar una fila de subtotales al DataFrame
        subtotales = pd.DataFrame({
            'Fecha': [''],
            'Producto': ['Subtotal'],
            'Cantidad': [subtotal_cantidad],
            'Val Venta': [''],
            'Val Costo': [''],
            'Sub Venta': [subtotal_venta],
            'Sub Costo': [subtotal_costo]
        })
        
        # Concatenar los datos con la fila de subtotales
        datos_tabla = pd.concat([datos_tabla, subtotales], ignore_index=True)
        
        # Convertir el DataFrame a una lista de listas para usar con tabulate
        tabla = datos_tabla.values.tolist()
        
        # Agregar una línea horizontal antes de la fila de subtotales
        tabla.insert(-1, ['─' * 20, '─' * 40, '─' * 8, '─' * 10, '─' * 10, '─' * 10, '─' * 10])
        
        # Mostrar la tabla con bordes y ajuste automático de columnas
        print(tabulate(tabla, headers=datos_tabla.columns, tablefmt='fancy_grid', showindex=False, stralign='left', numalign='right'))
        
        # Mostrar utilidad total
        print(f"\nUtilidad Total: {utilidad_total:.2f}")

# Función para generar resúmenes
def generar_resumenes(datos):
    if datos.empty:
        print("No hay datos para generar resúmenes.")
    else:
        # Utilidad por cada elemento
        datos = datos.copy()
        datos['Utilidad'] = datos['Sub Venta'] - datos['Sub Costo']
        
        # Utilidad total
        utilidad_total = datos['Utilidad'].sum()
        print(f"\nUtilidad Total: {utilidad_total:.2f}")
        
        # Cantidades totales
        cantidad_total = datos['Cantidad'].sum()
        print(f"Cantidad Total: {cantidad_total}")
        
        # Mayor y menor utilidad
        mayor_utilidad = datos.loc[datos['Utilidad'].idxmax()]
        menor_utilidad = datos.loc[datos['Utilidad'].idxmin()]
        print("\nProducto con Mayor Utilidad:")
        print(f"Producto: {mayor_utilidad['Producto']}, Utilidad: {mayor_utilidad['Utilidad']:.2f}")
        print("\nProducto con Menor Utilidad:")
        print(f"Producto: {menor_utilidad['Producto']}, Utilidad: {menor_utilidad['Utilidad']:.2f}")

# Función para guardar la consulta en un archivo txt
def guardar_consulta(datos, nombre_archivo):
    if not datos.empty:
        datos.to_csv(nombre_archivo, sep='|', index=False, encoding='latin-1')  # Guardar con la misma codificación
        print(f"Consulta guardada en {nombre_archivo}")
    else:
        print("No hay datos para guardar.")

# Función principal
def main():
    datos = cargar_datos()
    if datos is None:
        return
    
    print("Opciones de filtro:")
    fecha = input("Fecha (formato YYYY-MM-DD, 0 para omitir): ")
    producto = input("Producto (0 para omitir, 'all' para todos, o varias palabras clave): ")
    cantidad = input("Cantidad (0 para omitir): ")
    val_venta = input("Valor de venta (0 para omitir): ")
    val_costo = input("Valor de costo (0 para omitir): ")
    
    # Convertir entradas a tipos adecuados
    cantidad = int(cantidad) if cantidad != '0' else 0
    val_venta = float(val_venta) if val_venta != '0' else 0
    val_costo = float(val_costo) if val_costo != '0' else 0
    
    # Realizar la consulta
    resultados = realizar_consulta(datos, fecha, producto, cantidad, val_venta, val_costo)
    
    # Mostrar resultados
    mostrar_resultados(resultados)
    
    # Generar resúmenes
    generar_resumenes(resultados)
    
    # Opción de guardar o eliminar la consulta
    opcion = input("\n¿Desea guardar la consulta? (s/n): ").lower()
    if opcion == 's':
        nombre_archivo = input("Ingrese el nombre del archivo para guardar (ej: consulta.txt): ")
        guardar_consulta(resultados, nombre_archivo)
    else:
        print("Consulta no guardada.")

if __name__ == "__main__":
    main()