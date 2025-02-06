import pyperclip
from tabulate import tabulate
from datetime import datetime

def calcular_costo_base(venta, utilidad_porcentaje):
    """
    Calcula el costo base dado el valor de la venta y el porcentaje de utilidad.
    """
    utilidad_decimal = utilidad_porcentaje / 100
    costo_base = venta / (1 + utilidad_decimal)
    return costo_base

def contar_billetes():
    """
    Permite al usuario ingresar la cantidad de billetes para cada denominación,
    calcula el valor total por denominación y el monto total.
    Los resultados se muestran en una tabla y se guardan en un archivo.
    """
    denominaciones = [100000, 50000, 20000, 10000, 5000, 2000]  # 100.000 agregado
    total_general = 0
    tabla = []

    print("\n--- Contar billetes ---")
    nombre_conteo = input("Ingrese un nombre para este conteo: ")  # Nombre del conteo

    for denominacion in denominaciones:
        cantidad = int(input(f"Ingrese la cantidad de billetes de {denominacion:,}: ".replace(",", ".")))
        total_denominacion = cantidad * denominacion
        total_general += total_denominacion
        tabla.append([f"{denominacion:,}", cantidad, f"{total_denominacion:,}"])  # Agregar fila a la tabla

    # Mostrar la tabla
    print(f"\n--- Resultados del conteo: {nombre_conteo} ---")
    headers = ["Denominación", "Cantidad", "Total"]
    print(tabulate(tabla, headers=headers, tablefmt="pretty", numalign="right"))

    # Mostrar el total general
    print(f"\nEl monto total contado es: {total_general:,}".replace(",", "."))
    pyperclip.copy(str(total_general))  # Copiar el total al portapapeles
    print("(El monto total ha sido copiado al portapapeles)")

    # Guardar el conteo en un archivo
    guardar_conteo(nombre_conteo, tabla, total_general)

def guardar_conteo(nombre_conteo, tabla, total_general):
    """
    Guarda el conteo en un archivo de texto con la fecha y el nombre del conteo.
    """
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("registro_caja.txt", "a", encoding="utf-8") as archivo:
        archivo.write(f"\n--- Conteo: {nombre_conteo} ---\n")
        archivo.write(f"Fecha: {fecha_actual}\n")
        for fila in tabla:
            archivo.write(f"Denominación: {fila[0]}, Cantidad: {fila[1]}, Total: {fila[2]}\n")
        archivo.write(f"Monto total contado: {total_general:,}\n".replace(",", "."))
        archivo.write("-" * 30 + "\n")
    print("(El conteo ha sido guardado en 'registro_caja.txt')")

def menu():
    while True:
        try:
            # Mostrar el menú de opciones
            print("\n--- Menú de opciones ---")
            print("1. Venta de recargas (6% de utilidad)")
            print("2. Otra venta (ingresar porcentaje de utilidad)")
            print("3. Contar billetes")
            print("0. Salir")
            
            # Solicitar la opción al usuario
            opcion = input("Seleccione una opción: ")
            
            # Opción 1: Venta de recargas (6% de utilidad)
            if opcion == "1":
                venta = input("Ingrese el valor de la venta de recargas: ")
                venta = float(venta.replace(",", "."))  # Convertir coma a punto para cálculos
                costo_base = calcular_costo_base(venta, 6)
                resultado = f"{costo_base:,.2f}".replace(".", "|").replace(",", ".").replace("|", ",")  # Formato con comas
                print(f"\nEl valor antes de la utilidad (costo base) es: {resultado}")
                pyperclip.copy(resultado)  # Copiar al portapapeles
                print("(El resultado ha sido copiado al portapapeles)")
            
            # Opción 2: Otra venta (porcentaje personalizado)
            elif opcion == "2":
                venta = input("Ingrese el valor de la venta: ")
                venta = float(venta.replace(",", "."))  # Convertir coma a punto para cálculos
                utilidad_porcentaje = input("Ingrese el porcentaje de utilidad (%): ")
                utilidad_porcentaje = float(utilidad_porcentaje.replace(",", "."))  # Convertir coma a punto para cálculos
                costo_base = calcular_costo_base(venta, utilidad_porcentaje)
                resultado = f"{costo_base:,.2f}".replace(".", "|").replace(",", ".").replace("|", ",")  # Formato con comas
                print(f"\nEl valor antes de la utilidad (costo base) es: {resultado}")
                pyperclip.copy(resultado)  # Copiar al portapapeles
                print("(El resultado ha sido copiado al portapapeles)")
            
            # Opción 3: Contar billetes
            elif opcion == "3":
                contar_billetes()
            
            # Opción 0: Salir del programa
            elif opcion == "0":
                print("¡Gracias por usar el programa! ¡Hasta luego!")
                break
            
            # Opción no válida
            else:
                print("Opción no válida. Por favor, seleccione una opción del menú.")
        
        except ValueError:
            print("Error: Por favor, ingrese valores numéricos válidos.")

# Ejecutar el menú
menu()