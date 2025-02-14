import os
from datetime import datetime

class GestorInventario:
    def __init__(self):
        self.archivo_inventario = "bodegac.txt"
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        """Crea el archivo si no existe"""
        if not os.path.exists(self.archivo_inventario):
            with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                pass

    def imprimir_contenido(self, filtro_cantidad=None, operador=None):
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
                if not lineas:
                    print("\nEl archivo está vacío.")
                    return 0
                
                # Lista para almacenar advertencias y líneas inválidas
                advertencias = []
                lineas_invalidas = []
                
                # Verificar cada línea en busca de errores
                for i, linea in enumerate(lineas, 1):
                    linea = linea.strip()
                    partes = linea.rsplit(' ', 1)  # Divide desde la derecha en 2 partes
                    
                    if len(partes) == 2:
                        descripcion, cantidad = partes
                        try:
                            cantidad = int(cantidad)  # Intenta convertir la cantidad a entero
                        except ValueError:
                            advertencias.append(f"{i}. [ADVERTENCIA] Línea inválida: {linea} (la cantidad no es un número)")
                            lineas_invalidas.append(i - 1)  # Guarda el índice de la línea inválida
                    else:
                        advertencias.append(f"{i}. [ADVERTENCIA] Línea inválida: {linea} (formato incorrecto)")
                        lineas_invalidas.append(i - 1)  # Guarda el índice de la línea inválida
                
                # Mostrar advertencias si las hay
                if advertencias:
                    print("\n=== ADVERTENCIAS ===")
                    for advertencia in advertencias:
                        print(advertencia)
                    
                    # Preguntar al usuario qué desea hacer
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
                        # Corregir líneas inválidas
                        for indice in lineas_invalidas:
                            print(f"\nCorrigiendo línea {indice + 1}: {lineas[indice].strip()}")
                            nueva_cantidad = input("Ingrese la nueva cantidad (o presione Enter para omitir): ").strip()
                            
                            if nueva_cantidad:
                                try:
                                    nueva_cantidad = int(nueva_cantidad)  # Validar que sea un número
                                    # Agrega la nueva cantidad al final de la línea sin eliminar la descripción
                                    lineas[indice] = f"    {lineas[indice].strip()} {nueva_cantidad}\n"
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
                
                # Si el usuario decide continuar, imprimir el contenido válido
                print("\n=== CONTENIDO DEL INVENTARIO ===")
                for i, linea in enumerate(lineas, 1):
                    linea = linea.strip()
                    partes = linea.rsplit(' ', 1)
                    
                    if len(partes) == 2:
                        descripcion, cantidad = partes
                        try:
                            cantidad = int(cantidad)
                            
                            # Aplica el filtro si se proporciona
                            if filtro_cantidad is not None and operador is not None:
                                if operador == ">" and cantidad > filtro_cantidad:
                                    print(f"{i}. {descripcion} {cantidad}")
                                elif operador == "<" and cantidad < filtro_cantidad:
                                    print(f"{i}. {descripcion} {cantidad}")
                                elif operador == "=" and cantidad == filtro_cantidad:
                                    print(f"{i}. {descripcion} {cantidad}")
                            else:
                                print(f"{i}. {descripcion} {cantidad}")
                        except ValueError:
                            # Ignorar líneas inválidas (ya se mostraron en las advertencias)
                            pass
                    else:
                        # Ignorar líneas inválidas (ya se mostraron en las advertencias)
                        pass
                
                return len(lineas)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
            return 0
    def agregar_linea(self, descripcion, cantidad):
        try:
            cantidad = int(cantidad)
            with open(self.archivo_inventario, 'a', encoding='latin-1') as f:
                f.write(f"    {descripcion} {cantidad}\n")  # Agrega 4 espacios al inicio
            print("\nLínea agregada correctamente.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")

    def modificar_linea(self, numero_linea, nueva_descripcion, nueva_cantidad):
        try:
            nueva_cantidad = int(nueva_cantidad)
            lineas = []
            
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                lineas[numero_linea - 1] = f"    {nueva_descripcion} {nueva_cantidad}\n"  # Mantiene los 4 espacios
                
                with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                    f.writelines(lineas)
                print("\nLínea modificada correctamente.")
            else:
                print("\nError: Número de línea fuera de rango.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")

    def modificar_cantidad(self, numero_linea, cambio_cantidad):
        try:
            cambio_cantidad = int(cambio_cantidad)
            lineas = []
            
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                descripcion, cantidad = lineas[numero_linea - 1].strip().rsplit(' ', 1)
                nueva_cantidad = int(cantidad) + cambio_cantidad
                lineas[numero_linea - 1] = f"    {descripcion} {nueva_cantidad}\n"  # Mantiene los 4 espacios
                
                with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                    f.writelines(lineas)
                print("\nCantidad modificada correctamente.")
            else:
                print("\nError: Número de línea fuera de rango.")
        except ValueError:
            print("Error: La cantidad debe ser un número válido.")

    def eliminar_linea(self, numero_linea):
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()
            
            if 1 <= numero_linea <= len(lineas):
                linea_eliminada = lineas[numero_linea - 1].strip()
                del lineas[numero_linea - 1]
                
                with open(self.archivo_inventario, 'w', encoding='latin-1') as f:
                    f.writelines(lineas)
                print(f"\nLínea eliminada: {linea_eliminada}")
            else:
                print("\nError: Número de línea fuera de rango.")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

    def filtrar_por_palabra(self, palabra):
        try:
            with open(self.archivo_inventario, 'r', encoding='latin-1') as f:
                lineas = f.readlines()            
            if not lineas:
                print("\nEl archivo está vacío.")
                return
            
            palabra = palabra.lower()
            lineas_filtradas = []
            
            for i, linea in enumerate(lineas, 1):
                if palabra in linea.lower():
                    lineas_filtradas.append((i, linea.strip()))
            
            if lineas_filtradas:
                print(f"\nLíneas que contienen '{palabra}':")
                for num_linea, contenido in lineas_filtradas:
                    print(f"{num_linea}. {contenido}")
            else:
                print(f"\nNo se encontraron líneas que contengan '{palabra}'")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

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
    print("0. Salir")
    return input("\nSeleccione una opción: ")

