def cargar_archivo(nombre_archivo):
    try:
        with open(nombre_archivo, 'r') as archivo:
            lineas = archivo.readlines()
        return [linea.strip() for linea in lineas]
    except FileNotFoundError:
        print(f"El archivo '{nombre_archivo}' no fue encontrado.")
        return None

def guardar_archivo(nombre_archivo, elementos):
    # Guardar las líneas con 4 espacios al inicio
    with open(nombre_archivo, 'w') as archivo:
        for elemento in elementos:
            archivo.write(f"    {elemento}\n")

def ver_todos_los_elementos(elementos):
    for i, elemento in enumerate(elementos, 1):
        print(f"{i}. {elemento}")

def filtrar_por_palabra(elementos, palabra):
    resultados = []
    total = 0
    elementos_con_cero = []  # Lista para almacenar elementos con valor 0
    for elemento in elementos:
        if palabra.lower() in elemento.lower():
            partes = elemento.rsplit(' ', 1)
            if len(partes) == 2 and partes[1].isdigit():
                cantidad = int(partes[1])
                resultados.append(elemento)
                total += cantidad
                if cantidad == 0:  # Si el valor es 0, agregar a la lista
                    elementos_con_cero.append(elemento)
    return resultados, total, elementos_con_cero

def consultar_por_numero(elementos, numero):
    resultados = []
    for elemento in elementos:
        partes = elemento.rsplit(' ', 1)
        if len(partes) == 2 and partes[1].isdigit() and int(partes[1]) == numero:
            resultados.append(elemento)
    return resultados

def buscar_y_restar_unidades(nombre_archivo):
    # Recargar el archivo antes de realizar la operación
    elementos = cargar_archivo(nombre_archivo)
    if elementos is None:
        return
    
    palabra = input("Introduce el nombre del elemento a buscar: ").strip().lower()
    resultados = []
    
    # Buscar elementos que coincidan con la palabra (sin distinguir mayúsculas/minúsculas)
    for elemento in elementos:
        if palabra in elemento.lower():
            resultados.append(elemento)
    
    if not resultados:
        print(f"No se encontraron elementos que coincidan con '{palabra}'.")
        return
    
    print("\nElementos encontrados:")
    for i, resultado in enumerate(resultados, 1):
        print(f"{i}. {resultado}")
    
    try:
        indice = int(input("Selecciona el número del elemento a modificar: ")) - 1
        if indice < 0 or indice >= len(resultados):
            print("Selección no válida.")
            return
        
        elemento_seleccionado = resultados[indice]
        partes = elemento_seleccionado.rsplit(' ', 1)
        if len(partes) != 2 or not partes[1].isdigit():
            print("El elemento seleccionado no tiene un formato válido.")
            return
        
        nombre, cantidad_actual = partes[0], int(partes[1])
        unidades = int(input(f"Ingresa la cantidad de unidades a restar (máximo {cantidad_actual}): "))
        
        if unidades < 0:
            print("No se pueden restar unidades negativas.")
            return
        
        if unidades > cantidad_actual:
            print("No hay suficientes unidades para restar.")
            return
        
        # Restar las unidades
        nueva_cantidad = cantidad_actual - unidades
        nuevo_elemento = f"{nombre} {nueva_cantidad}"
        
        # Actualizar la lista de elementos
        indice_original = elementos.index(resultados[indice])
        elementos[indice_original] = nuevo_elemento
        
        # Guardar automáticamente los cambios en el archivo principal
        guardar_archivo(nombre_archivo, elementos)
        
        # Agregar la línea al archivo "local.txt" con 4 espacios al inicio
        agregar_a_local(nombre, unidades)
        
        print(f"\nSe restaron {unidades} unidades de '{nombre}'. Nueva cantidad: {nueva_cantidad}.")
        print(f"La línea se ha agregado al archivo 'local.txt'.")
    
    except ValueError:
        print("Entrada no válida. Introduce un número.")

def agregar_a_local(nombre, unidades):
    try:
        with open("local.txt", 'r') as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        lineas = []
    
    # Buscar si la línea ya existe en "local.txt" (ignorando el número final)
    encontrado = False
    for i, linea in enumerate(lineas):
        # Extraer el nombre de la línea (ignorando el número final)
        partes_linea = linea.strip().rsplit(' ', 1)
        nombre_linea = partes_linea[0].strip() if len(partes_linea) == 2 else linea.strip()
        
        if nombre.lower() == nombre_linea.lower():
            # Si existe, sumar las unidades
            if len(partes_linea) == 2 and partes_linea[1].isdigit():
                cantidad_actual = int(partes_linea[1])
                nueva_cantidad = cantidad_actual + unidades
                lineas[i] = f"    {nombre_linea} {nueva_cantidad}\n"  # 4 espacios al inicio
            else:
                lineas[i] = f"    {nombre_linea} {unidades}\n"  # 4 espacios al inicio
            encontrado = True
            break
    
    # Si no se encontró, agregar una nueva línea con 4 espacios al inicio
    if not encontrado:
        lineas.append(f"    {nombre} {unidades}\n")  # 4 espacios al inicio
    
    # Guardar los cambios en "local.txt"
    with open("local.txt", 'w') as archivo:
        archivo.writelines(lineas)

def main():
    nombre_archivo = input("Introduce el nombre del archivo: ")
    
    while True:
        # Recargar el archivo en cada iteración del menú
        elementos = cargar_archivo(nombre_archivo)
        if elementos is None:
            return
        
        print("\nOpciones:")
        print("1. Ver todos los elementos")
        print("2. Filtrar por palabra")
        print("3. Consultar elementos con un número indicado")
        print("4. Buscar y restar unidades de un elemento")
        print("0. Salir")
        opcion = input("Selecciona una opción: ")
        
        if opcion == '1':
            ver_todos_los_elementos(elementos)
        elif opcion == '2':
            palabra = input("Introduce la palabra para filtrar: ")
            resultados, total, elementos_con_cero = filtrar_por_palabra(elementos, palabra)
            print("\nResultados del filtro:")
            for i, resultado in enumerate(resultados, 1):
                print(f"{i}. {resultado}")
            print(f"\n(Total {total} Elementos)")
            if elementos_con_cero:  # Mostrar advertencia y elementos con valor 0
                print("\n¡Advertencia: Los siguientes elementos tienen un valor de 0!")
                for elemento in elementos_con_cero:
                    print(f"- {elemento}")
        elif opcion == '3':
            try:
                numero = int(input("Introduce el número a consultar: "))
                resultados = consultar_por_numero(elementos, numero)
                print(f"\nElementos con el número {numero}:")
                for i, resultado in enumerate(resultados, 1):
                    print(f"{i}. {resultado}")
                print(f"\n(Total {len(resultados)} Elementos)")
            except ValueError:
                print("Por favor, introduce un número válido.")
        elif opcion == '4':
            buscar_y_restar_unidades(nombre_archivo)
        elif opcion == '0':
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")

if __name__ == "__main__":
    main()