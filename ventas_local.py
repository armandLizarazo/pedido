def ver_contenido(archivo):
    try:
        with open(archivo, "r") as f:
            lineas = f.readlines()
            if not lineas:
                print(f"El archivo '{archivo}' está vacío.")
            else:
                print(f"Contenido actual de '{archivo}':")
                for i, linea in enumerate(lineas, 1):
                    print(f"{i}. {linea.strip()}")
    except FileNotFoundError:
        print(f"El archivo '{archivo}' no existe.")

def realizar_venta():
    try:
        with open("local.txt", "r") as archivo:
            lineas = archivo.readlines()
        
        if not lineas:
            print("El archivo está vacío. No hay items para vender.")
            return
        
        palabras_clave = input("Ingrese palabras clave para buscar el item: ").strip().lower()
        resultados = []
        
        for i, linea in enumerate(lineas):
            if palabras_clave in linea.lower():
                resultados.append((i, linea.strip()))
        
        if not resultados:
            print("No se encontraron items con esas palabras clave.")
            return
        
        print("Resultados de la búsqueda:")
        for idx, (i, linea) in enumerate(resultados, 1):
            print(f"{idx}. {linea}")
        
        try:
            seleccion = int(input("Seleccione el número del item que desea vender: ")) - 1
            if seleccion < 0 or seleccion >= len(resultados):
                print("Selección inválida.")
                return
            
            idx_original, linea = resultados[seleccion]
            partes = linea.split()
            cantidad = int(partes[-1])
            
            if cantidad <= 0:
                print("No hay unidades disponibles para este item.")
                verificar_existencias_bodega(partes)
                return
            
            cantidad -= 1
            nueva_linea = "    " + " ".join(partes[:-1]) + f" {cantidad}\n"
            lineas[idx_original] = nueva_linea
            
            with open("local.txt", "w") as archivo:
                archivo.writelines(lineas)
            
            print("Venta realizada con éxito.")
            verificar_stock_cero()
        
        except ValueError:
            print("Entrada inválida. Debe ingresar un número.")
    
    except FileNotFoundError:
        print("El archivo 'local.txt' no existe.")

def verificar_existencias_bodega(partes_item):
    try:
        with open("bodegac.txt", "r") as archivo:
            lineas = archivo.readlines()
        
        # Extraer el nombre del item sin la cantidad y convertirlo a minúsculas
        item_buscar = " ".join(partes_item[:-1]).strip().lower()
        
        for i, linea in enumerate(lineas):
            # Extraer el nombre del item en bodega sin la cantidad y convertirlo a minúsculas
            partes_bodega = linea.split()
            item_bodega = " ".join(partes_bodega[:-1]).strip().lower()
            
            if item_buscar == item_bodega:
                cantidad_bodega = int(partes_bodega[-1])
                if cantidad_bodega > 0:
                    print(f"Hay {cantidad_bodega} unidades de '{item_buscar}' en bodega.")
                    respuesta = input("¿Desea trasladar unidades a local? (s/n): ").strip().lower()
                    if respuesta == "s":
                        trasladar_unidades(item_buscar, cantidad_bodega)
                    return
                else:
                    print(f"No hay unidades de '{item_buscar}' en bodega.")
                    return
        
        print(f"El item '{item_buscar}' no se encuentra en bodega.")
        respuesta = input("¿Desea solicitar compra al proveedor? (s/n): ").strip().lower()
        if respuesta == "s":
            print("Solicitud de compra al proveedor enviada.")
        else:
            print("No se realizará ninguna acción.")
    
    except FileNotFoundError:
        print("El archivo 'bodegac.txt' no existe.")

def trasladar_unidades(item_buscar, cantidad_bodega):
    try:
        # Leer bodegac.txt
        with open("bodegac.txt", "r") as archivo:
            lineas_bodega = archivo.readlines()
        
        # Buscar el item en bodegac.txt
        for i, linea in enumerate(lineas_bodega):
            partes_bodega = linea.split()
            item_bodega = " ".join(partes_bodega[:-1]).strip().lower()
            
            if item_buscar == item_bodega:
                cantidad_bodega = int(partes_bodega[-1])
                if cantidad_bodega > 0:
                    # Restar una unidad en bodega
                    nueva_cantidad_bodega = cantidad_bodega - 1
                    nueva_linea_bodega = "    " + " ".join(partes_bodega[:-1]) + f" {nueva_cantidad_bodega}\n"
                    lineas_bodega[i] = nueva_linea_bodega
                    
                    # Escribir bodegac.txt actualizado
                    with open("bodegac.txt", "w") as archivo:
                        archivo.writelines(lineas_bodega)
                    
                    # Añadir una unidad en local.txt
                    with open("local.txt", "r") as archivo:
                        lineas_local = archivo.readlines()
                    
                    item_encontrado = False
                    for j, linea_local in enumerate(lineas_local):
                        partes_local = linea_local.split()
                        item_local = " ".join(partes_local[:-1]).strip().lower()
                        
                        if item_buscar == item_local:
                            cantidad_local = int(partes_local[-1])
                            nueva_cantidad_local = cantidad_local + 1
                            nueva_linea_local = "    " + " ".join(partes_local[:-1]) + f" {nueva_cantidad_local}\n"
                            lineas_local[j] = nueva_linea_local
                            item_encontrado = True
                            break
                    
                    # Si el item no existe en local.txt, se añade
                    if not item_encontrado:
                        nueva_linea_local = "    " + item_buscar.title() + " 1\n"  # Usamos title() para formato correcto
                        lineas_local.append(nueva_linea_local)
                    
                    # Escribir local.txt actualizado
                    with open("local.txt", "w") as archivo:
                        archivo.writelines(lineas_local)
                    
                    print("Unidad trasladada de bodega a local con éxito.")
                    return
                else:
                    print("No hay suficientes unidades en bodega para trasladar.")
                    return
        
        print(f"El item '{item_buscar}' no se encontró en bodega.")
    
    except FileNotFoundError:
        print("Error: Uno de los archivos no existe.")

def verificar_stock_cero():
    try:
        with open("local.txt", "r") as archivo:
            lineas = archivo.readlines()
        
        for i, linea in enumerate(lineas):
            partes = linea.split()
            cantidad = int(partes[-1])
            if cantidad == 0:
                item_buscar = " ".join(partes[:-1]).strip().lower()
                print(f"El item '{item_buscar}' está agotado en local.")
                verificar_existencias_bodega(partes)
    
    except FileNotFoundError:
        print("El archivo 'local.txt' no existe.")

def main():
    while True:
        print("\n--- Menú ---")
        print("1. Ver contenido actual de local.txt")
        print("2. Realizar venta")
        print("3. Ver contenido actual de bodegac.txt")
        print("4. Salir")
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_contenido("local.txt")
        elif opcion == "2":
            realizar_venta()
        elif opcion == "3":
            ver_contenido("bodegac.txt")
        elif opcion == "4":
            print("Saliendo del programa...")
            break
        else:
            print("Opción inválida. Intente nuevamente.")

if __name__ == "__main__":
    main()