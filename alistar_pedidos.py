import os # Importar os para manejo de archivos y directorios si es necesario

def agregar_elemento_pedido_modificado():
    """
    Permite agregar o modificar elementos y sus cantidades en diferentes archivos de pedido,
    verificando contra un inventario central (bodegac.txt).
    Si un item existe en bodega con cantidad > 0, permite al usuario elegir cuántas unidades restar (0 a stock actual).
    Utiliza encoding 'latin-1' para bodegac.txt y archivos de pedido.
    Agrega 4 espacios de indentación a las líneas en los archivos de pedido.
    Agrega items a bodegac.txt con indentación y cantidad 0 por defecto.
    Sale del programa al ingresar 'exit' en el prompt de descripción.
    """
    archivo_bodega = "bodegac.txt"
    encoding_bodega = 'latin-1'
    encoding_pedido = 'latin-1' # Usar la misma codificación para pedidos por consistencia

    # --- Función auxiliar para escribir la lista de bodega completa ---
    def escribir_bodega(lineas_bodega):
        try:
            with open(archivo_bodega, "w", encoding=encoding_bodega) as bodega:
                bodega.writelines(lineas_bodega)
            return True
        except IOError as e:
            print(f"Error crítico al escribir en '{archivo_bodega}': {e}. No se guardaron los cambios en bodega.")
            return False

    # Asegurarse que el archivo de bodega exista
    if not os.path.exists(archivo_bodega):
        print(f"Advertencia: El archivo '{archivo_bodega}' no existe. Se creará uno vacío.")
        if not escribir_bodega([f"# Inventario Central\n"]):
             return # Salir si no se puede crear el archivo base

    while True:
        # 1. Solicitar la descripción del elemento
        descripcion = input("Ingrese la descripción del elemento (o escriba 'exit' para terminar): ").strip()

        if descripcion.lower() == "exit":
            print("Saliendo del programa...")
            break

        if not descripcion:
            print("La descripción no puede estar vacía.")
            continue

        # 2. Solicitar la cantidad del elemento (para el pedido)
        while True:
            try:
                cantidad_str = input(f"Ingrese la cantidad para '{descripcion}' (para el pedido): ")
                cantidad = int(cantidad_str) # Cantidad deseada para el pedido
                if cantidad < 0:
                    print("La cantidad no puede ser negativa.")
                elif cantidad == 0:
                    print("La cantidad para el pedido debe ser mayor que 0.")
                else:
                    break
            except ValueError:
                print("Por favor, ingrese un número entero válido para la cantidad.")

        # --- Verificación en Bodega ---
        elemento_en_bodega = False
        cantidad_bodega_actual = 0
        indice_bodega = -1
        elementos_bodega = [] # Leeremos las líneas aquí

        try:
            with open(archivo_bodega, "r", encoding=encoding_bodega) as bodega:
                elementos_bodega = bodega.readlines() # Leer todas las líneas para posible reescritura

            # Buscar el elemento y obtener su cantidad actual e índice
            for i, linea in enumerate(elementos_bodega):
                linea_stripped = linea.strip()
                if not linea_stripped or linea_stripped.startswith('#'):
                    continue

                partes_bodega = linea_stripped.split()
                if len(partes_bodega) >= 2:
                    descripcion_bodega = " ".join(partes_bodega[:-1])
                    if descripcion_bodega.lower() == descripcion.lower():
                        elemento_en_bodega = True
                        indice_bodega = i
                        try:
                            cantidad_bodega_actual = int(partes_bodega[-1])
                        except ValueError:
                            print(f"Advertencia: Formato de cantidad inválido en línea {i+1} de '{archivo_bodega}'. Se asume 0.")
                            cantidad_bodega_actual = 0
                        break # Elemento encontrado

        except FileNotFoundError:
            print(f"Error: No se pudo leer el archivo '{archivo_bodega}'.")
            continue
        except Exception as e:
            print(f"Error inesperado al leer '{archivo_bodega}': {e}")
            continue

        # --- Lógica de Adición a Bodega (si no existe) ---
        if not elemento_en_bodega:
            respuesta_bodega = input(f"El elemento '{descripcion}' no existe en '{archivo_bodega}'. ¿Desea agregarlo al inventario? (s/n): ").strip().lower()
            if respuesta_bodega == 's':
                nueva_linea_bodega = f"    {descripcion} 0\n"
                elementos_bodega.append(nueva_linea_bodega)
                if escribir_bodega(elementos_bodega):
                    print(f"El elemento '{descripcion}' ha sido agregado a '{archivo_bodega}' con cantidad 0 (con indentación).")
                    elemento_en_bodega = True
                    indice_bodega = len(elementos_bodega) - 1
                    cantidad_bodega_actual = 0
                else:
                    elementos_bodega.pop()
                    print(f"No se pudo agregar '{descripcion}' a bodega debido a error de escritura.")
                    continue
            else:
                print(f"El elemento '{descripcion}' no fue agregado a '{archivo_bodega}'. No se puede agregar al pedido si no está en bodega.")
                continue

        # --- Lógica de Descuento de Bodega (si existe y hay stock > 0) ---
        # *** MODIFICACIÓN AQUÍ: Solo actuar si hay stock > 0 ***
        if elemento_en_bodega and cantidad_bodega_actual > 0:
            print(f"\nInformación de Bodega: '{descripcion}' tiene {cantidad_bodega_actual} unidad(es) en '{archivo_bodega}'.")

            # Advertir si la cantidad pedida excede el stock, solo como información
            if cantidad > cantidad_bodega_actual:
                print(f"Advertencia: La cantidad solicitada para el pedido ({cantidad}) es mayor que el stock actual en bodega ({cantidad_bodega_actual}).")

            # *** MODIFICACIÓN AQUÍ: Preguntar cuánto restar, validar entrada ***
            while True: # Bucle para validar la cantidad a restar
                cantidad_a_restar_str = input(f"¿Cuántas unidades desea restar de bodega? (Ingrese 0 a {cantidad_bodega_actual}, o Enter para no restar): ").strip()

                if not cantidad_a_restar_str: # Si presiona Enter
                    cantidad_a_restar = 0
                    break

                try:
                    cantidad_a_restar = int(cantidad_a_restar_str)
                    if 0 <= cantidad_a_restar <= cantidad_bodega_actual:
                        break # Cantidad válida, salir del bucle
                    else:
                        print(f"Error: La cantidad a restar debe estar entre 0 y {cantidad_bodega_actual}.")
                except ValueError:
                    print("Error: Por favor ingrese un número válido o presione Enter.")

            # --- Realizar la resta si se especificó una cantidad > 0 ---
            if cantidad_a_restar > 0:
                nueva_cantidad_bodega = cantidad_bodega_actual - cantidad_a_restar
                # Actualizar la línea correcta en la lista 'elementos_bodega'
                elementos_bodega[indice_bodega] = f"    {descripcion} {nueva_cantidad_bodega}\n"
                # Re-escribir todo el archivo bodega con la línea actualizada
                if escribir_bodega(elementos_bodega):
                     print(f"OK: Se restaron {cantidad_a_restar} unidad(es). Cantidad en '{archivo_bodega}' actualizada a {nueva_cantidad_bodega}.")
                else:
                     print(f"Error: No se pudo actualizar la cantidad en '{archivo_bodega}'.")
                     # Considerar revertir el cambio en memoria si falla la escritura
                     # elementos_bodega[indice_bodega] = f"    {descripcion} {cantidad_bodega_actual}\n" # Revertir
            else:
                print(f"INFO: No se modificará el stock en '{archivo_bodega}'.")

        # --- Continuar con la gestión del archivo de Pedido ---
        # Ya no se muestra mensaje si cantidad_bodega_actual <= 0
        print(f"\nProcediendo a agregar/modificar '{descripcion}' en el archivo de pedido...")

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
        lineas_pedido = []
        try:
            with open(nombre_pedido, "r", encoding=encoding_pedido) as pedido:
                lineas_pedido = pedido.readlines()
        except FileNotFoundError:
            print(f"El archivo '{nombre_pedido}' no existe. Se creará al agregar elementos.")
        except UnicodeDecodeError:
             print(f"Error de codificación al leer '{nombre_pedido}'. Verifique su codificación.")
             continue
        except IOError:
            print(f"Error al leer el archivo '{nombre_pedido}'. No se podrá procesar.")
            continue

        elemento_en_pedido = False
        indice_pedido = -1
        cantidad_pedido_actual = 0

        for i, linea in enumerate(lineas_pedido):
            partes = linea.strip().split()
            if len(partes) >= 2:
                descripcion_linea = " ".join(partes[:-1])
                if descripcion_linea.lower() == descripcion.lower():
                    elemento_en_pedido = True
                    indice_pedido = i
                    try:
                        cantidad_pedido_actual = int(partes[-1])
                    except ValueError:
                        print(f"Advertencia: Formato inválido en línea {i+1} del archivo '{nombre_pedido}'.")
                        elemento_en_pedido = False # Ignorar línea mal formada
                    break

        if elemento_en_pedido:
            print(f"El elemento '{descripcion}' ya existe en '{nombre_pedido}' con cantidad {cantidad_pedido_actual}.")
            # *** MODIFICACIÓN AQUÍ: Simplificar, siempre sumar al existente o reemplazar? Preguntemos qué hacer ***
            # Opción 1: Siempre sumar la nueva cantidad a la existente
            # nueva_cantidad_pedido = cantidad_pedido_actual + cantidad
            # print(f"Se sumará {cantidad} a la cantidad existente. Nueva cantidad: {nueva_cantidad_pedido}")
            # lineas_pedido[indice_pedido] = f"    {descripcion} {nueva_cantidad_pedido}\n"
            # accion_pedido = "actualizada (sumada)"

            # Opción 2: Preguntar si reemplazar o sumar
            while True:
                resp_modif = input("¿Desea [R]eemplazar la cantidad existente con la nueva, [S]umar la nueva cantidad a la existente, o [N]o hacer nada? (R/S/N): ").strip().lower()
                if resp_modif == 'r':
                    nueva_cantidad_pedido = cantidad # Reemplazar con la cantidad pedida ahora
                    lineas_pedido[indice_pedido] = f"    {descripcion} {nueva_cantidad_pedido}\n"
                    accion_pedido = "actualizada (reemplazada)"
                    print(f"Cantidad reemplazada. Nueva cantidad: {nueva_cantidad_pedido}")
                    break
                elif resp_modif == 's':
                    nueva_cantidad_pedido = cantidad_pedido_actual + cantidad # Sumar
                    lineas_pedido[indice_pedido] = f"    {descripcion} {nueva_cantidad_pedido}\n"
                    accion_pedido = "actualizada (sumada)"
                    print(f"Cantidad sumada. Nueva cantidad: {nueva_cantidad_pedido}")
                    break
                elif resp_modif == 'n':
                    print("La cantidad en el pedido no ha sido modificada.")
                    accion_pedido = None # No hacer nada
                    break
                else:
                    print("Opción inválida. Por favor ingrese R, S o N.")

        else:
            # Agregar como nuevo al pedido
            nueva_linea_pedido = f"    {descripcion} {cantidad}\n"
            lineas_pedido.append(nueva_linea_pedido)
            accion_pedido = "agregado"

        # Escribir cambios en el archivo de pedido si es necesario
        if accion_pedido:
            try:
                with open(nombre_pedido, "w", encoding=encoding_pedido) as pedido:
                    pedido.writelines(lineas_pedido)
                print(f"OK: Elemento '{descripcion}' {accion_pedido} en '{nombre_pedido}' (con indentación).\n")
            except IOError:
                 print(f"Error: No se pudo escribir en el archivo '{nombre_pedido}'.\n")

# Ejecutar la función modificada
agregar_elemento_pedido_modificado()
