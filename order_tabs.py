def ordenar_lineas_tabuladas(nombre_archivo):
    """
    Lee un archivo y ordena alfabéticamente las líneas que comienzan con 4 espacios.
    Mantiene las líneas no indentadas en su posición original.
    """
    try:
        # Leer el archivo
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            lineas = archivo.readlines()
        
        # Inicializar variables
        resultado = []
        lineas_indentadas = []
        
        # Procesar cada línea
        for linea in lineas:
            # Si la línea comienza con exactamente 4 espacios
            if linea.startswith('    '):
                lineas_indentadas.append(linea)
            else:
                # Si tenemos líneas indentadas acumuladas, las ordenamos e insertamos
                if lineas_indentadas:
                    lineas_indentadas.sort()
                    resultado.extend(lineas_indentadas)
                    lineas_indentadas = []
                resultado.append(linea)
        
        # Si quedan líneas indentadas al final, ordenarlas y agregarlas
        if lineas_indentadas:
            lineas_indentadas.sort()
            resultado.extend(lineas_indentadas)
        
        # Escribir el resultado en el archivo
        with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
            archivo.writelines(resultado)
            
        print("Archivo ordenado exitosamente.")
        
        # Para debug: mostrar cómo quedó el archivo
        print("\nContenido del archivo ordenado:")
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            print(archivo.read())
            
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

# Uso del script
if __name__ == "__main__":
    ordenar_lineas_tabuladas("pedido.txt")
    ordenar_lineas_tabuladas("bodegac.txt")