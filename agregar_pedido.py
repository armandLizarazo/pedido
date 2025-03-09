import os
import re

def leer_archivo(nombre_archivo):
    """Lee un archivo y devuelve una lista de líneas."""
    with open(nombre_archivo, 'r') as archivo:
        return archivo.readlines()

def escribir_archivo(nombre_archivo, lineas):
    """Escribe una lista de líneas en un archivo."""
    with open(nombre_archivo, 'w') as archivo:
        archivo.writelines(lineas)

def procesar_item_bodega(linea):
    """
    Procesa un item del archivo bodegac.txt.
    Devuelve el nombre y la cantidad.
    """
    # Buscar el último número en la línea (precedido por espacios)
    match = re.search(r'(\s+\d+)$', linea)  # Busca espacios seguidos de un número al final
    if not match:
        return None, None  # No se encontró un número al final

    cantidad = int(match.group(1).strip())  # Extraer el número como entero
    nombre = linea[:match.start()].strip()  # Extraer el nombre (todo antes del número)
    return nombre, cantidad

def procesar_item_archivo(item, linea_numero=None, archivo_nombre=None):
    """
    Procesa un item de los archivos analizados.
    Devuelve el nombre y la cantidad.
    """
    partes = item.strip().rsplit(maxsplit=2)  # Dividir desde la derecha en máximo 2 partes
    if len(partes) < 2:
        print(f"Error: Formato inválido en la línea {linea_numero} del archivo {archivo_nombre}: {item.strip()}")
        return None, None  # Devolver valores nulos para indicar un error

    nombre = partes[0].strip()  # Nombre del item (sin espacios adicionales)
    try:
        cantidad = int(partes[1])  # Intentar convertir la cantidad a entero
    except ValueError:
        print(f"Error: La cantidad no es un número válido en la línea {linea_numero} del archivo {archivo_nombre}: {item.strip()}")
        return None, None  # Devolver valores nulos para indicar un error

    return nombre, cantidad

def buscar_item_en_bodega(nombre, bodega):
    """Busca un item en la bodega y devuelve su índice y cantidad."""
    for i, linea in enumerate(bodega):
        nombre_bodega, cantidad_bodega = procesar_item_bodega(linea)
        if nombre_bodega and nombre_bodega.strip() == nombre.strip():
            return i, cantidad_bodega
    return None, 0

def actualizar_bodega(bodega, nombre, cantidad):
    """Actualiza la bodega con el nuevo item o cantidad."""
    if nombre is None or cantidad is None:
        return  # Ignorar items con errores

    indice, cantidad_existente = buscar_item_en_bodega(nombre, bodega)
    if indice is not None:
        # Si el item existe, actualiza la cantidad
        nueva_cantidad = cantidad_existente + cantidad
        bodega[indice] = f"    {nombre.strip()} {nueva_cantidad}\n"
        print(f"Actualizado: {nombre.strip()} ({cantidad_existente} + {cantidad} = {nueva_cantidad})")  # Depuración
    else:
        # Si el item no existe, lo agrega con 4 espacios al inicio
        bodega.append(f"    {nombre.strip()} {cantidad}\n")
        print(f"Agregado: {nombre.strip()} {cantidad}")  # Depuración

def eliminar_duplicados_bodega(bodega):
    """
    Elimina items duplicados en la bodega, sumando sus cantidades.
    Devuelve una nueva lista sin duplicados.
    """
    items_unicos = {}
    for linea in bodega:
        nombre, cantidad = procesar_item_bodega(linea)
        if nombre is None or cantidad is None:
            continue  # Ignorar líneas inválidas
        if nombre in items_unicos:
            items_unicos[nombre] += cantidad  # Sumar cantidades si el item ya existe
        else:
            items_unicos[nombre] = cantidad  # Agregar el item si no existe

    # Convertir el diccionario de items únicos a una lista de líneas
    bodega_sin_duplicados = [f"    {nombre} {cantidad}\n" for nombre, cantidad in items_unicos.items()]
    return bodega_sin_duplicados

def main():
    archivos_a_analizar = input("Ingrese los nombres de los archivos a analizar, separados por comas: ").split(',')
    archivos_a_analizar = [archivo.strip() for archivo in archivos_a_analizar]

    # Leer el archivo bodegac.txt
    bodega = leer_archivo('bodegac.txt')

    for archivo in archivos_a_analizar:
        if not os.path.exists(archivo):
            print(f"El archivo {archivo} no existe.")
            continue

        lineas = leer_archivo(archivo)
        for linea_numero, linea in enumerate(lineas, start=1):  # Empezar a contar desde 1
            if linea.strip().endswith('ok'):  # Solo procesar líneas que terminan con 'ok'
                nombre, cantidad = procesar_item_archivo(linea.strip(), linea_numero, archivo)
                if nombre is None or cantidad is None:
                    continue  # Ignorar líneas con errores
                actualizar_bodega(bodega, nombre, cantidad)

    # Eliminar duplicados en la bodega
    bodega = eliminar_duplicados_bodega(bodega)

    # Escribir los cambios en bodegac.txt
    escribir_archivo('bodegac.txt', bodega)
    print("Bodega actualizada correctamente.")

if __name__ == "__main__":
    main()