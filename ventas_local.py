from datetime import datetime

def ver_contenido(archivo):
    try:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = f.readlines()
        except UnicodeDecodeError:
            with open(archivo, "r", encoding="latin-1") as f:
                lineas = f.readlines()
                print(f"Advertencia: El archivo '{archivo}' contenía caracteres no UTF-8. Se leyó usando la codificación latin-1.")
        
        if not lineas:
            print(f"El archivo '{archivo}' está vacío.")
            return
        
        if archivo == "registro_ventas.txt":
            # Mostrar el contenido sin procesar (formato especial)
            print(f"Contenido actual de '{archivo}':")
            for i, linea in enumerate(lineas, 1):
                print(f"{i}. {linea.strip()}")
            return
        
        print("\nOpciones de filtrado:")
        print("1. Mostrar todos los items")
        print("2. Mostrar items con cantidad igual a 0")
        print("3. Mostrar items con cantidad mayor a 0")
        print("4. Mostrar items con cantidad menor a un valor específico")
        print("5. Mostrar items con cantidad mayor a un valor específico")
        opcion_filtro = input("Seleccione una opción: ").strip()
        
        print(f"\nContenido actual de '{archivo}':")
        for i, linea in enumerate(lineas, 1):
            partes = linea.split()
            cantidad = int(partes[-1])
            
            if opcion_filtro == "1":  # Mostrar todos
                print(f"{i}. {linea.strip()}")
            elif opcion_filtro == "2" and cantidad == 0:  # Cantidad igual a 0
                print(f"{i}. {linea.strip()}")
            elif opcion_filtro == "3" and cantidad > 0:  # Cantidad mayor a 0
                print(f"{i}. {linea.strip()}")
            elif opcion_filtro == "4":  # Cantidad menor a un valor específico
                try:
                    valor = int(input("Ingrese el valor máximo de cantidad: ").strip())
                    if cantidad < valor:
                        print(f"{i}. {linea.strip()}")
                except ValueError:
                    print("Entrada inválida. Debe ingresar un número.")
            elif opcion_filtro == "5":  # Cantidad mayor a un valor específico
                try:
                    valor = int(input("Ingrese el valor mínimo de cantidad: ").strip())
                    if cantidad > valor:
                        print(f"{i}. {linea.strip()}")
                except ValueError:
                    print("Entrada inválida. Debe ingresar un número.")
            else:
                continue
    
    except FileNotFoundError:
        print(f"El archivo '{archivo}' no existe.")
    except Exception as e:
        print(f"Ocurrió un error inesperado al leer el archivo '{archivo}': {e}")

def obtener_valor_costo(item_buscar):
    try:
        with open("dbcst.txt", "r") as archivo:
            lineas = archivo.readlines()
        
        item_buscar = item_buscar.lower()
        for linea in lineas:
            partes = linea.split()
            item_db = " ".join(partes[:-1]).strip().lower()
            if item_buscar == item_db:
                return float(partes[-1])
        
        print(f"El item '{item_buscar}' no tiene un valor de costo definido en 'dbcst.txt'.")
        return None
    
    except FileNotFoundError:
        print("El archivo 'dbcst.txt' no existe.")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado al leer el archivo 'dbcst.txt': {e}")
        return None


def registrar_venta(item, cantidad, valor_venta, valor_costo):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subtotal_venta = cantidad * valor_venta
    subtotal_costo = cantidad * valor_costo
    
    try:
        with open("registro_ventas.txt", "a") as archivo:
            archivo.write(
                f"{fecha_actual} | {item} | {cantidad} | {valor_venta:.2f} | {valor_costo:.2f} | {subtotal_venta:.2f} | {subtotal_costo:.2f}\n"
            )
        print("Venta registrada con éxito.")
    except Exception as e:
        print(f"Ocurrió un error inesperado al escribir en 'registro_ventas.txt': {e}")

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
            cantidad_disponible = int(partes[-1])
            item_buscar = " ".join(partes[:-1]).strip()
            
            # Solicitar la cantidad a vender
            try:
                cantidad_vender = int(input(f"Ingrese la cantidad de '{item_buscar}' a vender (disponibles: {cantidad_disponible}): ").strip())
                if cantidad_vender <= 0:
                    print("La cantidad a vender debe ser mayor que 0.")
                    return
                if cantidad_vender > cantidad_disponible:
                    print("No hay suficientes unidades disponibles.")
                    return
            except ValueError:
                print("Entrada inválida. Debe ingresar un número.")
                return
            
            # Solicitar el valor de venta manualmente
            try:
                valor_venta = float(input(f"Ingrese el valor de venta para '{item_buscar}': ").strip())
                if valor_venta < 0:
                    print("El valor de venta no puede ser negativo.")
                    return
            except ValueError:
                print("Entrada inválida. Debe ingresar un número.")
                return
            
            # Obtener el valor de costo desde dbcst.txt
            valor_costo = obtener_valor_costo(item_buscar)
            if valor_costo is None:
                return
            
            # Realizar la venta
            cantidad_disponible -= cantidad_vender
            nueva_linea = "    " + " ".join(partes[:-1]) + f" {cantidad_disponible}\n"
            lineas[idx_original] = nueva_linea
            
            try:
                with open("local.txt", "w") as archivo:
                    archivo.writelines(lineas)
            except Exception as e:
                print(f"Ocurrió un error inesperado al escribir en 'local.txt': {e}")
                return
            
            print("Venta realizada con éxito.")
            registrar_venta(item_buscar, cantidad_vender, valor_venta, valor_costo)  # Registrar la venta
        
        except ValueError:
            print("Entrada inválida. Debe ingresar un número.")
    
    except FileNotFoundError:
        print("El archivo 'local.txt' no existe.")
    except Exception as e:
        print(f"Ocurrió un error inesperado al leer el archivo 'local.txt': {e}")

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
    except Exception as e:
        print(f"Ocurrió un error inesperado al leer el archivo 'bodegac.txt': {e}")

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
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")


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
    except Exception as e:
        print(f"Ocurrió un error inesperado al leer el archivo 'local.txt': {e}")


def main():
    while True:
        print("\n--- Menú ---")
        print("1. Ver contenido actual de local.txt")
        print("2. Realizar venta")
        print("3. Ver contenido actual de bodegac.txt")
        print("4. Ver registro de ventas")
        print("5. Salir")
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            ver_contenido("local.txt")
        elif opcion == "2":
            realizar_venta()
        elif opcion == "3":
            ver_contenido("bodegac.txt")
        elif opcion == "4":
            ver_contenido("registro_ventas.txt")
        elif opcion == "5":
            print("Saliendo del programa...")
            break
        else:
            print("Opción inválida. Intente nuevamente.")

if __name__ == "__main__":
    main()
