import os
from datetime import datetime

class GestorInventario:
    def __init__(self, archivo_inventario='bodegac.txt', archivo_reportes='reportes.txt'):
        self.archivo_inventario = archivo_inventario
        self.archivo_reportes = archivo_reportes
        self.crear_archivos_si_no_existen()

    def crear_archivos_si_no_existen(self):
        """Crea los archivos si no existen"""
        for archivo in [self.archivo_inventario, self.archivo_reportes]:
            if not os.path.exists(archivo):
                with open(archivo, 'w', encoding='utf-8') as f:
                    pass

    def registrar_movimiento(self, descripcion):
        """Registra un movimiento en el archivo de reportes"""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.archivo_reportes, 'a', encoding='utf-8') as f:
            f.write(f"[{fecha}] {descripcion}\n")

    def imprimir_contenido(self):
        """Imprime el contenido actual del inventario"""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
                if not lineas:
                    print("\nEl archivo está vacío.")
                else:
                    print("\nContenido actual del inventario:")
                    for i, linea in enumerate(lineas, 1):
                        print(f"{i}. {linea.strip()}")
            self.registrar_movimiento("Se consultó el contenido del inventario")
            self.verificar_cantidades()
            return len(lineas)  # Retorna el número total de líneas
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")
            return 0

    def agregar_linea(self, descripcion, cantidad):
        """Agrega una nueva línea al inventario"""
        try:
            cantidad = int(cantidad)
            with open(self.archivo_inventario, 'a', encoding='utf-8') as f:
                f.write(f"    {descripcion} {cantidad}\n")  # 4 espacios al inicio
            self.registrar_movimiento(f"Se agregó nuevo item: {descripcion} {cantidad}")
            print(f"\nSe agregó: {descripcion} {cantidad}")
            self.verificar_cantidades()
        except ValueError:
            print("Error: La cantidad debe ser un número entero")

    def modificar_cantidad(self, numero_linea, cambio_cantidad):
        """Modifica la cantidad de una línea sumando o restando al valor existente"""
        try:
            cambio_cantidad = int(cambio_cantidad)
            lineas = []
            
            # Leer el archivo
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()

            if 1 <= numero_linea <= len(lineas):
                # Separar la línea en descripción y cantidad
                linea_actual = lineas[numero_linea - 1].strip()
                partes = linea_actual.rsplit(' ', 1)
                if len(partes) == 2:
                    descripcion, cantidad_actual = partes
                    cantidad_actual = int(cantidad_actual)
                    nueva_cantidad = cantidad_actual + cambio_cantidad
                    
                    # Actualizar la línea manteniendo los 4 espacios al inicio
                    lineas[numero_linea - 1] = f"    {descripcion} {nueva_cantidad}\n"
                    
                    # Escribir todas las líneas de vuelta al archivo
                    with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                        f.writelines(lineas)
                    
                    self.registrar_movimiento(
                        f"Se modificó la cantidad del item '{descripcion}' "
                        f"de {cantidad_actual} a {nueva_cantidad} (cambio: {cambio_cantidad:+d})"
                    )
                    print(f"\nCantidad actualizada para la línea {numero_linea}")
                    print(f"Cantidad anterior: {cantidad_actual}")
                    print(f"Cambio aplicado: {cambio_cantidad:+d}")
                    print(f"Nueva cantidad: {nueva_cantidad}")
                    self.verificar_cantidades()
                else:
                    print("Error: Formato de línea inválido")
            else:
                print(f"Error: El número de línea debe estar entre 1 y {len(lineas)}")
        except ValueError:
            print("Error: La cantidad debe ser un número entero")

    def verificar_cantidades(self):
        """Verifica si hay líneas con cantidad 0 o menor"""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            lineas_problema = []
            for i, linea in enumerate(lineas, 1):
                partes = linea.strip().rsplit(' ', 1)
                if len(partes) == 2:
                    descripcion, cantidad = partes
                    try:
                        if int(cantidad) <= 0:
                            lineas_problema.append((i, descripcion, cantidad))
                    except ValueError:
                        print(f"Error en línea {i}: Cantidad no válida")

            if lineas_problema:
                print("\n¡ADVERTENCIA! Las siguientes líneas tienen cantidad 0 o menor:")
                for num_linea, desc, cant in lineas_problema:
                    print(f"Línea {num_linea}: {desc} {cant}")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

    def ver_reportes(self, ultimas_n_lineas=None):
        """Muestra los últimos movimientos registrados"""
        try:
            with open(self.archivo_reportes, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if not lineas:
                print("\nNo hay reportes registrados.")
                return

            if ultimas_n_lineas:
                lineas = lineas[-ultimas_n_lineas:]

            print("\nReporte de movimientos:")
            for linea in lineas:
                print(linea.strip())
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_reportes}")

    def eliminar_linea(self, numero_linea):
        """Elimina una línea específica del inventario"""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if 1 <= numero_linea <= len(lineas):
                # Obtener la línea que se va a eliminar para el reporte
                linea_eliminada = lineas[numero_linea - 1].strip()
                # Eliminar la línea
                del lineas[numero_linea - 1]
                
                # Escribir las líneas actualizadas al archivo
                with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                    f.writelines(lineas)
                
                self.registrar_movimiento(f"Se eliminó la línea: {linea_eliminada}")
                print(f"\nSe eliminó la línea {numero_linea}: {linea_eliminada}")
            else:
                print(f"Error: El número de línea debe estar entre 1 y {len(lineas)}")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

    def ordenar_alfabeticamente(self):
        """Ordena las líneas del inventario alfabéticamente"""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if not lineas:
                print("\nEl archivo está vacío.")
                return
            
            # Ordenar las líneas ignorando los espacios iniciales
            lineas_ordenadas = sorted(lineas, key=lambda x: x.strip())
            
            # Escribir las líneas ordenadas al archivo
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                f.writelines(lineas_ordenadas)
            
            self.registrar_movimiento("Se ordenó el inventario alfabéticamente")
            print("\nInventario ordenado alfabéticamente.")
            self.imprimir_contenido()
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

    def filtrar_por_palabra(self, palabra):
        """Muestra las líneas que contienen la palabra o palabras especificadas"""
        try:
            with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
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
            
            self.registrar_movimiento(f"Se filtró el inventario por la palabra: {palabra}")
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {self.archivo_inventario}")

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n=== GESTOR DE INVENTARIO ===")
    print("1. Ver contenido actual")
    print("2. Agregar nueva línea")
    print("3. Agregar unidades a línea existente")
    print("4. Quitar unidades a línea existente")
    print("5. Ver reportes")
    print("6. Eliminar línea")
    print("7. Ordenar alfabéticamente")
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
            descripcion = input("Ingrese la descripción del item: ")
            cantidad = input("Ingrese la cantidad: ")
            gestor.agregar_linea(descripcion, cantidad)
        
        elif opcion == "3":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a modificar: "))
                    cantidad = input("Ingrese la cantidad a agregar: ")
                    gestor.modificar_cantidad(linea, cantidad)
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "4":
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a modificar: "))
                    cantidad = input("Ingrese la cantidad a quitar: ")
                    gestor.modificar_cantidad(linea, str(-int(cantidad)))
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "5":
            try:
                n = input("¿Cuántos últimos movimientos desea ver? (Enter para ver todos): ")
                n = int(n) if n.strip() else None
                gestor.ver_reportes(n)
            except ValueError:
                print("Error: Ingrese un número válido")
        
        elif opcion == "6":  # Nueva opción: Eliminar línea
            total_lineas = gestor.imprimir_contenido()
            if total_lineas > 0:
                try:
                    linea = int(input("\nIngrese el número de línea a eliminar: "))
                    gestor.eliminar_linea(linea)
                except ValueError:
                    print("Error: Ingrese un número válido")
        
        elif opcion == "7":  # Nueva opción: Ordenar alfabéticamente
            gestor.ordenar_alfabeticamente()
        
        elif opcion == "8":  # Nueva opción: Filtrar por palabra
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