def main():
    gestor = GestorInventario()
    
    while True:
        opcion = mostrar_menu()
        
        if opcion == "1":
            gestor.imprimir_contenido()
        
        elif opcion == "2":
            try:
                cantidad = int(input("Ingrese la cantidad para filtrar: "))
                print("\nSeleccione el tipo de filtro:")
                print("1. Mayor que (>)")
                print("2. Menor que (<)")
                print("3. Igual a (=)")
                filtro = input("Seleccione una opción (1-3): ").strip()
                
                operador = {
                    "1": ">",
                    "2": "<",
                    "3": "="
                }.get(filtro)
                
                if operador:
                    gestor.imprimir_contenido(cantidad, operador)
                else:
                    print("Opción de filtro inválida. Debe ser 1, 2 o 3.")
            except ValueError:
                print("Error: La cantidad debe ser un número válido")
        
        elif opcion == "3":
            descripcion = input("Ingrese la descripción del item: ")
            cantidad = input("Ingrese la cantidad: ")
            gestor.agregar_linea(descripcion, cantidad)
        
        elif opcion == "4":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a modificar: "))
                    descripcion = input("Ingrese la nueva descripción: ")
                    cantidad = input("Ingrese la nueva cantidad: ")
                    gestor.modificar_linea(linea, descripcion, cantidad)
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "5":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a modificar: "))
                    cantidad = input("Ingrese la cantidad a agregar: ")
                    gestor.modificar_cantidad(linea, cantidad)
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "6":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a modificar: "))
                    cantidad = input("Ingrese la cantidad a quitar: ")
                    gestor.modificar_cantidad(linea, str(-int(cantidad)))
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "7":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a eliminar: "))
                    gestor.eliminar_linea(linea)
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "8":
            palabra = input("Ingrese la palabra a buscar: ")
            gestor.filtrar_por_palabra(palabra)
        
        elif opcion == "0":
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\nOpción inválida")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()