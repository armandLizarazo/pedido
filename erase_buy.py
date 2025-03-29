from datetime import datetime

def eliminar_lineas_ok(nombre_archivo):
    """
    Elimina las líneas que:
    1. Comienzan con 4 espacios
    2. Terminan con ' ok'
    Y genera un informe con historial de los elementos eliminados
    """
    try:
        # Leer el archivo
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()
        
        # Inicializar listas para el resultado y elementos eliminados
        resultado = []
        eliminados = []
        contador_eliminados = 0
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Procesar cada línea
        for numero_linea, linea in enumerate(lineas, 1):
            if linea.startswith('    ') and linea.rstrip().endswith(' ok'):
                # Guardar la línea eliminada y su número
                eliminados.append((numero_linea, linea.strip()))
                contador_eliminados += 1
            else:
                resultado.append(linea)
        
        # Escribir el resultado en el archivo
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
            archivo.writelines(resultado)
            
        # Generar y mostrar el informe actual
        print("\n=== INFORME DE ELEMENTOS ELIMINADOS ===")
        print(f"Fecha: {fecha_actual}")
        print(f"Total de elementos eliminados: {contador_eliminados}")
        if eliminados:
            print("\nDetalle de elementos eliminados:")
            print("Línea  | Contenido")
            print("-" * 50)
            for num_linea, contenido in eliminados:
                print(f"{num_linea:5d} | {contenido}")
        
        # Guardar en el historial
        nombre_historial = "historial_eliminados.txt"
        try:
            with open(nombre_historial, 'a', encoding='utf-8') as archivo_historial:
                archivo_historial.write(f"\n{'='*50}\n")
                archivo_historial.write(f"Fecha de proceso: {fecha_actual}\n")
                archivo_historial.write(f"Archivo procesado: {nombre_archivo}\n")
                archivo_historial.write(f"Total de elementos eliminados: {contador_eliminados}\n\n")
                if eliminados:
                    archivo_historial.write("Elementos eliminados:\n")
                    archivo_historial.write("Línea  | Contenido\n")
                    archivo_historial.write("-" * 50 + "\n")
                    for num_linea, contenido in eliminados:
                        archivo_historial.write(f"{num_linea:5d} | {contenido}\n")
        except FileNotFoundError:
            # Si el archivo no existe, lo creamos con un encabezado
            with open(nombre_historial, 'w', encoding='utf-8') as archivo_historial:
                archivo_historial.write("HISTORIAL DE ELEMENTOS ELIMINADOS\n")
                archivo_historial.write("="*50 + "\n")
                archivo_historial.write(f"Fecha de proceso: {fecha_actual}\n")
                archivo_historial.write(f"Archivo procesado: {nombre_archivo}\n")
                archivo_historial.write(f"Total de elementos eliminados: {contador_eliminados}\n\n")
                if eliminados:
                    archivo_historial.write("Elementos eliminados:\n")
                    archivo_historial.write("Línea  | Contenido\n")
                    archivo_historial.write("-" * 50 + "\n")
                    for num_linea, contenido in eliminados:
                        archivo_historial.write(f"{num_linea:5d} | {contenido}\n")
        
        print(f"\nHistorial actualizado en: {nombre_historial}")
        
        # Mostrar el contenido actual del archivo
        print("\n=== CONTENIDO FINAL DEL ARCHIVO ===")
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            print(archivo.read())
            
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

# Uso del script
if __name__ == "__main__":
    eliminar_lineas_ok("pdcentro.txt")
    eliminar_lineas_ok("pdpr.txt")
    eliminar_lineas_ok("pdst.txt")