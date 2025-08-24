from datetime import datetime


def eliminar_lineas_ok(nombre_archivo):
    """
    Elimina las líneas que:
    1. Comienzan con 4 espacios Y terminan con ' ok'
    2. Comienzan con '#'
    3. Son líneas en blanco
    Y genera un informe con historial de los elementos eliminados
    """
    try:
        # Leer el archivo
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()

        # Inicializar listas para el resultado y elementos eliminados
        resultado = []
        eliminados = []
        contador_eliminados = 0
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Procesar cada línea
        for numero_linea, linea in enumerate(lineas, 1):
            # Condición actualizada: elimina líneas ' ok', las que empiezan con '#', o las que están en blanco
            if (
                (linea.startswith("    ") and linea.rstrip().endswith(" ok"))
                or linea.strip().startswith("#")
                or not linea.strip()
            ):
                # Guardar la línea eliminada y su número
                # Para líneas en blanco, mostramos un texto descriptivo
                contenido_eliminado = (
                    linea.strip() if linea.strip() else "[Línea en blanco]"
                )
                eliminados.append((numero_linea, contenido_eliminado))
                contador_eliminados += 1
            else:
                resultado.append(linea)

        # Escribir el resultado en el archivo
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.writelines(resultado)

        # Generar y mostrar el informe actual
        print(f"\n=== INFORME PARA: {nombre_archivo} ===")
        print(f"Fecha: {fecha_actual}")
        print(f"Total de elementos eliminados: {contador_eliminados}")
        if eliminados:
            print("\nDetalle de elementos eliminados:")
            print("Línea  | Contenido")
            print("-" * 50)
            for num_linea, contenido in eliminados:
                print(f"{num_linea:5d} | {contenido}")
        else:
            print("No se eliminaron líneas en esta ejecución.")

        # Guardar en el historial
        nombre_historial = "historial_eliminados.txt"
        try:
            with open(nombre_historial, "a", encoding="utf-8") as archivo_historial:
                archivo_historial.write(f"\n{'='*50}\n")
                archivo_historial.write(f"Fecha de proceso: {fecha_actual}\n")
                archivo_historial.write(f"Archivo procesado: {nombre_archivo}\n")
                archivo_historial.write(
                    f"Total de elementos eliminados: {contador_eliminados}\n\n"
                )
                if eliminados:
                    archivo_historial.write("Elementos eliminados:\n")
                    archivo_historial.write("Línea  | Contenido\n")
                    archivo_historial.write("-" * 50 + "\n")
                    for num_linea, contenido in eliminados:
                        archivo_historial.write(f"{num_linea:5d} | {contenido}\n")
        except FileNotFoundError:
            # Si el archivo no existe, lo creamos con un encabezado
            with open(nombre_historial, "w", encoding="utf-8") as archivo_historial:
                archivo_historial.write("HISTORIAL DE ELEMENTOS ELIMINADOS\n")
                archivo_historial.write("=" * 50 + "\n")
                # Escribir el registro actual
                archivo_historial.write(f"\n{'='*50}\n")
                archivo_historial.write(f"Fecha de proceso: {fecha_actual}\n")
                archivo_historial.write(f"Archivo procesado: {nombre_archivo}\n")
                archivo_historial.write(
                    f"Total de elementos eliminados: {contador_eliminados}\n\n"
                )
                if eliminados:
                    archivo_historial.write("Elementos eliminados:\n")
                    archivo_historial.write("Línea  | Contenido\n")
                    archivo_historial.write("-" * 50 + "\n")
                    for num_linea, contenido in eliminados:
                        archivo_historial.write(f"{num_linea:5d} | {contenido}\n")

        print(f"\nHistorial actualizado en: {nombre_historial}")

        # Mostrar el contenido actual del archivo
        print("\n=== CONTENIDO FINAL DEL ARCHIVO ===")
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            print(archivo.read())

    except FileNotFoundError:
        print(f"Error: El archivo '{nombre_archivo}' no fue encontrado.")
    except Exception as e:
        print(f"Error al procesar el archivo '{nombre_archivo}': {e}")


# Uso del script
if __name__ == "__main__":
    # Lista de archivos a procesar
    archivos_a_procesar = ["pdcentro.txt", "pdpr.txt", "pdst.txt", "np.txt"]

    # Crear archivos de prueba si no existen
    for nombre in archivos_a_procesar:
        try:
            with open(nombre, "x", encoding="utf-8") as f:
                f.write("# Esto es una línea de comentario.\n")
                f.write("\n")  # Línea en blanco para eliminar
                f.write("Esta línea se debe conservar.\n")
                f.write("    task one ok\n")
                f.write("\n")  # Otra línea en blanco
                f.write("    # Otro comentario con espacios.\n")
                f.write("    task two not ok\n")
            print(f"Archivo de prueba '{nombre}' creado.")
        except FileExistsError:
            pass  # El archivo ya existe, no hacer nada

    # Procesar cada archivo
    for nombre_archivo in archivos_a_procesar:
        eliminar_lineas_ok(nombre_archivo)
