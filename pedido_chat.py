import random
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- CONFIGURACIÓN Y LÓGICA CORE ---

# Los diccionarios de marcas e ítems se definen DENTRO del script para evitar errores de JSON no cargado.
# **IMPORTANTE:** Se asume que estos diccionarios serán alimentados manualmente aquí si no se usan JSON.

# Si decides no usar archivos JSON para marcas/ítems, debes definirlos aquí:
# Diccionario de marcas: {"Marca_a_agregar": ["Palabra_clave1", "Palabra_clave2"]}
PALABRAS_MARCA = {
    "Motorola": [
        "Moto",
        "G60",
        "G20",
        "Motorola",
    ],  # Se agregó "Motorola" a la lista para capturar casos donde ya esté presente
    "Samsung": [
        "S10",
        "A50",
        "Galaxy",
        "Samsung",
    ],  # Se agregó "Samsung" a la lista para capturar casos donde ya esté presente
    "Display": ["Pantalla", "Vizor", "Vidrio"],
    "Tecno": ["Spark", "Camon", "Pop", "Pova"],
    "Tecno Spark": ["Go"],
}

# Lista de ítems: ["Palabra_clave_item1", "Palabra_clave_item2"]
PALABRAS_ITEM = [
    "Pacha",
    "Bateria",
    "Bandeja Sim",
    "Flex de Power",
    "Logica",
    "Tapa",
    "Pin",
    "Camara",
]

# --- Funciones de Carga de Artículos (Simplificadas) ---


def parse_text_file(filepath):
    """
    Lee un archivo de texto con el formato: [4 espacios] Descripción [espacio] Cantidad (entero).
    Retorna una lista de artículos formateados como 'Descripción Cantidad'.
    """
    parsed_articles = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            line = line.rstrip()  # Eliminar espacio en blanco/nueva línea al final

            # Requisito: La línea debe empezar con 4 espacios
            if not line.startswith("    "):
                continue

            content = line[4:].strip()  # Quitar los 4 espacios y espacios restantes

            # Requisito: El último elemento es la cantidad
            parts = content.rsplit(" ", 1)

            if len(parts) < 2:
                # No hay espacio, no se puede separar la descripción de la cantidad.
                continue

            description = parts[0].strip()
            quantity_str = parts[1].strip()

            try:
                quantity = int(quantity_str)
                if quantity > 0:
                    # Nuevo formato deseado: "Descripción Cantidad"
                    parsed_articles.append(f"{description} {quantity}")
            except ValueError:
                # El último elemento no es un entero (la cantidad)
                continue

    except Exception as e:
        messagebox.showerror(
            "Error de Lectura",
            f"Ocurrió un error al leer el archivo: {os.path.basename(filepath)}\nDetalle: {e}",
        )
        return []

    return parsed_articles


