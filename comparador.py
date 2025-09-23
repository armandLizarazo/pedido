import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# --- Creación de archivos de ejemplo ---
# Se crean los archivos bodegac.txt y local.txt con datos de ejemplo
# si no existen. Esto es para que el programa se pueda ejecutar y probar
# inmediatamente sin tener que crear los archivos manualmente.
try:
    with open("bodegac.txt", "x", encoding="utf-8") as f:
        f.write("    TORNILLO CABEZA PLANA 1/4 100\n")
        f.write("    TUERCA HEXAGONAL 1/4 250\n")
        f.write("    ARANDELA PLANA 1/4 500\n")
        f.write("    MARTILLO DE BOLA 16 OZ 15\n")
        f.write("    DESTORNILLADOR PHILLIPS #2 30\n")
        f.write("    CINTA METRICA 5M 25\n")

    with open("local.txt", "x", encoding="utf-8") as f:
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
    Vuelve a cargar los datos de los archivos .txt y refresca la básqueda actual
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
        tree_local.insert(
            "", tk.END, values=(search_term, "No encontrado"), tags=("not_found",)
        )
    elif found_in_local and not found_in_bodega:
        tree_bodega.insert(
            "", tk.END, values=(search_term, "No encontrado"), tags=("not_found",)
        )


def normalize_files():
    """
    Compara ambos archivos y agrega los items faltantes en cada uno con cantidad 0.
    """
    global data_bodega, data_local

    bodega_descs = {item[0] for item in data_bodega}
    local_descs = {item[0] for item in data_local}

    missing_in_local = bodega_descs - local_descs
    missing_in_bodega = local_descs - bodega_descs

    items_added = len(missing_in_local) + len(missing_in_bodega)

    if items_added > 0:
        confirm = messagebox.askyesno(
            "Confirmar Normalización",
            f"Se encontraron {items_added} items para sincronizar.\n"
            "¿Desea agregar los items faltantes a cada archivo con cantidad 0?",
        )
        if confirm:
            for desc in missing_in_local:
                data_local.append((desc, 0))
            for desc in missing_in_bodega:
                data_bodega.append((desc, 0))

            update_file("bodegac.txt", data_bodega)
            update_file("local.txt", data_local)

            data_bodega = parse_file("bodegac.txt")
            data_local = parse_file("local.txt")
            search()

            messagebox.showinfo(
                "Éxito", "Los archivos han sido normalizados correctamente."
            )
    else:
        messagebox.showinfo(
            "Normalización",
            "Los inventarios ya están sincronizados. No se requieren cambios.",
        )


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
    """Agrega o quita unidades de un item en el archivo de origen."""
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


def create_new_item():
    """Crea un nuevo item en ambos archivos con cantidad inicial de 0."""
    new_item_desc = entry_new_item.get().strip()

    if not new_item_desc:
        messagebox.showwarning(
            "Entrada Vacía", "El nombre del nuevo ítem no puede estar vacío."
        )
        return

    # Comprobar si el item ya existe (insensible a mayúsculas/minúsculas)
    all_descriptions = {item[0].lower() for item in data_bodega} | {
        item[0].lower() for item in data_local
    }
    if new_item_desc.lower() in all_descriptions:
        messagebox.showerror(
            "Ítem Existente", f"El ítem '{new_item_desc}' ya existe en el inventario."
        )
        return

    confirm = messagebox.askyesno(
        "Confirmar Creación",
        f"¿Desea crear el nuevo ítem '{new_item_desc}' en ambos inventarios con cantidad 0?",
    )

    if confirm:
        # Usamos el nombre tal como lo escribió el usuario para mantener el formato
        data_bodega.append((new_item_desc, 0))
        data_local.append((new_item_desc, 0))

        if update_file("bodegac.txt", data_bodega) and update_file(
            "local.txt", data_local
        ):
            messagebox.showinfo(
                "Éxito", f"El ítem '{new_item_desc}' ha sido creado exitosamente."
            )
            entry_new_item.delete(0, tk.END)
            # Opcional: buscar automáticamente el nuevo ítem
            entry_search.delete(0, tk.END)
            entry_search.insert(0, new_item_desc)
            search()


