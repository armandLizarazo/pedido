import chardet

def detectar_codificacion(nombre_archivo):
    with open(nombre_archivo, 'rb') as archivo:
        raw_data = archivo.read()
    resultado = chardet.detect(raw_data)
    return resultado['encoding']

def ordenar_lineas_tabuladas(nombre_archivo):
    try:
        # Detectar la codificación del archivo
        codificacion = detectar_codificacion(nombre_archivo)
        print(f"\nProcesando archivo: {nombre_archivo}")
        print(f"Detectada codificación: {codificacion}")
        
        # Abrir el archivo con la codificación detectada
        with open(nombre_archivo, 'r', encoding=codificacion) as archivo:
            lineas = archivo.readlines()
        
        # Filtrar solo las líneas que inician con 4 espacios
        lineas_4_espacios = [linea for linea in lineas if linea.startswith('    ')]
        lineas_no_4_espacios = [linea for linea in lineas if not linea.startswith('    ')]
        
        # Aplicar formato "title" a las líneas que inician con 4 espacios
        lineas_4_espacios = ['    ' + linea.lstrip().title() for linea in lineas_4_espacios]
        
        # Ordenar las líneas que inician con 4 espacios alfabéticamente
        lineas_4_espacios.sort()
        
        # Combinar las líneas no tabuladas con las tabuladas ordenadas
        lineas_ordenadas = lineas_no_4_espacios + lineas_4_espacios
        
        # Escribir las líneas ordenadas de vuelta al archivo con la misma codificación
        with open(nombre_archivo, 'w', encoding=codificacion) as archivo:
            archivo.writelines(lineas_ordenadas)
        
        print(f"Las líneas que inician con 4 espacios en el archivo '{nombre_archivo}' han sido ordenadas y formateadas correctamente.")
    
    except FileNotFoundError:
        print(f"El archivo '{nombre_archivo}' no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

# Solicitar al usuario los nombres de los archivos
nombres_archivos = input("Por favor, ingresa los nombres de los archivos que deseas ordenar (separados por comas): ")

# Separar los nombres de los archivos
lista_archivos = [nombre.strip() for nombre in nombres_archivos.split(',')]

# Procesar cada archivo
for archivo in lista_archivos:
    ordenar_lineas_tabuladas(archivo)