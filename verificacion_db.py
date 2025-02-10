def leer_archivo(nombre_archivo):
    with open(nombre_archivo, 'r') as archivo:
        lineas = archivo.readlines()
    # Ignorar el último número de cada línea
    elementos = [linea.rsplit(' ', 1)[0] for linea in lineas]
    return elementos

def comparar_archivos(archivo1, archivo2):
    elementos1 = set(leer_archivo(archivo1))
    elementos2 = set(leer_archivo(archivo2))

    faltantes_en_archivo1 = elementos2 - elementos1
    faltantes_en_archivo2 = elementos1 - elementos2

    return faltantes_en_archivo1, faltantes_en_archivo2

def generar_reporte(faltantes_en_archivo1, faltantes_en_archivo2, archivo1, archivo2):
    reporte = "Reporte de líneas faltantes:\n"
    if faltantes_en_archivo1:
        reporte += f"Faltan en {archivo1}:\n"
        for elemento in faltantes_en_archivo1:
            reporte += f"{elemento}\n"
    if faltantes_en_archivo2:
        reporte += f"Faltan en {archivo2}:\n"
        for elemento in faltantes_en_archivo2:
            reporte += f"{elemento}\n"
    return reporte

def agregar_elementos(nombre_archivo, elementos):
    with open(nombre_archivo, 'a') as archivo:
        for elemento in elementos:
            # Solicitar al usuario que ingrese el número final
            numero_final = input(f"Ingrese el número final para '{elemento}': ")
            archivo.write(f"{elemento} {numero_final}\n")  # Agregar el elemento con el número final
    print(f"Elementos agregados a {nombre_archivo}.")

def main():
    archivo1 = input("Ingrese el nombre del primer archivo: ")
    archivo2 = input("Ingrese el nombre del segundo archivo: ")

    faltantes_en_archivo1, faltantes_en_archivo2 = comparar_archivos(archivo1, archivo2)

    reporte = generar_reporte(faltantes_en_archivo1, faltantes_en_archivo2, archivo1, archivo2)
    print(reporte)

    if faltantes_en_archivo1:
        respuesta = input(f"¿Desea agregar los elementos faltantes a {archivo1}? (s/n): ")
        if respuesta.lower() == 's':
            agregar_elementos(archivo1, faltantes_en_archivo1)

    if faltantes_en_archivo2:
        respuesta = input(f"¿Desea agregar los elementos faltantes a {archivo2}? (s/n): ")
        if respuesta.lower() == 's':
            agregar_elementos(archivo2, faltantes_en_archivo2)

if __name__ == "__main__":
    main()