def add_to_purchase_order(filename):
    """Agrega un item y cantidad a un archivo de pedido de proveedor."""
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida",
            "Por favor, busque un artículo para agregarlo a un pedido.",
        )
        return

    try:
        pedido_qty = int(entry_pedido_qty.get())
        if pedido_qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada", "Por favor, ingrese una cantidad válida para el pedido."
        )
        return

    order_data = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("    ") and len(line.strip()) > 0:
                    parts = line.strip().rsplit(" ", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        order_data.append((parts[0], int(parts[1])))
    except FileNotFoundError:
        pass  # El archivo no existe, se creará uno nuevo.

    item_found_in_order = False
    for i, (desc, qty) in enumerate(order_data):
        if desc.strip().lower() == search_term.lower():
            order_data[i] = (desc, qty + pedido_qty)
            item_found_in_order = True
            break

    if not item_found_in_order:
        order_data.append((search_term, pedido_qty))

    if update_file(filename, order_data):
        messagebox.showinfo(
            "Éxito",
            f"Se agregaron {pedido_qty} unidades de '{search_term}' a {filename}.",
        )
        entry_pedido_qty.delete(0, tk.END)


def delete_item():
    """Elimina un item de ambos archivos."""
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida",
            "Por favor, primero busque un artículo para poder eliminarlo.",
        )
        return

    confirm = messagebox.askyesno(
        "Confirmar Eliminación",
        f"¿Está seguro de que desea eliminar el ítem '{search_term}' de ambos inventarios?\nEsta acción no se puede deshacer.",
    )

    if confirm:
        global data_bodega, data_local

        # Verificamos si el item existe antes de intentar eliminarlo
        item_exists = any(
            item[0].strip().lower() == search_term.lower() for item in data_bodega
        ) or any(item[0].strip().lower() == search_term.lower() for item in data_local)

        if not item_exists:
            messagebox.showinfo(
                "No Encontrado",
                f"El ítem '{search_term}' no se encontró en los inventarios.",
            )
            return

        data_bodega = [
            item
            for item in data_bodega
            if item[0].strip().lower() != search_term.lower()
        ]
        data_local = [
            item
            for item in data_local
            if item[0].strip().lower() != search_term.lower()
        ]

        if update_file("bodegac.txt", data_bodega) and update_file(
            "local.txt", data_local
        ):
            messagebox.showinfo(
                "Éxito", f"El ítem '{search_term}' ha sido eliminado exitosamente."
            )
            entry_search.delete(0, tk.END)
            search()


def edit_item():
    """Edita la descripción de un item en ambos archivos."""
    global data_bodega, data_local
    old_desc = entry_search.get().strip()
    new_desc = entry_edit_item.get().strip()

    if not old_desc:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, busque un artículo para editar."
        )
        return

    if not new_desc:
        messagebox.showwarning(
            "Entrada Vacía", "El nuevo nombre del ítem no puede estar vacío."
        )
        return

    if old_desc.lower() == new_desc.lower():
        messagebox.showinfo("Sin Cambios", "El nuevo nombre es igual al actual.")
        return

    # Comprobamos que el nuevo nombre no exista ya
    all_descriptions = {item[0].lower() for item in data_bodega} | {
        item[0].lower() for item in data_local
    }
    if new_desc.lower() in all_descriptions:
        messagebox.showerror(
            "Ítem Existente",
            f"El ítem '{new_desc}' ya existe. Por favor elija otro nombre.",
        )
        return

    confirm = messagebox.askyesno(
        "Confirmar Edición",
        f"¿Desea renombrar el ítem '{old_desc}' a '{new_desc}' en ambos inventarios?",
    )

    if confirm:
        item_found_and_changed = False

        # Actualizamos la lista de bodega
        for i, (desc, qty) in enumerate(data_bodega):
            if desc.strip().lower() == old_desc.lower():
                data_bodega[i] = (new_desc, qty)
                item_found_and_changed = True
                break

        # Actualizamos la lista de local
        for i, (desc, qty) in enumerate(data_local):
            if desc.strip().lower() == old_desc.lower():
                data_local[i] = (new_desc, qty)
                item_found_and_changed = True
                break

        if not item_found_and_changed:
            messagebox.showinfo(
                "No Encontrado", f"No se encontró el ítem '{old_desc}'."
            )
            return

        if update_file("bodegac.txt", data_bodega) and update_file(
            "local.txt", data_local
        ):
            messagebox.showinfo("Éxito", f"El ítem ha sido renombrado a '{new_desc}'.")
            entry_search.delete(0, tk.END)
            entry_search.insert(0, new_desc)
            entry_edit_item.delete(0, tk.END)
            search()


# --- Carga de Datos ---
data_bodega = parse_file("bodegac.txt")
data_local = parse_file("local.txt")

# --- Configuración de la Interfaz Gráfica ---
root = tk.Tk()
root.title("Comparador de Inventario")
root.geometry("850x950")  # Aumentado el alto para las nuevas secciones
root.configure(bg="#f0f0f0")

main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# --- Frame de Básqueda ---
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
button_normalize = tk.Button(
    frame_search,
    text="Normalizar",
    command=normalize_files,
    font=("Helvetica", 11, "bold"),
    bg="#ffc107",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="#e0a800",
)
button_normalize.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

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

