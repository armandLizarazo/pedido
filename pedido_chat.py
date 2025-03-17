import random
import json

def cargar_palabras_clave(nombre_archivo):
    """Carga las palabras clave desde un archivo JSON."""
    try:
        with open(nombre_archivo, 'r') as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return {}

def generar_mensaje_chat(articulos, palabras_marca, palabras_item):
    """
    Genera un mensaje para chat con saludos y cierres aleatorios, y lista de artículos con guiones.

    Args:
        articulos (list): Lista de artículos a incluir en el mensaje.
        palabras_marca (dict): Diccionario de marcas y listas de palabras clave.
        palabras_item (list): Lista de palabras clave de item a las que se agregará "del" después.

    Returns:
        str: Mensaje generado.
    """

    saludos = [
        "Don Julián, ¡buen día! ¿Cómo vamos?",
        "Buenos días, Don Julián.",
        "¡Buen día! ¿Activos?",
        "¿Cómo vamos?",
    ]

    cierres = [
        "¿Paso de una?",
        "¿A qué hora le caigo?",
        "Estoy cerca, ¿paso? ¿Dentro de cuándo...?",
        "Quedo atento.",
    ]

    saludo_aleatorio = random.choice(saludos)
    cierre_aleatorio = random.choice(cierres)

    mensaje = saludo_aleatorio + "\n"

    # Generar lista de artículos con guiones y palabras clave
    for articulo in articulos:
        for marca, palabras_clave in palabras_marca.items():
            for palabra_clave in palabras_clave:
                if palabra_clave.lower() in articulo.lower():
                    posicion = articulo.lower().find(palabra_clave.lower())
                    articulo = articulo[:posicion] + marca + " " + articulo[posicion:]
        for palabra_clave in palabras_item: # Bucle corregido
            if palabra_clave.lower() in articulo.lower():
                posicion = articulo.lower().find(palabra_clave.lower())
                articulo = articulo[:posicion + len(palabra_clave)] + " del " + articulo[posicion + len(palabra_clave):]
        mensaje += "- " + articulo + "\n"

    mensaje += "\n" + cierre_aleatorio

    return mensaje

# Pedir al usuario que ingrese los artículos
articulos = []
while True:
    articulo = input("Ingresa un artículo (o presiona Enter para terminar): ")
    if not articulo:
        break
    articulos.append(articulo)

# Cargar palabras clave desde archivos JSON
palabras_marca = cargar_palabras_clave('claves_marca.json')
palabras_item = cargar_palabras_clave('claves_item.json')

# Generar y mostrar el mensaje
mensaje_generado = generar_mensaje_chat(articulos, palabras_marca, palabras_item)

# Capitalizar la primera letra de cada palabra en el mensaje, manteniendo los saltos de línea
mensaje_capitalizado = ""
for linea in mensaje_generado.splitlines():
    palabras_capitalizadas = [palabra.capitalize() for palabra in linea.split()]
    mensaje_capitalizado += " ".join(palabras_capitalizadas) + "\n"

print("\n" + mensaje_capitalizado.strip())