def generar_mensaje_chat(articulos, palabras_marca, palabras_item):
    """
    Genera un mensaje para chat con saludos, cierres aleatorios y lista de artículos.
    """
    saludos = [
        "Don Julián, ¡buen día! ¿Cómo vamos?",
        "Buenos días, Don Julián.",
        "¡Buen día! ¿Activos?",
        "¿Cómo vamos?",
        "Activos?",
    ]

    cierres = [
        "¿Paso de una?",
        "¿A qué hora le caigo?",
        "¿Tiempos de espera?",
        "Estoy cerca, ¿paso? ¿Dentro de cuánto...?",
        "Quedo atento.",
    ]

    saludo_aleatorio = random.choice(saludos)
    cierre_aleatorio = random.choice(cierres)

    mensaje_estructurado = saludo_aleatorio + "\n"

    # Procesamiento de Artículos
    for articulo in articulos:
        articulo_modificado = articulo
        articulo_lower = articulo_modificado.lower()

        # A. Aplicar Palabras Clave de MARCA (Anteponer la Marca y eliminar duplicados)
        for marca, palabras_clave in palabras_marca.items():

            # Formato de búsqueda de duplicado (ej: "Motorola Motorola ")
            duplicado = f"{marca} {marca}"

            # Primero, intenta anteponer la marca si encuentra la clave
            for palabra_clave in palabras_clave:
                if palabra_clave.lower() in articulo_lower:
                    posicion = articulo_lower.find(palabra_clave.lower())
                    articulo_modificado = (
                        articulo_modificado[:posicion]
                        + marca
                        + " "
                        + articulo_modificado[posicion:]
                    )

                    # CORRECCIÓN DE DUPLICADOS: Verificar si la marca quedó repetida
                    # Esto ocurre si la marca ya era la primera palabra del artículo antes del cambio.
                    if articulo_modificado.startswith(f"{marca} {marca}"):
                        # Si está duplicada al inicio, la quitamos
                        articulo_modificado = articulo_modificado[len(marca) + 1 :]

                    # Verificar duplicados en el resto del string (más robusto)
                    if duplicado in articulo_modificado:
                        articulo_modificado = articulo_modificado.replace(
                            duplicado, marca, 1
                        )  # Solo reemplazamos la primera ocurrencia

                    break  # Detener al encontrar la primera coincidencia de marca

        # Actualizamos la versión en minúsculas para el siguiente chequeo (clave ITEM)
        articulo_lower = articulo_modificado.lower()

        # B. Aplicar Palabras Clave de ITEM (Agregar " del " después de la clave)
        for palabra_clave in palabras_item:
            if palabra_clave.lower() in articulo_lower:
                posicion = articulo_lower.find(palabra_clave.lower())
                articulo_modificado = (
                    articulo_modificado[: posicion + len(palabra_clave)]
                    + " del "
                    + articulo_modificado[posicion + len(palabra_clave) :]
                )

        # Formato deseado: Item y Cantidad en línea separada, sin guión
        mensaje_estructurado += articulo_modificado + "\n"

    # 3. Cierre
    mensaje_estructurado += "\n" + cierre_aleatorio

    return mensaje_estructurado


def capitalizar_mensaje(mensaje):
    """
    Capitaliza la primera letra de cada palabra en el mensaje, manteniendo los saltos de línea.
    """
    mensaje_capitalizado = ""
    for linea in mensaje.splitlines():
        if not linea.strip() and not linea:
            mensaje_capitalizado += "\n"
            continue

        palabras_capitalizadas = [palabra.capitalize() for palabra in linea.split()]
        mensaje_capitalizado += " ".join(palabras_capitalizadas) + "\n"

    return mensaje_capitalizado.strip()


# --- Interfaz Gráfica (Tkinter) ---


class ChatMessageGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("Generador de Mensajes de Pedido")
        master.configure(padx=15, pady=15)

        # Usar las variables definidas en el script (ya no se cargan de JSON)
        self.palabras_marca = PALABRAS_MARCA
        self.palabras_item = PALABRAS_ITEM
        self.inventario_items = []  # Se elimina la selección de inventario JSON

        # Variables de estado
        self.loaded_file_articles = []  # Variable para artículos del TXT

        self.create_widgets()

    def create_widgets(self):
        # 1. Marco de Carga de Archivo TXT (Ahora es la opción principal)
        self.frame_file_load = ttk.LabelFrame(
            self.master, text="1. Cargar Artículos desde Archivo TXT", padding="10"
        )
        self.frame_file_load.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.file_path_var = tk.StringVar(value="Ningún archivo cargado")
        ttk.Label(
            self.frame_file_load,
            textvariable=self.file_path_var,
            wraplength=350,
            foreground="gray",
        ).pack(side="left", padx=5, fill="x", expand=True)

        self.load_file_button = ttk.Button(
            self.frame_file_load,
            text="Seleccionar TXT",
            command=self.load_articles_from_file,
        )
        self.load_file_button.pack(side="right")

        # 2. Marco de Ingreso Manual
        self.frame_manual = ttk.LabelFrame(
            self.master, text="2. Ingreso Manual (ej: item_a 5, item_b 1)", padding="10"
        )
        self.frame_manual.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.manual_entry = tk.Text(self.frame_manual, height=5, width=50)
        self.manual_entry.pack(fill="x", expand=True)
        ttk.Label(
            self.frame_manual,
            text="NOTA: Agregue la cantidad al final de la descripción (ej: Tapa roja 2)",
        ).pack(pady=5)

        # 3. Botón Generar
        self.generate_button = ttk.Button(
            self.master,
            text="3. GENERAR MENSAJE",
            command=self.generar_y_mostrar_mensaje,
            style="Accent.TButton",
        )
        self.generate_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # 4. Marco de Salida
        self.frame_output = ttk.LabelFrame(
            self.master, text="4. Mensaje Generado (Listo para Chat)", padding="10"
        )
        self.frame_output.grid(
            row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew"
        )

        self.output_text = tk.Text(
            self.frame_output, height=20, width=60, state="disabled"
        )
        self.output_text.pack(fill="both", expand=True)

        # 5. Botón Copiar
        self.copy_button = ttk.Button(
            self.frame_output,
            text="COPIAR MENSAJE",
            command=self.copiar_mensaje,
            state="disabled",
        )
        self.copy_button.pack(pady=5, fill="x")

        # Configuración de pesos para redimensionamiento
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

    def load_articles_from_file(self):
        """Abre un diálogo para seleccionar un archivo TXT y carga los artículos."""
        filepath = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if filepath:
            articles = parse_text_file(filepath)
            self.loaded_file_articles = articles
            self.file_path_var.set(os.path.basename(filepath))
            messagebox.showinfo(
                "Carga Exitosa",
                f"{len(articles)} artículos válidos cargados desde el archivo.",
            )

            # Limpiar entradas manuales para evitar acumulación accidental
            self.manual_entry.delete("1.0", tk.END)
        else:
            self.loaded_file_articles = []
            self.file_path_var.set("Ningún archivo cargado")

    def obtener_articulos_seleccionados(self):
        """Compila la lista final de artículos (manual + archivo cargado)."""
        articulos_final = []

        # 1. Artículos de Ingreso Manual (Se espera formato "Descripción Cantidad")
        manual_text = self.manual_entry.get("1.0", tk.END).strip()
        if manual_text:
            manual_lines = [
                line.strip() for line in manual_text.split("\n") if line.strip()
            ]
            articulos_final.extend(manual_lines)

        # 2. Artículos del Archivo Cargado (Ya vienen en formato "Descripción Cantidad")
        articulos_final.extend(self.loaded_file_articles)

        return articulos_final

    def generar_y_mostrar_mensaje(self):
        """Función principal para generar el mensaje y mostrarlo en la GUI."""

        articulos = self.obtener_articulos_seleccionados()

        if not articulos:
            messagebox.showwarning(
                "Advertencia", "Debes ingresar o cargar al menos un artículo."
            )
            self.output_text.config(state="normal")
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", "¡No se seleccionaron artículos!")
            self.output_text.config(state="disabled")
            self.copy_button.config(state="disabled")
            return

        # Generar mensaje usando la lógica existente
        mensaje_generado = generar_mensaje_chat(
            articulos, self.palabras_marca, self.palabras_item
        )
        mensaje_final = capitalizar_mensaje(mensaje_generado)

        # Mostrar el resultado
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", mensaje_final)
        self.output_text.config(state="disabled")
        self.copy_button.config(state="normal")

    def copiar_mensaje(self):
        """Copia el texto generado al portapapeles."""
        text_to_copy = self.output_text.get("1.0", tk.END).strip()
        if text_to_copy:
            # Usar métodos de Tkinter para copiar
            self.master.clipboard_clear()
            self.master.clipboard_append(text_to_copy)
            messagebox.showinfo(
                "Copiado", "¡El mensaje ha sido copiado al portapapeles!"
            )


if __name__ == "__main__":
    # Inicialización de la aplicación
    root = tk.Tk()

    # Configuración de estilo moderno (opcional, pero mejora la apariencia)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Accent.TButton",
        font=("Arial", 10, "bold"),
        foreground="black",
        background="#4CAF50",
    )

    app = ChatMessageGeneratorApp(root)
    root.mainloop()
