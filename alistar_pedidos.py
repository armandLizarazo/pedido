import os # Importar os para manejo de archivos y directorios si es necesario

def agregar_elemento_pedido_modificado():
    """
    Permite agregar o modificar elementos y sus cantidades en diferentes archivos de pedido,
    verificando contra un inventario central (bodegac.txt).
    Utiliza encoding 'latin-1' para bodegac.txt y archivos de pedido.
    Agrega 4 espacios de indentación a las líneas en los archivos de pedido.
    Agrega items a bodegac.txt con indentación y cantidad 0 por defecto.
    Sale del programa al ingresar 'exit' en el prompt de descripción.
    """
    archivo_bodega = "bodegac.txt"
    # Especificar la codificación al leer/escribir bodegac.txt
    encoding_bodega = 'latin-1'

    # Asegurarse que el archivo de bodega exista, si no, crearlo vacío con la codificación correcta
    if not os.path.exists(archivo_bodega):
        print(f"Advertencia: El archivo '{archivo_bodega}' no existe. Se creará uno vacío.")
        try:
            # Usar encoding al crear el archivo
            with open(archivo_bodega, "w", encoding=encoding_bodega) as bodega:
                # Escribir un encabezado o dejarlo vacío, sin indentación para el encabezado
                bodega.write("# Inventario Central\n")
        except IOError:
            print(f"Error crítico: No se pudo crear el archivo '{archivo_bodega}'. Verifique los permisos.")
            return # Salir si no se puede crear el archivo base

    while True:
        # 1. Solicitar la descripción del elemento
        descripcion = input("Ingrese la descripción del elemento (o escriba 'exit' para terminar): ").strip()

        # Verificar si el usuario desea salir (ANTES de pedir cantidad o archivo)
        if descripcion.lower() == "exit":
            print("Saliendo del programa...")
            break # Este break debería terminar el bucle while True inmediatamente.

        if not descripcion: # Si el usuario solo presiona Enter
            print("La descripción no puede estar vacía.")
            continue

        # 2. Solicitar la cantidad del elemento (para el pedido)
        while True:
            try:
                cantidad_str = input(f"Ingrese la cantidad para '{descripcion}' (para el pedido): ")
                cantidad = int(cantidad_str)
                if cantidad < 0:
                    print("La cantidad no puede ser negativa.")
                else:
                    break # Salir del bucle de cantidad si es válida
            except ValueError:
                print("Por favor, ingrese un número entero válido para la cantidad.")

        # --- Verificación y posible adición a Bodega ---
        elemento_en_bodega = False
        elementos_bodega = [] # Inicializar lista
        try:
            # Usar encoding al leer
            with open(archivo_bodega, "r", encoding=encoding_bodega) as bodega:
                elementos_bodega = bodega.readlines()

            # *** MODIFICACIÓN AQUÍ: Actualizar lógica de búsqueda en bodega ***
            for linea in elementos_bodega:
                linea_stripped = linea.strip()
                # Ignorar líneas vacías o comentarios
                if not linea_stripped or linea_stripped.startswith('#'):
                    continue

                partes_bodega = linea_stripped.split()
                # Verificar si la línea tiene al menos descripción y cantidad
                if len(partes_bodega) >= 2:
                    # Reconstruir descripción (todo menos el último elemento, que es la cantidad)
                    descripcion_bodega = " ".join(partes_bodega[:-1])
                    # Comparar descripción ignorando mayúsculas/minúsculas
                    if descripcion_bodega.lower() == descripcion.lower():
                        elemento_en_bodega = True
                        # Podríamos opcionalmente leer la cantidad de bodega aquí si fuera necesario
                        # cantidad_bodega = partes_bodega[-1]
                        break # Elemento encontrado
                # Opcional: manejar líneas con formato antiguo (solo descripción) si es necesario
                # elif len(partes_bodega) == 1:
                #     if partes_bodega[0].lower() == descripcion.lower():
                #         elemento_en_bodega = True
                #         break

        except FileNotFoundError:
            print(f"Error: No se pudo leer el archivo '{archivo_bodega}'.")
            continue
        except Exception as e:
            print(f"Error inesperado al leer '{archivo_bodega}': {e}")
            continue


        # Si el elemento no existe en bodegac.txt, preguntar al usuario si desea agregarlo
        if not elemento_en_bodega:
            respuesta_bodega = input(f"El elemento '{descripcion}' no existe en '{archivo_bodega}'. ¿Desea agregarlo al inventario? (s/n): ").strip().lower()
            if respuesta_bodega == 's':
                try:
                    # Usar encoding al añadir
                    with open(archivo_bodega, "a", encoding=encoding_bodega) as bodega:
                        # *** MODIFICACIÓN AQUÍ: Añadir con cantidad 0 por defecto ***
                        bodega.write(f"    {descripcion} 0\n")
                    print(f"El elemento '{descripcion}' ha sido agregado a '{archivo_bodega}' con cantidad 0 (con indentación).")
                    # Actualizar la lista en memoria consistentemente
                    elementos_bodega.append(f"    {descripcion} 0\n")
                except IOError:
                    print(f"Error: No se pudo escribir en el archivo '{archivo_bodega}'.")
            else:
                print(f"El elemento '{descripcion}' no fue agregado a '{archivo_bodega}'. No se puede agregar al pedido si no está en bodega.")
                continue


        # 3. Solicitar el nombre del archivo de "Pedido"
        while True:
            nombre_pedido_base = input(f"Ingrese el nombre del archivo de Pedido para '{descripcion}' (sin extensión .txt): ").strip()
            if nombre_pedido_base:
                nombre_pedido = nombre_pedido_base + ".txt"
                print(f"Archivo de Pedido seleccionado: {nombre_pedido}")
                break
            else:
                print("El nombre del archivo no puede estar vacío.")


        # --- Verificación y adición/modificación en el Archivo de Pedido específico ---
        encoding_pedido = 'latin-1' # Mantener encoding para archivos de pedido
        lineas_pedido = []
        try:
            # Intentar leer el archivo de pedido específico con encoding
            with open(nombre_pedido, "r", encoding=encoding_pedido) as pedido:
                lineas_pedido = pedido.readlines()
        except FileNotFoundError:
            print(f"El archivo '{nombre_pedido}' no existe. Se creará si agrega elementos.")
        except UnicodeDecodeError:
             print(f"Error de codificación al leer '{nombre_pedido}'. Intenta verificar su codificación.")
             continue
        except IOError:
            print(f"Error al leer el archivo '{nombre_pedido}'. No se podrá procesar.")
            continue

        elemento_en_pedido = False
        indice_elemento = -1
        cantidad_actual = 0

        # Buscar el elemento en las líneas leídas del pedido
        for i, linea in enumerate(lineas_pedido):
            # Usar strip() para quitar espacios al inicio/final antes de dividir
            partes = linea.strip().split()
            if len(partes) >= 2:
                # Reconstruir descripción si tiene espacios
                descripcion_linea = " ".join(partes[:-1])
                if descripcion_linea.lower() == descripcion.lower():
                    elemento_en_pedido = True
                    indice_elemento = i
                    try:
                        cantidad_actual = int(partes[-1])
                    except ValueError:
                        print(f"Advertencia: Formato de cantidad inválido en línea {i+1} del archivo '{nombre_pedido}'. Se ignorará la línea.")
                        elemento_en_pedido = False
                    break

        if elemento_en_pedido:
            print(f"El elemento '{descripcion}' ya existe en '{nombre_pedido}' con cantidad {cantidad_actual}.")
            respuesta_modificar = input("¿Desea modificar la cantidad? (s/n): ").strip().lower()
            if respuesta_modificar == 's':
                nueva_cantidad = cantidad # Usar la cantidad pedida al inicio para el pedido
                # Añadir 4 espacios al inicio de la línea actualizada
                lineas_pedido[indice_elemento] = f"    {descripcion} {nueva_cantidad}\n"
                try:
                    with open(nombre_pedido, "w", encoding=encoding_pedido) as pedido:
                        pedido.writelines(lineas_pedido)
                    print(f"Cantidad de '{descripcion}' actualizada a {nueva_cantidad} en '{nombre_pedido}' (con indentación).")
                except IOError:
                     print(f"Error: No se pudo escribir en el archivo '{nombre_pedido}'.")
            else:
                print("La cantidad no ha sido modificada.")
        else:
            # Añadir 4 espacios al inicio de la nueva línea
            nueva_linea = f"    {descripcion} {cantidad}\n" # Usar la cantidad pedida al inicio para el pedido
            try:
                with open(nombre_pedido, "a", encoding=encoding_pedido) as pedido:
                    pedido.write(nueva_linea)
                print(f"Elemento '{descripcion}' agregado a '{nombre_pedido}' con cantidad {cantidad} (con indentación).")
            except IOError:
                print(f"Error: No se pudo escribir en el archivo '{nombre_pedido}'.")

# Ejecutar la función modificada
agregar_elemento_pedido_modificado()
