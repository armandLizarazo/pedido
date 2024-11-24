def eliminar_lineas_ok(nombre_archivo):
    """
    Elimina las líneas que:
    1. Comienzan con 4 espacios
    2. Terminan con ' ok'
    Y genera un informe de los elementos eliminados
    """
    try:
        # Leer el archivo
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()
        
        # Inicializar listas para el resultado y elementos eliminados
        resultado = []
        eliminados = []
        contador_eliminados = 0
        
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
            
        # Generar y mostrar el informe
        print("\n=== INFORME DE ELEMENTOS ELIMINADOS ===")
        print(f"Total de elementos eliminados: {contador_eliminados}")
        if eliminados:
            print("\nDetalle de elementos eliminados:")
            print("Línea  | Contenido")
            print("-" * 50)
            for num_linea, contenido in eliminados:
                print(f"{num_linea:5d} | {contenido}")
        
        print("\n=== CONTENIDO FINAL DEL ARCHIVO ===")
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            contenido_final = archivo.read()
            print(contenido_final)
            
        # Guardar el informe en un archivo separado
        nombre_informe = "informe_eliminados.txt"
        with open(nombre_informe, 'w', encoding='utf-8') as archivo_informe:
            archivo_informe.write("=== INFORME DE ELEMENTOS ELIMINADOS ===\n")
            archivo_informe.write(f"Fecha de proceso: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            archivo_informe.write(f"Archivo procesado: {nombre_archivo}\n")
            archivo_informe.write(f"Total de elementos eliminados: {contador_eliminados}\n\n")
            if eliminados:
                archivo_informe.write("Detalle de elementos eliminados:\n")
                archivo_informe.write("Línea  | Contenido\n")
                archivo_informe.write("-" * 50 + "\n")
                for num_linea, contenido in eliminados:
                    archivo_informe.write(f"{num_linea:5d} | {contenido}\n")
        
        print(f"\nSe ha guardado el informe detallado en: {nombre_informe}")
            
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

# Uso del script
if __name__ == "__main__":
    from datetime import datetime
    eliminar_lineas_ok("pedido.txt")