import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# --- Creación de archivos de ejemplo ---
# Se crean los archivos bodegac.txt y local.txt con datos de ejemplo
# si no existen. Esto es para que el programa se pueda ejecutar y probar
# inmediatamente sin tener que crear los archivos manualmente.
try:
    with open("bodegac.txt", "x") as f:
        f.write("    TORNILLO CABEZA PLANA 1/4 100\n")
        f.write("    TUERCA HEXAGONAL 1/4 250\n")
        f.write("    ARANDELA PLANA 1/4 500\n")
        f.write("    MARTILLO DE BOLA 16 OZ 15\n")
        f.write("    DESTORNILLADOR PHILLIPS #2 30\n")
        f.write("    CINTA METRICA 5M 25\n")

    with open("local.txt", "x") as f:
        f.write("    TORNILLO CABEZA PLANA 1/4 50\n")
        f.write("    TUERCA HEXAGONAL 1/4 120\n")
        f.write("    ARANDELA PLANA 1/4 300\n")
        f.write("    LLAVE AJUSTABLE 8 PULGADAS 10\n")
        f.write("    ALICATE DE PUNTA 6 PULGADAS 20\n")

except FileExistsError:
    # Si los archivos ya existen, no se hace nada.
    pass

# --- Funciones Principales ---


