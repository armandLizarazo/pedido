import chardet

def detectar_codificacion(nombre_archivo):
    """
    Detecta la codificación de un archivo.

    Args:
        nombre_archivo (str): El nombre del archivo a analizar.

    Returns:
        str: La codificación detectada, o 'utf-8' si no se puede detectar.
    """
    try:
        with open(nombre_archivo, 'rb') as archivo:
            raw_data = archivo.read()
        resultado = chardet.detect(raw_data)
        return resultado['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'

def eliminar_lineas_repetidas(nombre_archivo, codificacion):
    """
    Elimina las líneas repetidas de un archivo, conservando la de mayor valor numérico.
    Maneja correctamente la codificación de caracteres.

    Args:
        nombre_archivo (str): El nombre del archivo a procesar.
        codificacion (str): La codificación del archivo.
    """
    try:
        with open(nombre_archivo, 'r', encoding=codificacion) as archivo:
            lineas = archivo.readlines()
        
        lineas_unicas = {}
        lineas_repetidas = []

        for linea in lineas:
            partes = linea.strip().split()
            if not partes:
                continue
            
            clave = ' '.join(partes[:-1])
            valor = int(partes[-1]) if partes[-1].isdigit() else 0
            
            if clave in lineas_unicas:
                if valor > lineas_unicas[clave][1]:
                    lineas_repetidas.append(lineas_unicas[clave][0])
                    lineas_unicas[clave] = (linea, valor)
                else:
                    lineas_repetidas.append(linea)
            else:
                lineas_unicas[clave] = (linea, valor)
            
            
        if lineas_repetidas:
            print(f"\nSe encontraron {len(lineas_repetidas)} líneas repetidas en el archivo '{nombre_archivo}':")
            for repetida in lineas_repetidas:
                print(repetida.strip())
            
            respuesta = input("\n¿Deseas eliminar las líneas repetidas? (s/n): ").strip().lower()
            if respuesta == 's':
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
    """
    Ordena las líneas de un archivo que comienzan con 4 espacios, aplicando formato y eliminando repetidas.
    Maneja la codificación de caracteres detectada.

    Args:
        nombre_archivo (str): El nombre del archivo a procesar.
    """
    try:
        codificacion = detectar_codificacion(nombre_archivo)
        print(f"\nProcesando archivo: {nombre_archivo}")
        print(f"Detectada codificación: {codificacion}")
        
        with open(nombre_archivo, 'r', encoding=codificacion) as archivo:
            lineas = archivo.readlines()
        
        lineas_4_espacios = [linea for linea in lineas if linea.startswith('    ')]
        lineas_no_4_espacios = [linea for linea in lineas if not linea.startswith('    ')]
        
        lineas_4_espacios = ['    ' + linea.lstrip().title() for linea in lineas_4_espacios]
        
        lineas_4_espacios.sort()
        
        lineas_ordenadas = lineas_no_4_espacios + lineas_4_espacios
        
        with open(nombre_archivo, 'w', encoding=codificacion) as archivo:
            archivo.writelines(lineas_ordenadas)
        
        print(f"Las líneas que inician con 4 espacios en el archivo '{nombre_archivo}' han sido ordenadas y formateadas correctamente.")
        
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
