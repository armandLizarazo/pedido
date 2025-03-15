def agregar_elemento_pedido():
    # Solicitar el nombre del archivo de "Pedido" al inicio
    nombre_pedido = input("Ingrese el nombre del archivo de Pedido (sin extensión .txt): ") + ".txt"
    print(f"Archivo de Pedido seleccionado: {nombre_pedido}")
    
    while True:
        # Solicitar la descripción del elemento
        descripcion = input("Ingrese la descripción del elemento (o escriba 'exit' para terminar): ")
        
        # Verificar si el usuario desea salir
        if descripcion.lower() == "exit":
            print("Saliendo del programa...")
            break
        
        # Solicitar la cantidad del elemento
        cantidad = int(input("Ingrese la cantidad del elemento: "))
        
        # Verificar si el elemento existe en bodegac.txt
        with open("bodegac.txt", "r") as bodega:
            elementos_bodega = bodega.readlines()
        
        elemento_encontrado = False
        for linea in elementos_bodega:
            if descripcion in linea:
                elemento_encontrado = True
                break
        
        # Si el elemento no existe en bodegac.txt, preguntar al usuario si desea agregarlo
        if not elemento_encontrado:
            respuesta = input(f"El elemento '{descripcion}' no existe en bodegac.txt. ¿Desea agregarlo? (s/n): ").strip().lower()
            if respuesta != 's':
                print("El elemento no fue agregado.")
                continue  # Volver al inicio del bucle
            else:
                # Agregar el elemento a bodegac.txt
                with open("bodegac.txt", "a") as bodega:
                    bodega.write(f"    {descripcion} 0\n")  # Se agrega con cantidad 0 inicialmente
                print(f"El elemento '{descripcion}' ha sido agregado a bodegac.txt.")
        
        # Verificar si el elemento ya existe en el archivo de "Pedido"
        try:
            with open(nombre_pedido, "r") as pedido:
                lineas_pedido = pedido.readlines()
        except FileNotFoundError:
            # Si el archivo no existe, se crea vacío
            lineas_pedido = []
        
        elemento_en_pedido = False
        for i, linea in enumerate(lineas_pedido):
            if descripcion in linea:
                elemento_en_pedido = True
                # Extraer la cantidad actual
                cantidad_actual = int(linea.strip().split()[-1])
                print(f"El elemento '{descripcion}' ya existe en el archivo '{nombre_pedido}' con una cantidad de {cantidad_actual}.")
                
                # Preguntar al usuario si desea modificar la cantidad
                respuesta = input("¿Desea modificar la cantidad? (s/n): ").strip().lower()
                if respuesta == 's':
                    nueva_cantidad = int(input("Ingrese la nueva cantidad: "))
                    # Actualizar la línea con la nueva cantidad
                    lineas_pedido[i] = f"    {descripcion} {nueva_cantidad}\n"
                    with open(nombre_pedido, "w") as pedido:
                        pedido.writelines(lineas_pedido)
                    print(f"La cantidad del elemento '{descripcion}' ha sido actualizada a {nueva_cantidad}.")
                else:
                    print("La cantidad no ha sido modificada.")
                break
        
        # Si el elemento no existe en el archivo de "Pedido", agregarlo
        if not elemento_en_pedido:
            with open(nombre_pedido, "a") as pedido:
                pedido.write(f"    {descripcion} {cantidad}\n")
            print(f"El elemento '{descripcion}' ha sido agregado al archivo '{nombre_pedido}' con una cantidad de {cantidad}.")

# Ejecutar la función
agregar_elemento_pedido()