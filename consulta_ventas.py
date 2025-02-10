import pandas as pd
from tabulate import tabulate

# Cargar los datos desde el archivo txt
def cargar_datos():
    try:
        # Leer el archivo con el separador '|' y sin nombres de columnas
        datos = pd.read_csv('registro_ventas.txt', sep='|', header=None, names=['Fecha', 'Nombre', 'Cantidad', 'Valor'], skipinitialspace=True)
        
        # Eliminar espacios en blanco adicionales en la columna 'Fecha'
        datos['Fecha'] = datos['Fecha'].str.strip()
        
        # Convertir las columnas a los tipos correctos
        datos['Fecha'] = pd.to_datetime(datos['Fecha'], format='%Y-%m-%d %H:%M:%S', errors='coerce')  # Usar 'coerce' para manejar errores
        datos['Cantidad'] = pd.to_numeric(datos['Cantidad'], errors='coerce')  # Convertir a número
        datos['Valor'] = pd.to_numeric(datos['Valor'], errors='coerce')  # Convertir a número
        
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
def realizar_consulta(datos, fecha=0, nombre=0, cantidad=0, valor=0):
    try:
        if fecha != 0:
            fecha = pd.to_datetime(fecha, format='%Y-%m-%d', errors='coerce')  # Convertir entrada a datetime
            if pd.isna(fecha):  # Si la conversión falla, no aplicar filtro
                print("Formato de fecha incorrecto. No se aplicará el filtro de fecha.")
            else:
                datos = datos[datos['Fecha'].dt.date == fecha.date()]  # Comparar solo la fecha (sin hora)
        if nombre != 0 and nombre.lower() != "all":  # Ignorar filtro si nombre es "all"
            palabras_clave = nombre.lower().split()  # Dividir la entrada en palabras clave
            datos = datos[datos['Nombre'].apply(lambda x: any(palabra in x.lower() for palabra in palabras_clave))]
        if cantidad != 0:
            datos = datos[datos['Cantidad'] == cantidad]
        if valor != 0:
            datos = datos[datos['Valor'] == valor]
        return datos
    except Exception as e:
        print(f"Error al realizar la consulta: {e}")
        return pd.DataFrame()  # Retornar un DataFrame vacío en caso de error

# Función para mostrar los resultados en formato de tabla
def mostrar_resultados(datos):
    if datos.empty:
        print("No se encontraron resultados.")
    else:
        # Crear una copia del DataFrame para no modificar el original
        datos_tabla = datos.copy()
        
        # Calcular subtotales
        subtotal_cantidad = datos_tabla['Cantidad'].sum()
        subtotal_valor = datos_tabla['Valor'].sum()
        
        # Agregar una fila de subtotales al DataFrame
        subtotales = pd.DataFrame({
            'Fecha': [''],
            'Nombre': ['Subtotal'],
            'Cantidad': [subtotal_cantidad],
            'Valor': [subtotal_valor]
        })
        
        # Concatenar los datos con la fila de subtotales
        datos_tabla = pd.concat([datos_tabla, subtotales], ignore_index=True)
        
        # Convertir el DataFrame a una lista de listas para usar con tabulate
        tabla = datos_tabla.values.tolist()
        
        # Agregar una línea horizontal antes de la fila de subtotales
        tabla.insert(-1, ['─' * 20, '─' * 30, '─' * 8, '─' * 10])  # Línea horizontal
        
        # Mostrar la tabla con bordes y ajuste automático de columnas
        print(tabulate(tabla, headers=datos_tabla.columns, tablefmt='fancy_grid', showindex=False, stralign='left', numalign='right'))

# Función para guardar la consulta en un archivo txt
def guardar_consulta(datos, nombre_archivo):
    if not datos.empty:
        datos.to_csv(nombre_archivo, sep='|', index=False)
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
    nombre = input("Nombre (0 para omitir, 'all' para todos, o varias palabras clave): ")
    cantidad = input("Cantidad (0 para omitir): ")
    valor = input("Valor (0 para omitir): ")
    
    # Convertir entradas a tipos adecuados
    cantidad = int(cantidad) if cantidad != '0' else 0
    valor = float(valor) if valor != '0' else 0
    
    # Realizar la consulta
    resultados = realizar_consulta(datos, fecha, nombre, cantidad, valor)
    
    # Mostrar resultados
    mostrar_resultados(resultados)
    
    # Opción de guardar o eliminar la consulta
    opcion = input("\n¿Desea guardar la consulta? (s/n): ").lower()
    if opcion == 's':
        nombre_archivo = input("Ingrese el nombre del archivo para guardar (ej: consulta.txt): ")
        guardar_consulta(resultados, nombre_archivo)
    else:
        print("Consulta no guardada.")

if __name__ == "__main__":
    main()