def parse_file(filename):
    """
    Lee un archivo de texto y extrae la descripción y la cantidad de cada línea.
    Ignora las líneas que no siguen el formato esperado.
    """
    data = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("    ") and len(line.strip()) > 0:
                    line_content = line.strip()
                    parts = line_content.rsplit(" ", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        description = parts[0]
                        quantity = int(parts[1])
                        data.append((description, quantity))
    except FileNotFoundError:
        messagebox.showerror("Error", f"El archivo {filename} no fue encontrado.")
    return data


def update_file(filename, data):
    """Sobrescribe un archivo con los nuevos datos de inventario."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            # Ordena los datos alfabéticamente antes de escribir
            sorted_data = sorted(data, key=lambda item: item[0])
            for description, quantity in sorted_data:
                f.write(f"    {description} {quantity}\n")
        return True
    except Exception as e:
        messagebox.showerror(
            "Error de Archivo",
            f"No se pudo escribir en el archivo {filename}.\nError: {e}",
        )
        return False


def refresh_data():
    """
    Vuelve a cargar los datos de los archivos .txt y refresca la búsqueda actual
    sin borrar el texto del buscador.
    """
    global data_bodega, data_local
    data_bodega = parse_file("bodegac.txt")
    data_local = parse_file("local.txt")
    listbox_autocomplete.place_forget()
    search()
    messagebox.showinfo("Refrescar", "Los datos han sido actualizados.")


def update_autocomplete(event):
    """Actualiza la lista de autocompletado a medida que el usuario escribe."""
    search_term = entry_search.get().lower()
    listbox_autocomplete.delete(0, tk.END)
    if not search_term:
        listbox_autocomplete.place_forget()
        return

    all_descriptions = [item[0] for item in data_bodega] + [
        item[0] for item in data_local
    ]
    unique_descriptions = sorted(list(set(all_descriptions)))

    matches = [desc for desc in unique_descriptions if search_term in desc.lower()]

    for match in matches:
        listbox_autocomplete.insert(tk.END, match)

    if matches:
        entry_x = entry_search_container.winfo_rootx() - root.winfo_rootx()
        entry_y = entry_search_container.winfo_rooty() - root.winfo_rooty()
        entry_height = entry_search_container.winfo_height()
        entry_width = entry_search_container.winfo_width()
        listbox_autocomplete.place(
            x=entry_x, y=entry_y + entry_height + 1, width=entry_width
        )
    else:
        listbox_autocomplete.place_forget()


def select_from_listbox(event):
    """Pone la selección del autocompletado en el cuadro de texto y busca."""
    if listbox_autocomplete.curselection():
        selected_value = listbox_autocomplete.get(listbox_autocomplete.curselection())
        entry_search.delete(0, tk.END)
        entry_search.insert(0, selected_value)
        listbox_autocomplete.place_forget()
        search()


def search():
    """Busca el item en ambos archivos y muestra los resultados."""
    search_term = entry_search.get().strip()
    listbox_autocomplete.place_forget()

    for item in tree_bodega.get_children():
        tree_bodega.delete(item)
    for item in tree_local.get_children():
        tree_local.delete(item)

    if not search_term:
        return

    found_in_bodega = False
    for description, quantity in data_bodega:
        if description.strip().lower() == search_term.lower():
            tree_bodega.insert("", tk.END, values=(description, quantity))
            found_in_bodega = True
            break

    found_in_local = False
    for description, quantity in data_local:
        if description.strip().lower() == search_term.lower():
            tree_local.insert("", tk.END, values=(description, quantity))
            found_in_local = True
            break

    if found_in_bodega and not found_in_local:
        tree_local.insert("", tk.END, values=(search_term, "No encontrado"))
    elif found_in_local and not found_in_bodega:
        tree_bodega.insert("", tk.END, values=(search_term, "No encontrado"))


def transfer_quantity(direction):
    """Mueve una cantidad de un item entre bodega y local."""
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida",
            "Por favor, primero busque un artículo para poder trasladarlo.",
        )
        return
    try:
        transfer_qty = int(entry_transfer_qty.get())
        if transfer_qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada",
            "Por favor, ingrese una cantidad numérica válida y positiva.",
        )
        return

    bodega_item_index, local_item_index = -1, -1
    bodega_qty, local_qty = 0, 0
    for i, (desc, qty) in enumerate(data_bodega):
        if desc.strip().lower() == search_term.lower():
            bodega_item_index, bodega_qty = i, qty
            break
    for i, (desc, qty) in enumerate(data_local):
        if desc.strip().lower() == search_term.lower():
            local_item_index, local_qty = i, qty
            break

    if direction == "to_local":
        if bodega_item_index == -1:
            messagebox.showerror(
                "Error", f"El artículo '{search_term}' no existe en la bodega."
            )
            return
        if bodega_qty < transfer_qty:
            messagebox.showerror(
                "Stock Insuficiente",
                f"No hay suficiente stock en bodega. Disponible: {bodega_qty}",
            )
            return
        data_bodega[bodega_item_index] = (search_term, bodega_qty - transfer_qty)
        if local_item_index != -1:
            data_local[local_item_index] = (search_term, local_qty + transfer_qty)
        else:
            data_local.append((search_term, transfer_qty))
    elif direction == "to_bodega":
        if local_item_index == -1:
            messagebox.showerror(
                "Error", f"El artículo '{search_term}' no existe en el local."
            )
            return
        if local_qty < transfer_qty:
            messagebox.showerror(
                "Stock Insuficiente",
                f"No hay suficiente stock en el local. Disponible: {local_qty}",
            )
            return
        data_local[local_item_index] = (search_term, local_qty - transfer_qty)
        if bodega_item_index != -1:
            data_bodega[bodega_item_index] = (search_term, bodega_qty + transfer_qty)
        else:
            data_bodega.append((search_term, transfer_qty))

    if update_file("bodegac.txt", data_bodega) and update_file("local.txt", data_local):
        messagebox.showinfo(
            "Éxito", f"Se trasladaron {transfer_qty} unidades de '{search_term}'."
        )
        search()
        entry_transfer_qty.delete(0, tk.END)


def adjust_quantity(target, action):
    """NUEVA FUNCIÓN: Agrega o quita unidades de un item en el archivo de origen."""
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida",
            "Por favor, primero busque un artículo para poder ajustarlo.",
        )
        return
    try:
        adjust_qty = int(entry_adjust_qty.get())
        if adjust_qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada",
            "Por favor, ingrese una cantidad numérica válida y positiva para el ajuste.",
        )
        return

    data_list = data_bodega if target == "bodega" else data_local
    filename = "bodegac.txt" if target == "bodega" else "local.txt"
    item_index, current_qty = -1, 0

    for i, (desc, qty) in enumerate(data_list):
        if desc.strip().lower() == search_term.lower():
            item_index, current_qty = i, qty
            break

    if item_index == -1:
        messagebox.showerror(
            "Error", f"El artículo '{search_term}' no se encontró en {target}."
        )
        return

    if action == "add":
        new_qty = current_qty + adjust_qty
        data_list[item_index] = (search_term, new_qty)
        action_text = "agregaron"
    elif action == "remove":
        if current_qty < adjust_qty:
            messagebox.showerror(
                "Stock Insuficiente",
                f"No se pueden quitar {adjust_qty} unidades. Disponible en {target}: {current_qty}",
            )
            return
        new_qty = current_qty - adjust_qty
        data_list[item_index] = (search_term, new_qty)
        action_text = "quitaron"

    if update_file(filename, data_list):
        messagebox.showinfo(
            "Éxito",
            f"Se {action_text} {adjust_qty} unidades de '{search_term}' en {target}.",
        )
        search()
        entry_adjust_qty.delete(0, tk.END)


# --- Carga de Datos ---
data_bodega = parse_file("bodegac.txt")
data_local = parse_file("local.txt")

# --- Configuración de la Interfaz Gráfica ---
root = tk.Tk()
root.title("Comparador de Inventario")
root.geometry("800x700")
root.configure(bg="#f0f0f0")

main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# --- Frame de Búsqueda ---
frame_search = tk.Frame(main_frame, bg="#f0f0f0")
frame_search.pack(fill=tk.X, pady=(0, 20))
entry_search_container = tk.Frame(
    frame_search, relief="solid", borderwidth=1, bg="white"
)
entry_search_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
entry_search = tk.Entry(
    entry_search_container,
    font=("Helvetica", 12),
    width=40,
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_search.pack(expand=True, fill=tk.BOTH, ipady=4, padx=2, pady=1)
entry_search.bind("<KeyRelease>", update_autocomplete)
button_search = tk.Button(
    frame_search,
    text="Buscar",
    command=search,
    font=("Helvetica", 11, "bold"),
    bg="#cce0ff",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="#b3d1ff",
    activeforeground="black",
    borderwidth=0,
)
button_search.pack(side=tk.LEFT, padx=(10, 0), ipady=3)
button_refresh = tk.Button(
    frame_search,
    text="Refrescar",
    command=refresh_data,
    font=("Helvetica", 11, "bold"),
    bg="#ccebdc",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="#b3e0c7",
    activeforeground="black",
    borderwidth=0,
)
button_refresh.pack(side=tk.LEFT, padx=(5, 0), ipady=3)
listbox_autocomplete = tk.Listbox(
    root, font=("Helvetica", 11), relief="solid", borderwidth=1
)
listbox_autocomplete.bind("<<ListboxSelect>>", select_from_listbox)

# --- Frame de Resultados ---
frame_results = tk.Frame(main_frame, bg="#f0f0f0")
frame_results.pack(expand=True, fill=tk.BOTH)
frame_results.columnconfigure(0, weight=1)
frame_results.columnconfigure(1, weight=1)
frame_results.rowconfigure(1, weight=1)
label_bodega = tk.Label(
    frame_results, text="Contenido Bodega", font=("Helvetica", 14, "bold"), bg="#f0f0f0"
)
label_bodega.grid(row=0, column=0, pady=(0, 10))
tree_bodega = ttk.Treeview(frame_results, columns=("Item", "Cantidad"), show="headings")
tree_bodega.heading("Item", text="Item")
tree_bodega.heading("Cantidad", text="Cantidad")
tree_bodega.column("Item", width=250)
tree_bodega.column("Cantidad", width=80, anchor=tk.CENTER)
tree_bodega.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
label_local = tk.Label(
    frame_results, text="Contenido Local", font=("Helvetica", 14, "bold"), bg="#f0f0f0"
)
label_local.grid(row=0, column=1, pady=(0, 10))
tree_local = ttk.Treeview(frame_results, columns=("Item", "Cantidad"), show="headings")
tree_local.heading("Item", text="Item")
tree_local.heading("Cantidad", text="Cantidad")
tree_local.column("Item", width=250)
tree_local.column("Cantidad", width=80, anchor=tk.CENTER)
tree_local.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

# --- Frame de Ajuste (movido antes de Traslado para mejor flujo visual) ---
frame_adjust = tk.Frame(main_frame, bg="#f8f9fa", pady=10, padx=10)
frame_adjust.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_adjust,
    text="Ajuste de Inventario:",
    font=("Helvetica", 11, "bold"),
    bg=frame_adjust["bg"],
).pack(side=tk.LEFT, padx=(0, 5))
entry_adjust_container = tk.Frame(
    frame_adjust, relief="solid", borderwidth=1, bg="white"
)
entry_adjust_container.pack(side=tk.LEFT)
entry_adjust_qty = tk.Entry(
    entry_adjust_container,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_adjust_qty.pack(ipady=2, padx=1, pady=1)

# MODIFICADO: Colores de botones de ajuste para mejor legibilidad
btn_add_bodega = tk.Button(
    frame_adjust,
    text="+ Bodega",
    command=lambda: adjust_quantity("bodega", "add"),
    font=("Helvetica", 10, "bold"),
    bg="#a3e9a4",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#8fcf90",
)
btn_add_bodega.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_remove_bodega = tk.Button(
    frame_adjust,
    text="- Bodega",
    command=lambda: adjust_quantity("bodega", "remove"),
    font=("Helvetica", 10, "bold"),
    bg="#ffb3b3",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#ff9999",
)
btn_remove_bodega.pack(side=tk.LEFT, padx=(0, 5), ipady=2)
btn_add_local = tk.Button(
    frame_adjust,
    text="+ Local",
    command=lambda: adjust_quantity("local", "add"),
    font=("Helvetica", 10, "bold"),
    bg="#a3e9a4",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#8fcf90",
)
btn_add_local.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_remove_local = tk.Button(
    frame_adjust,
    text="- Local",
    command=lambda: adjust_quantity("local", "remove"),
    font=("Helvetica", 10, "bold"),
    bg="#ffb3b3",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#ff9999",
)
btn_remove_local.pack(side=tk.LEFT, ipady=2)

# --- Frame de Traslado ---
frame_transfer = tk.Frame(main_frame, bg="#e9ecef", pady=10, padx=10)
frame_transfer.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_transfer,
    text="Cantidad a Trasladar:",
    font=("Helvetica", 11, "bold"),
    bg=frame_transfer["bg"],
).pack(side=tk.LEFT, padx=(0, 5))
entry_qty_container = tk.Frame(
    frame_transfer, relief="solid", borderwidth=1, bg="white"
)
entry_qty_container.pack(side=tk.LEFT)
entry_transfer_qty = tk.Entry(
    entry_qty_container,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_transfer_qty.pack(ipady=2, padx=1, pady=1)
btn_to_local = tk.Button(
    frame_transfer,
    text="Bodega -> Local",
    command=lambda: transfer_quantity("to_local"),
    font=("Helvetica", 10, "bold"),
    bg="#ffc107",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#e0a800",
)
btn_to_local.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_to_bodega = tk.Button(
    frame_transfer,
    text="Local -> Bodega",
    command=lambda: transfer_quantity("to_bodega"),
    font=("Helvetica", 10, "bold"),
    bg="#ffc107",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#e0a800",
)
btn_to_bodega.pack(side=tk.LEFT, ipady=2)

root.mainloop()
