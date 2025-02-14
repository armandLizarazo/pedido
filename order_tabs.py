import chardet

def detectar_codificacion(nombre_archivo):
    with open(nombre_archivo, 'rb') as archivo:
        raw_data = archivo.read()
    resultado = chardet.detect(raw_data)
    return resultado['encoding']

def eliminar_lineas_repetidas(nombre_archivo, codificacion):
    try:
        with open(nombre_archivo, 'r', encoding=codificacion) as archivo:
            lineas = archivo.readlines()
        
        # Diccionario para almacenar la línea con el mayor valor para cada clave
        lineas_unicas = {}
        lineas_repetidas = []

        for linea in lineas:
            # Ignorar el número final de la línea (si existe)
            partes = linea.strip().split()
            if not partes:
                continue  # Ignorar líneas vacías
            
            clave = ' '.join(partes[:-1])  # Todo excepto el último elemento
            valor = int(partes[-1]) if partes[-1].isdigit() else 0  # Convertir el último elemento a entero
            
            # Verificar si la clave ya existe en el diccionario
            if clave in lineas_unicas:
                # Comparar el valor actual con el valor almacenado
                if valor > lineas_unicas[clave][1]:
                    lineas_repetidas.append(lineas_unicas[clave][0])  # Agregar la línea anterior a repetidas
                    lineas_unicas[clave] = (linea, valor)  # Actualizar con la nueva línea y valor
                else:
                    lineas_repetidas.append(linea)  # Agregar la línea actual a repetidas
            else:
                lineas_unicas[clave] = (linea, valor)  # Almacenar la línea y su valor
        
        # Si hay líneas repetidas, preguntar al usuario si desea eliminarlas
        if lineas_repetidas:
            print(f"\nSe encontraron {len(lineas_repetidas)} líneas repetidas en el archivo '{nombre_archivo}':")
            for repetida in lineas_repetidas:
                print(repetida.strip())
            
            respuesta = input("\n¿Deseas eliminar las líneas repetidas? (s/n): ").strip().lower()
            if respuesta == 's':
                # Escribir solo las líneas únicas en el archivo (conservando las de mayor valor)
                with open(nombre_archivo, 'w', encoding=codificacion) as archivo:
                    archivo.writelines([linea[0] for linea in lineas_unicas.values()])
                print(f"Se han eliminado las líneas repetidas del archivo '{nombre_archivo}'.")
            else:
                print("No se han eliminado las líneas repetidas.")
        else:
            print(f"No se encontraron líneas repetidas en el archivo '{nombre_archivo}'.")
    
    except Exception as e:
        print(f"Ocurrió un error al verificar líneas repetidas: {e}")

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
        
        # Verificar y eliminar líneas repetidas
        eliminar_lineas_repetidas(nombre_archivo, codificacion)
    
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