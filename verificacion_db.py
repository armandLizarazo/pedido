def leer_archivo(nombre_archivo):
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()
    # Ignorar el último número de cada línea
    elementos = [linea.rsplit(' ', 1)[0] for linea in lineas]
    return elementos

def comparar_archivos(archivos):
    # Leer los elementos de todos los archivos
    elementos_archivos = {archivo: set(leer_archivo(archivo)) for archivo in archivos}
    
    # Encontrar todos los elementos únicos en todos los archivos
    todos_los_elementos = set()
    for elementos in elementos_archivos.values():
        todos_los_elementos.update(elementos)
    
    # Identificar los elementos faltantes en cada archivo
    faltantes = {}
    for archivo, elementos in elementos_archivos.items():
        faltantes[archivo] = todos_los_elementos - elementos
    
    return faltantes

def generar_reporte(faltantes):
    reporte = "Reporte de líneas faltantes:\n"
    for archivo, elementos in faltantes.items():
        if elementos:
            reporte += f"Faltan en {archivo}:\n"
            for elemento in elementos:
                reporte += f"{elemento}\n"
    return reporte

def agregar_elementos(nombre_archivo, elementos):
    with open(nombre_archivo, 'a') as archivo:
        for elemento in elementos:
            # Solicitar al usuario que ingrese el número final
            numero_final = input(f"Ingrese el número final para '{elemento}' en '{nombre_archivo}': ")
            archivo.write(f"{elemento} {numero_final}\n")  # Agregar el elemento con el número final
    print(f"Elementos agregados a {nombre_archivo}.")

def main():
    # Solicitar la cantidad de archivos
    cantidad_archivos = int(input("Ingrese la cantidad de archivos a verificar: "))
    archivos = []
    for i in range(cantidad_archivos):
        nombre_archivo = input(f"Ingrese el nombre del archivo {i + 1}: ")
        archivos.append(nombre_archivo)

    # Comparar los archivos
    faltantes = comparar_archivos(archivos)

    # Generar el reporte
    reporte = generar_reporte(faltantes)
    print(reporte)

    # Permitir al usuario agregar elementos faltantes
    for archivo, elementos in faltantes.items():
        if elementos:
            respuesta = input(f"¿Desea agregar los elementos faltantes a {archivo}? (s/n): ")
            if respuesta.lower() == 's':
                agregar_elementos(archivo, elementos)

if __name__ == "__main__":
    main()