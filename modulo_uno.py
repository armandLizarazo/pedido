def cargar_archivo(nombre_archivo):
    try:
        with open(nombre_archivo, 'r') as archivo:
            lineas = archivo.readlines()
        return [linea.strip() for linea in lineas]
    except FileNotFoundError:
        print(f"El archivo '{nombre_archivo}' no fue encontrado.")
        return None

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

def main():
    nombre_archivo = input("Introduce el nombre del archivo: ")
    elementos = cargar_archivo(nombre_archivo)
    
    if elementos is None:
        return
    
    while True:
        print("\nOpciones:")
        print("1. Ver todos los elementos")
        print("2. Filtrar por palabra")
        print("3. Consultar elementos con un número indicado")
        print("4. Salir")
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
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")

if __name__ == "__main__":
    main()