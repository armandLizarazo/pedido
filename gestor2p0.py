import os
import sys
import platform

# Configurar la codificación para la entrada/salida estándar
if sys.stdout.encoding != 'latin-1':
    try:
        sys.stdout.reconfigure(encoding='latin-1')
    except AttributeError:
        # Para versiones anteriores de Python que no tienen reconfigure
        pass

class GestorInventario:
    def __init__(self, archivo_inventario=None):
        self.archivo_inventario = archivo_inventario or "bodegac.txt"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        """Crea el archivo si no existe"""
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                pass

    def cambiar_archivo(self, nuevo_archivo):
        """Cambia el archivo de inventario actual"""
        self.archivo_inventario = nuevo_archivo
        self.crear_archivos_si_no_existen()
        print(f"\nArchivo cambiado a: {self.archivo_inventario}")

    def imprimir_contenido(self, filtro_cantidad=None, operador=None, palabra_clave=None):
        """
        Imprime el contenido del archivo de inventario, con opción de filtrar por cantidad y palabra clave.

        Args:
            filtro_cantidad (int, opcional): Cantidad para filtrar.
            operador (str, opcional): Operador de comparación ('>', '<', '=').
            palabra_clave (str, opcional): Palabra clave para filtrar.
        """
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
                if not lineas:
                    print(f"\nEl archivo {self.archivo_inventario} está vacío.")
                    return 0
                
                advertencias = []
                lineas_invalidas = []
                total_items_filtrados = 0 
                suma_cantidades = 0
                
                for i, linea in enumerate(lineas, 1):
                    linea = linea.strip()
                    partes = linea.rsplit(' ', 1)
                    
                    if len(partes) == 2:
                        descripcion, cantidad = partes
                        try:
                            cantidad = int(cantidad)
                        except ValueError:
                            advertencias.append(f"{i}. [ADVERTENCIA] Línea inválida: {linea} (la cantidad no es un número)")
                            lineas_invalidas.append(i - 1)
                    else:
                        advertencias.append(f"{i}. [ADVERTENCIA] Línea inválida: {linea} (formato incorrecto)")
                        lineas_invalidas.append(i - 1)
                
                if advertencias:
                    print("\n=== ADVERTENCIAS ===")
                    for advertencia in advertencias:
                        print(advertencia)
                    
                    print("\nOpciones:")
                    print("1. Continuar (ignorar líneas inválidas)")
                    print("2. Cancelar proceso")
                    print("3. Corregir líneas inválidas")
                    opcion = input("Seleccione una opción (1-3): ").strip()
                    
                    if opcion == "1":
                        print("\nContinuando con el proceso...")
                    elif opcion == "2":
                        print("Proceso cancelado.")
                        return 0
                    elif opcion == "3":
                        for indice in lineas_invalidas:
                            print(f"\nCorrigiendo línea {indice + 1}: {lineas[indice].strip()}")
                            nueva_cantidad = input("Ingrese la nueva cantidad (o presione Enter para omitir): ").strip()
                            
                            if nueva_cantidad:
                                try:
                                    nueva_cantidad = int(nueva_cantidad)  # Validar que sea un número
                                    descripcion = lineas[indice].strip().rsplit(' ', 1)[0] if len(lineas[indice].strip().rsplit(' ', 1)) > 1 else lineas[indice].strip()
                                    lineas[indice] = f"    {descripcion} {nueva_cantidad}\n"
                                    print("Línea corregida correctamente.")
                                except ValueError:
                                    print("Error: La cantidad debe ser un número válido. No se realizaron cambios.")
                            else:
                                print("La línea no fue modificada.")
                        
                        # Guardar los cambios en el archivo
                        with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                            f.writelines(lineas)
                        print("\nCambios guardados en el archivo.")
                    else:
                        print("Opción inválida. Continuando con el proceso...")
                
                print(f"\n=== CONTENIDO DEL INVENTARIO ({self.archivo_inventario}) ===")
                if filtro_cantidad is not None and operador is not None:
                    print("==================================================================")
                    print("| Línea | Cant | Item                                                       |")
                    print("==================================================================")
                    
                    encontrado = False  # Para verificar si se encontraron elementos
                    for i, linea in enumerate(lineas, 1):
                        linea = linea.strip()
                        partes = linea.rsplit(' ', 1)
                        
                        if len(partes) == 2:
                            descripcion, cantidad = partes
                            try:
                                cantidad = int(cantidad)
                                # Aplica el filtro
                                if operador == ">" and cantidad > filtro_cantidad:
                                    if palabra_clave:
                                        if palabra_clave.lower() in descripcion.lower():
                                            print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                            encontrado = True
                                            total_items_filtrados += 1
                                            suma_cantidades += cantidad
                                    else:
                                        print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                        encontrado = True
                                        total_items_filtrados += 1
                                        suma_cantidades += cantidad
                                elif operador == "<" and cantidad < filtro_cantidad:
                                    if palabra_clave:
                                        if palabra_clave.lower() in descripcion.lower():
                                            print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                            encontrado = True
                                            total_items_filtrados += 1
                                            suma_cantidades += cantidad
                                    else:
                                        print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                        encontrado = True
                                        total_items_filtrados += 1
                                        suma_cantidades += cantidad
                                elif operador == "=" and cantidad == filtro_cantidad:
                                    if palabra_clave:
                                        if palabra_clave.lower() in descripcion.lower():
                                             print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                             encontrado = True
                                             total_items_filtrados += 1
                                             suma_cantidades += cantidad
                                    else:
                                        print(f"| {i:<5} | {cantidad:<4} | {descripcion:<60} |")
                                        encontrado = True
                                        total_items_filtrados += 1
                                        suma_cantidades += cantidad
                            except ValueError:
                                pass
                        else:
                            pass
                    if not encontrado:
                        print("| No se encontraron elementos.                                                   |\n")
                    print("==================================================================")
                    print(f"Total de items filtrados: {total_items_filtrados}")
                    print(f"Suma de cantidades: {suma_cantidades}")
                else:
                    print("==========================================================")
                    print("| Línea | Cant | Item                                         |")
                    print("==========================================================")
                    for i, linea in enumerate(lineas, 1):
                        linea = linea.strip()
                        partes = linea.rsplit(' ', 1)
                        
                        if len(partes) == 2:
                            descripcion, cantidad = partes
                            try:
                                cantidad = int(cantidad)
                                if palabra_clave:
                                     if palabra_clave.lower() in descripcion.lower():
                                        print(f"| {i:<5} | {cantidad:<4} | {descripcion:<40}|")
                                else:
                                    print(f"| {i:<5} | {cantidad:<4} | {descripcion:<40}|")
                            except ValueError:
                                pass
                        else:
                            pass
                    print("==========================================================")
                return len(lineas)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
            return 0
        except UnicodeDecodeError:
            print(f"Error: No se pudo leer el archivo {self.archivo_inventario}. Posible problema de codificación.")
            return 0

    def agregar_linea(self, descripcion, cantidad):
        try:
            cantidad = int(cantidad)
            with open(self.archivo_inventario, 'a', encoding='latin-1') as f:
                f.write(f"    {descripcion} {cantidad}\n")
            print("\nLínea agregada correctamente.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")
        except UnicodeEncodeError:
            print("Error: No se pudo guardar. Hay caracteres que no pueden codificarse en latin-1.")

    def modificar_linea(self, numero_linea, nueva_descripcion, nueva_cantidad):
        try:
            nueva_cantidad = int(nueva_cantidad)
            lineas = []
            
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                lineas[numero_linea - 1] = f"    {nueva_descripcion} {nueva_cantidad}\n"
                
                with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                    f.writelines(lineas)
                print("\nLínea modificada correctamente.")
            else:
                print("\nError: Número de línea fuera de rango.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")
        except UnicodeEncodeError:
            print("Error: No se pudo guardar. Hay caracteres que no pueden codificarse en latin-1.")

    def modificar_cantidad(self, numero_linea, cambio_cantidad):
        try:
            cambio_cantidad = int(cambio_cantidad)
            lineas = []
            
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                linea = lineas[numero_linea - 1].strip()
                partes = linea.rsplit(' ', 1)
                
                if len(partes) == 2:
                    descripcion, cantidad = partes
                    try:
                        nueva_cantidad = int(cantidad) + cambio_cantidad
                        if nueva_cantidad < 0:
                            print("\nError: La cantidad no puede ser negativa.")
                            return
                        lineas[numero_linea - 1] = f"    {descripcion} {nueva_cantidad}\n"
                        
                        with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                            f.writelines(lineas)
                        print("\nCantidad modificada correctamente.")
                    except ValueError:
                        print("\nError: Cantidad inválida en el archivo.")
                else:
                    print("\nError: Formato de línea inválido.")
            else:
                print("\nError: Número de línea fuera de rango.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")
        except UnicodeEncodeError:
            print("Error: No se pudo guardar. Hay caracteres que no pueden codificarse en latin-1.")

    def eliminar_linea(self, numero_linea):
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
            
            if 1 <= numero_linea <= len(lineas):
                linea_eliminada = lineas[numero_linea - 1].strip()
                del lineas[numero_linea - 1]
                
                with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                    f.writelines(lineas)
                print(f"\nLínea eliminada correctamente: {linea_eliminada}")
            else:
                print("\nError: Número de línea fuera de rango.")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
        except UnicodeDecodeError:
            print(f"Error: No se pudo leer el archivo. Posible problema de codificación.")

    def filtrar_por_palabra_y_cantidad(self, palabra, tipo_filtro_cantidad=None, cantidad=None):
        """
        Filtra líneas del archivo por palabra clave y/o cantidad.

        Args:
            palabra (str): Palabra clave para filtrar.
            tipo_filtro_cantidad (str, opcional): Tipo de filtro de cantidad ('igual', 'mayor', 'menor').
            cantidad (int, opcional): Valor de cantidad para el filtro.
        """
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
            if not lineas:
                print(f"\nEl archivo {self.archivo_inventario} está vacío.")
                return

            palabra = palabra.lower()
            lineas_filtradas = []

            for i, linea in enumerate(lineas, 1):
                linea_lower = linea.lower()
                if palabra in linea_lower:
                    # Intenta extraer la cantidad de la línea
                    try:
                         # Dividir la línea por espacios, quedándonos con el último elemento que debería ser la cantidad
                        partes = linea.split()
                        cantidad_str = partes[-1]
                        cantidad_linea = int(cantidad_str)
                    except ValueError:
                        cantidad_linea = None

                    # Aplica el filtro de cantidad si se especifica
                    if tipo_filtro_cantidad and cantidad is not None and cantidad_linea is not None:
                        if tipo_filtro_cantidad == 'igual' and cantidad_linea == cantidad:
                            lineas_filtradas.append((i, linea.strip()))
                        elif tipo_filtro_cantidad == 'mayor' and cantidad_linea > cantidad:
                            lineas_filtradas.append((i, linea.strip()))
                        elif tipo_filtro_cantidad == 'menor' and cantidad_linea < cantidad:
                            lineas_filtradas.append((i, linea.strip()))
                    elif tipo_filtro_cantidad is None or cantidad is None:
                        # Si no hay filtro de cantidad, agrega la línea directamente
                        lineas_filtradas.append((i, linea.strip()))

            if lineas_filtradas:
                print(f"\nLíneas que contienen '{palabra}' y cumplen con los criterios de cantidad:")
                for num_linea, contenido in lineas_filtradas:
                    print(f"{num_linea}. {contenido}")
            else:
                print(f"\nNo se encontraron líneas que coincidan con los criterios de búsqueda.")

        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
        except UnicodeDecodeError:
            print(f"Error: No se pudo leer el archivo. Posible problema de codificación.")

    def ordenar_alfabeticamente(self):
        """Ordena alfabéticamente las líneas del archivo de inventario."""
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
            
            if not lineas:
                print(f"\nEl archivo {self.archivo_inventario} está vacío.")
                return

            # Ordenar las líneas alfabéticamente, ignorando mayúsculas y minúsculas
            lineas.sort(key=lambda linea: linea.lower())
            
            # Sobreescribir el archivo con las líneas ordenadas
            with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                f.writelines(lineas)
            
            print(f"\nEl archivo {self.archivo_inventario} ha sido ordenado alfabéticamente.")

        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
        except UnicodeDecodeError:
            print(f"Error: No se pudo leer el archivo. Posible problema de codificación.")
            

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n=== GESTOR DE INVENTARIO ===")
    print("1. Ver contenido actual")
    print("2. Ver contenido filtrado por cantidad")
    print("3. Agregar nueva línea")
    print("4. Modificar línea existente")
    print("5. Agregar unidades a línea existente")
    print("6. Quitar unidades a línea existente")
    print("7. Eliminar línea")
    print("8. Filtrar por palabra")
    print("9. Cambiar archivo de inventario")
    print("10. Ordenar alfabéticamente")
    print("0. Salir")
    return input("\nSeleccione una opción: ")