# --- CONFIGURACIÓN DE TAGS PARA COLORES ---
tree_bodega.tag_configure("not_found", foreground="red")
tree_local.tag_configure("not_found", foreground="red")

# --- Frame de Zona de Peligro (Eliminar) ---
frame_danger = tk.Frame(
    main_frame, bg="#f8d7da", pady=10, padx=10, relief="solid", borderwidth=1
)
frame_danger.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_danger,
    text="Zona de Peligro:",
    font=("Helvetica", 11, "bold"),
    bg=frame_danger["bg"],
    fg="#721c24",
).pack(side=tk.LEFT, padx=(0, 10))
btn_delete_item = tk.Button(
    frame_danger,
    text="Eliminar Ítem Buscado",
    command=delete_item,
    font=("Helvetica", 10, "bold"),
    bg="#dc3545",
    fg="white",
    relief="flat",
    padx=10,
    activebackground="#c82333",
)
btn_delete_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)

# --- Frame de Edición de Ítem ---
frame_edit = tk.Frame(
    main_frame, bg="#fff3cd", pady=10, padx=10, relief="solid", borderwidth=1
)
frame_edit.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_edit,
    text="Nuevo Nombre:",
    font=("Helvetica", 11, "bold"),
    bg=frame_edit["bg"],
    fg="#856404",
).pack(side=tk.LEFT, padx=(0, 5))
entry_edit_container = tk.Frame(frame_edit, relief="solid", borderwidth=1, bg="white")
entry_edit_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
entry_edit_item = tk.Entry(
    entry_edit_container,
    font=("Helvetica", 11),
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_edit_item.pack(ipady=2, padx=1, pady=1, expand=True, fill=tk.X)
btn_edit_item = tk.Button(
    frame_edit,
    text="Renombrar Ítem",
    command=edit_item,
    font=("Helvetica", 10, "bold"),
    bg="#ffc107",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#e0a800",
)
btn_edit_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)

# --- Frame de Creación de Ítem ---
frame_create = tk.Frame(main_frame, bg="#d4edda", pady=10, padx=10)
frame_create.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_create,
    text="Crear Nuevo Ítem:",
    font=("Helvetica", 11, "bold"),
    bg=frame_create["bg"],
).pack(side=tk.LEFT, padx=(0, 5))
entry_create_container = tk.Frame(
    frame_create, relief="solid", borderwidth=1, bg="white"
)
entry_create_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
entry_new_item = tk.Entry(
    entry_create_container,
    font=("Helvetica", 11),
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_new_item.pack(ipady=2, padx=1, pady=1, expand=True, fill=tk.X)
btn_create_item = tk.Button(
    frame_create,
    text="Crear Ítem",
    command=create_new_item,
    font=("Helvetica", 10, "bold"),
    bg="#198754",
    fg="white",
    relief="flat",
    padx=10,
    activebackground="#157347",
)
btn_create_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)


# --- Frame de Ajuste ---
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

# --- Frame de Pedidos a Proveedores ---
frame_pedido = tk.Frame(main_frame, bg="#d1ecf1", pady=10, padx=10)
frame_pedido.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

tk.Label(
    frame_pedido,
    text="Agregar a Pedido:",
    font=("Helvetica", 11, "bold"),
    bg=frame_pedido["bg"],
    fg="#0c5460",
).pack(side=tk.LEFT, padx=(0, 5))

entry_pedido_container = tk.Frame(
    frame_pedido, relief="solid", borderwidth=1, bg="white"
)
entry_pedido_container.pack(side=tk.LEFT)
entry_pedido_qty = tk.Entry(
    entry_pedido_container,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_pedido_qty.pack(ipady=2, padx=1, pady=1)

btn_pd_centro = tk.Button(
    frame_pedido,
    text="PD Centro",
    command=lambda: add_to_purchase_order("pdcentro.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#a3e9a4",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#8fcf90",
)
btn_pd_centro.pack(side=tk.LEFT, padx=(10, 5), ipady=2)

btn_pd_pr = tk.Button(
    frame_pedido,
    text="PD PR",
    command=lambda: add_to_purchase_order("pdpr.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#a8d8ff",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#8fbcff",
)
btn_pd_pr.pack(side=tk.LEFT, padx=(0, 5), ipady=2)

btn_pd_st = tk.Button(
    frame_pedido,
    text="PD ST",
    command=lambda: add_to_purchase_order("pdst.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#d3d3d3",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="#b8b8b8",
)
btn_pd_st.pack(side=tk.LEFT, ipady=2)


root.mainloop()