def main():
    # Intentar configurar la consola para latin-1 solo en Windows
    if platform.system() == "Windows":
        try:
            os.system("chcp 1252 > nul")
        except:
            pass
    
    archivo_predeterminado = "bodegac.txt"
    print(f"Archivo predeterminado: {archivo_predeterminado}")
    nuevo_archivo = input("Ingrese nombre de archivo a usar (Enter para usar el predeterminado): ").strip()
    archivo_a_usar = nuevo_archivo if nuevo_archivo else archivo_predeterminado
    
    gestor = GestorInventario(archivo_a_usar)
    
    while True:
        opcion = mostrar_menu()
        
        if opcion == "1":
            palabra_clave = input("Ingrese la palabra clave para filtrar (o Enter para mostrar todo): ")
            gestor.imprimir_contenido(palabra_clave=palabra_clave)
        
        elif opcion == "2":
            try:
                # Mostrar opciones de filtro
                print("\nSeleccione el tipo de filtro:")
                print("1. Mayor que (>)")
                print("2. Menor que (<)")
                print("3. Igual a (=)")
                print("4. Todos")
                filtro = input("Seleccione una opción (1-4): ").strip()
                
                if filtro in ("1", "2", "3"):
                    cantidad = int(input("\nIngrese la cantidad para filtrar: "))
                    palabra_clave = input("Ingrese la palabra clave para filtrar (o Enter para mostrar todo): ")
                    
                    operador = {
                        "1": ">",
                        "2": "<",
                        "3": "="
                    }.get(filtro)
                    
                    gestor.imprimir_contenido(cantidad, operador, palabra_clave)
                elif filtro == "4":
                    palabra_clave = input("Ingrese la palabra clave para filtrar (o Enter para mostrar todo): ")
                    gestor.imprimir_contenido(palabra_clave=palabra_clave)
                else:
                    print("Opción de filtro inválida. Debe ser 1, 2, 3 o 4.")
            except ValueError:
                print("Error: La cantidad debe ser un número válido")
        
        elif opcion == "3":
            descripcion = input("Ingrese la descripción del item: ")
            cantidad = input("Ingrese la cantidad: ")
            gestor.agregar_linea(descripcion, cantidad)
        
        elif opcion == "4":
            try:
                linea = int(input("\nIngrese el número de línea a modificar: "))
                descripcion = input("Ingrese la nueva descripción: ")
                cantidad = input("Ingrese la nueva cantidad: ")
                gestor.modificar_linea(linea, descripcion, cantidad)
            except ValueError:
                print("Error: Ingrese un número válido")
        
        elif opcion == "5":
            try:
                linea = int(input("\nIngrese el número de línea a modificar: "))
                cantidad = input("Ingrese la cantidad a agregar: ")
                gestor.modificar_cantidad(linea, cantidad)
            except ValueError:
                print("Error: Ingrese un número válido")
        
        elif opcion == "6":
            try:
                linea = int(input("\nIngrese el número de línea a modificar: "))
                cantidad = input("Ingrese la cantidad a quitar: ")
                gestor.modificar_cantidad(linea, str(-int(cantidad)))
            except ValueError:
                print("Error: Ingrese un número válido")
        
        elif opcion == "7":
            try:
                linea = int(input("\nIngrese el número de línea a eliminar: "))
                gestor.eliminar_linea(linea)
            except ValueError:
                print("Error: Ingrese un número válido")
        
        elif opcion == "8":
            palabra = input("Ingrese la palabra a buscar: ")
            # Mostrar opciones de filtro de cantidad
            print("\nOpciones de filtro de cantidad:")
            print("1. Mayor que (>)")
            print("2. Menor que (<)")
            print("3. Igual a (=)")
            print("4. Todos los elementos")
            filtro_cantidad = input("Seleccione una opción (1-4): ").strip()
            
            if filtro_cantidad in ("1", "2", "3"):
                cantidad_filtro = int(input("Ingrese la cantidad: "))
                operador = {
                    "1": ">",
                    "2": "<",
                    "3": "="
                }.get(filtro_cantidad)
                gestor.filtrar_por_palabra_y_cantidad(palabra, operador, cantidad_filtro)
            elif filtro_cantidad == "4":
                gestor.filtrar_por_palabra_y_cantidad(palabra)  # Llama a la función sin filtro de cantidad
            else:
                print("Opción de filtro de cantidad inválida. Debe ser 1, 2, 3 o 4.")
        
        elif opcion == "9":
            nuevo_archivo = input("Ingrese el nombre del nuevo archivo: ").strip()
            if nuevo_archivo:
                gestor.cambiar_archivo(nuevo_archivo)
            else:
                print("El nombre del archivo no puede estar vacío.")
        
        elif opcion == "10":
            gestor.ordenar_alfabeticamente()
        
        elif opcion == "0":
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\nOpción inválida")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()

