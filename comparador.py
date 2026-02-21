import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import json
import os
import re  # Importamos regex para búsquedas más precisas

# --- Constantes y Configuración ---
RESTRICTIONS_FILE = "restricciones.json"
DEFAULT_RESTRICTIONS = {
    "pdcentro.txt": ["pacha"],
    "pdpr.txt": ["pacha"],
    "pdst.txt": [],
}

# --- Creación de archivos de ejemplo ---
try:
    with open("bodegac.txt", "x", encoding="utf-8") as f:
        f.write("    TORNILLO CABEZA PLANA 1/4 100\n")
        f.write("    TUERCA HEXAGONAL 1/4 250\n")
        f.write("    ARANDELA PLANA 1/4 500\n")
        f.write("    MARTILLO DE BOLA 16 OZ 15\n")
        f.write("    DESTORNILLADOR PHILLIPS #2 30\n")
        f.write("    CINTA METRICA 5M 25\n")
        f.write("    SILICONE IPHONE 15 ROJO 10\n")
        f.write("    SILICONE IPHONE 15 AZUL 10\n")
        f.write("    SILICONE IPHONE 15 PRO MAX NEGRO 5\n")
        f.write("    FORRO SPACE IPHONE 15 8\n")

    with open("local.txt", "x", encoding="utf-8") as f:
        f.write("    TORNILLO CABEZA PLANA 1/4 50\n")
        f.write("    TUERCA HEXAGONAL 1/4 120\n")
        f.write("    ARANDELA PLANA 1/4 300\n")
        f.write("    LLAVE AJUSTABLE 8 PULGADAS 10\n")
        f.write("    ALICATE DE PUNTA 6 PULGADAS 20\n")
        f.write("    SILICONE IPHONE 15 ROJO 5\n")

except FileExistsError:
    pass

# Variable global para almacenar el último término de búsqueda
last_search_term = ""
# Foco pegajoso: recordar qué ítem estaba seleccionado
sticky_item = ""
# Variable global para restricciones
current_restrictions = {}

# --- Paleta de Colores Matrix ---
BG_COLOR = "#0D0D0D"
FG_GREEN = "#00FF41"
FG_RED = "#FF3333"
ENTRY_BG = "#000000"
BTN_BG = "#FFFFFF"  # Fondo blanco para todos los botones
BTN_FG = "#FF3333"  # Letras rojas para todos los botones

# --- Funciones de Gestión de Restricciones ---


def load_restrictions():
    """Carga las restricciones desde el archivo JSON o usa las predeterminadas."""
    global current_restrictions
    if os.path.exists(RESTRICTIONS_FILE):
        try:
            with open(RESTRICTIONS_FILE, "r", encoding="utf-8") as f:
                current_restrictions = json.load(f)
        except json.JSONDecodeError:
            current_restrictions = DEFAULT_RESTRICTIONS.copy()
    else:
        current_restrictions = DEFAULT_RESTRICTIONS.copy()
        save_restrictions()  # Crear el archivo si no existe


def save_restrictions():
    """Guarda las restricciones actuales en el archivo JSON."""
    try:
        with open(RESTRICTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_restrictions, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron guardar las restricciones: {e}")


# Cargar restricciones al inicio
load_restrictions()

# --- Funciones Principales ---


def parse_file(filename):
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
        pass
    return data


def update_file(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
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
    global data_bodega, data_local
    data_bodega = parse_file("bodegac.txt")
    data_local = parse_file("local.txt")
    entry_search.delete(0, tk.END)
    entry_search.insert(0, last_search_term)
    search()


def on_item_select(event):
    global sticky_item
    widget = event.widget
    other_widget = tree_local if widget == tree_bodega else tree_bodega

    if other_widget.selection():
        other_widget.selection_remove(other_widget.selection())

    selected_items = widget.selection()
    if not selected_items:
        return

    selected_item = selected_items[0]
    item_values = widget.item(selected_item, "values")
    if not item_values or len(item_values) < 1:
        return

    description = item_values[0]
    sticky_item = description  # Guarda el ítem seleccionado como foco pegajoso
    entry_search.delete(0, tk.END)
    entry_search.insert(0, description)
    update_provider_quantities(description)


def update_provider_quantities(search_term):
    provider_files = {
        "pdcentro.txt": pd_centro_qty_var,
        "pdpr.txt": pd_pr_qty_var,
        "pdst.txt": pd_st_qty_var,
    }
    for filename, qty_var in provider_files.items():
        order_data = parse_file(filename)
        found_qty = 0
        for desc, qty in order_data:
            if desc.strip().lower() == search_term.lower():
                found_qty = qty
                break
        qty_var.set(str(found_qty))


def manual_search(event=None):
    global last_search_term
    last_search_term = entry_search.get().strip()
    search()


def check_qty(item_qty, op, val_str):
    """
    Verifica si la cantidad del ítem cumple con el filtro numérico.
    """
    if op == "Todos" or not val_str:
        return True
    try:
        val = int(val_str)
    except ValueError:
        return True  # Si no es un número válido, no filtra

    if op == "=":
        return item_qty == val
    if op == ">":
        return item_qty > val
    if op == "<":
        return item_qty < val
    if op == ">=":
        return item_qty >= val
    if op == "<=":
        return item_qty <= val
    return True


def check_match(description, search_term, mode):
    """
    Verifica si la descripción coincide con el término de búsqueda según el modo.
    """
    desc_lower = description.strip().lower()
    term_lower = search_term.lower()

    if mode == "phrase":  # Frase Exacta (Comportamiento original)
        return term_lower in desc_lower

    elif (
        mode == "keywords"
    ):  # Palabras Clave (Todas las palabras deben estar, cualquier orden)
        words = term_lower.split()
        if not words:
            return True
        return all(word in desc_lower for word in words)

    elif mode == "advanced":  # Avanzada (Soporta exclusión con -)
        parts = term_lower.split()
        if not parts:
            return True

        match = True
        for part in parts:
            if part.startswith("-") and len(part) > 1:
                exclude_word = part[1:]
                if exclude_word in desc_lower:
                    match = False
                    break
            else:
                if part not in desc_lower:
                    match = False
                    break
        return match

    return False


def search():
    global sticky_item
    search_term = entry_search.get().strip()
    filter_extra = entry_filter.get().strip().lower()  # Nuevo filtro adicional
    mode = search_mode_var.get()

    qty_op = qty_op_var.get()
    qty_val = entry_qty_val.get().strip()

    for item in tree_bodega.get_children():
        tree_bodega.delete(item)
    for item in tree_local.get_children():
        tree_local.delete(item)

    pd_centro_qty_var.set("-")
    pd_pr_qty_var.set("-")
    pd_st_qty_var.set("-")

    # Variables para estadísticas
    stats_bodega = {"items": 0, "units": 0, "zeros": 0}
    stats_local = {"items": 0, "units": 0, "zeros": 0}

    if not search_term:
        var_bodega_stats.set("Items: 0 | Unidades: 0 | Sin Stock: 0")
        var_local_stats.set("Items: 0 | Unidades: 0 | Sin Stock: 0")
        return

    # Buscar en bodega
    for description, quantity in data_bodega:
        # Verifica la búsqueda principal Y el filtro adicional
        if check_match(description, search_term, mode):
            if filter_extra and filter_extra not in description.lower():
                continue
            if not check_qty(quantity, qty_op, qty_val):
                continue

            item_id = tree_bodega.insert("", tk.END, values=(description, quantity))

            # Foco Pegajoso: re-seleccionar automáticamente si coincide
            if sticky_item and description == sticky_item:
                tree_bodega.selection_set(item_id)
                tree_bodega.see(item_id)

            stats_bodega["items"] += 1
            stats_bodega["units"] += quantity
            if quantity == 0:
                stats_bodega["zeros"] += 1

    # Buscar en local
    for description, quantity in data_local:
        if check_match(description, search_term, mode):
            if filter_extra and filter_extra not in description.lower():
                continue
            if not check_qty(quantity, qty_op, qty_val):
                continue

            item_id = tree_local.insert("", tk.END, values=(description, quantity))

            # Foco Pegajoso: re-seleccionar automáticamente si coincide
            if sticky_item and description == sticky_item:
                tree_local.selection_set(item_id)
                tree_local.see(item_id)

            stats_local["items"] += 1
            stats_local["units"] += quantity
            if quantity == 0:
                stats_local["zeros"] += 1

    # Actualizar etiquetas de resumen
    var_bodega_stats.set(
        f"Items: {stats_bodega['items']} | Unidades: {stats_bodega['units']} | Sin Stock: {stats_bodega['zeros']}"
    )
    var_local_stats.set(
        f"Items: {stats_local['items']} | Unidades: {stats_local['units']} | Sin Stock: {stats_local['zeros']}"
    )


def normalize_files():
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
            entry_search.delete(0, tk.END)
            entry_search.insert(0, last_search_term)
            search()
            # Sin popup de confirmación para más agilidad
    else:
        messagebox.showinfo("Normalización", "Los inventarios ya están sincronizados.")


def format_all_files_title_case():
    """Convierte las descripciones de todos los archivos a formato Título (Primera letra mayúscula)."""
    files_to_format = [
        "bodegac.txt",
        "local.txt",
        "pdcentro.txt",
        "pdpr.txt",
        "pdst.txt",
    ]

    confirm = messagebox.askyesno(
        "Confirmar Formato",
        "Esta acción convertirá las descripciones de TODOS los archivos activos\n"
        "(Bodega, Local y Proveedores) al formato 'Primera Letra Mayúscula'.\n"
        "Ejemplo: 'TORNILLO CABEZA' -> 'Tornillo Cabeza'\n\n"
        "¿Desea continuar?",
    )

    if not confirm:
        return

    processed_count = 0
    for filename in files_to_format:
        data = parse_file(filename)
        if not data:
            continue

        formatted_data = []
        for desc, qty in data:
            # .title() convierte "hola mundo" a "Hola Mundo"
            new_desc = desc.title()
            formatted_data.append((new_desc, qty))

        if update_file(filename, formatted_data):
            processed_count += 1

    # Refrescar datos y búsqueda
    global data_bodega, data_local
    data_bodega = parse_file("bodegac.txt")
    data_local = parse_file("local.txt")
    search()  # Re-ejecutar búsqueda para ver los cambios
    # Sin popup de confirmación para más agilidad


def sync_local_to_other():
    target_filename = filedialog.askopenfilename(
        title="Seleccionar archivo para sincronizar desde Local",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")),
    )
    if not target_filename:
        return
    try:
        local_data = parse_file("local.txt")
        if not local_data:
            messagebox.showwarning("Advertencia", "El archivo local.txt está vacío.")
            return
        local_items = {item[0] for item in local_data}
        target_data = parse_file(target_filename)
        target_dict = {item[0]: item[1] for item in target_data}

        items_in_target = set(target_dict.keys())
        items_to_add = local_items - items_in_target
        items_to_remove = items_in_target - local_items

        count_add = len(items_to_add)
        count_remove = len(items_to_remove)

        if count_add == 0 and count_remove == 0:
            messagebox.showinfo(
                "Sincronización",
                f"El archivo '{target_filename}' ya está sincronizado.",
            )
            return

        msg = f"Se actualizará '{target_filename}' basándose en 'local.txt'.\n\n"
        msg += f"• Agregar: {count_add} ítems.\n"
        msg += f"• ELIMINAR: {count_remove} ítems.\n\n"
        msg += "¿Desea continuar?"

        if not messagebox.askyesno("Confirmar Sincronización Estricta", msg):
            return

        final_data = []
        for item_desc in local_items:
            val = target_dict.get(item_desc, 0)
            final_data.append((item_desc, val))

        if update_file(target_filename, final_data):
            if target_filename.endswith("bodegac.txt") or target_filename.endswith(
                "local.txt"
            ):
                refresh_data()
            else:
                search()
    except Exception as e:
        messagebox.showerror("Error", f"Error al sincronizar: {e}")


def open_cost_manager():
    target_filename = filedialog.askopenfilename(
        title="Seleccionar archivo de Costos/Valores",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")),
    )
    if not target_filename:
        return
    cost_window = tk.Toplevel(root)
    cost_window.title(f"Gestor de Costos - {target_filename}")
    cost_window.geometry("600x600")
    cost_window.configure(bg=BG_COLOR)
    cost_data = parse_file(target_filename)

    frame_cost_search = tk.Frame(cost_window, bg=BG_COLOR, pady=10)
    frame_cost_search.pack(fill=tk.X, padx=10)
    entry_cost_search = tk.Entry(
        frame_cost_search,
        font=("Helvetica", 12),
        bg=ENTRY_BG,
        fg=FG_GREEN,
        insertbackground=FG_GREEN,
        relief="solid",
        borderwidth=1,
    )
    entry_cost_search.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

    tree_cost = ttk.Treeview(cost_window, columns=("Item", "Costo"), show="headings")
    tree_cost.heading("Item", text="Item")
    tree_cost.heading("Costo", text="Costo/Valor")
    tree_cost.column("Item", width=400)
    tree_cost.column("Costo", width=150, anchor=tk.CENTER)
    tree_cost.pack(expand=True, fill=tk.BOTH, padx=10)
    scrollbar_cost = ttk.Scrollbar(
        cost_window, orient="vertical", command=tree_cost.yview
    )
    tree_cost.configure(yscrollcommand=scrollbar_cost.set)
    scrollbar_cost.place(relx=1.0, rely=0.0, anchor="ne", height=600)

    frame_cost_edit = tk.Frame(cost_window, bg=BG_COLOR, pady=15, padx=10)
    frame_cost_edit.pack(fill=tk.X, side=tk.BOTTOM)
    lbl_selected_item = tk.Label(
        frame_cost_edit,
        text="Seleccione un ítem",
        font=("Helvetica", 10, "italic"),
        bg=BG_COLOR,
        fg=FG_GREEN,
    )
    lbl_selected_item.pack(anchor="w", pady=(0, 5))
    tk.Label(
        frame_cost_edit,
        text="Nuevo Costo:",
        font=("Helvetica", 11, "bold"),
        bg=BG_COLOR,
        fg=FG_RED,
    ).pack(side=tk.LEFT)
    entry_new_cost = tk.Entry(
        frame_cost_edit,
        font=("Helvetica", 11),
        width=15,
        bg=ENTRY_BG,
        fg=FG_GREEN,
        insertbackground=FG_GREEN,
    )
    entry_new_cost.pack(side=tk.LEFT, padx=10)

    def filter_costs(*args):
        search_text = entry_cost_search.get().strip().lower()
        tree_cost.delete(*tree_cost.get_children())
        for desc, val in cost_data:
            if search_text in desc.lower():
                tree_cost.insert("", tk.END, values=(desc, val))

    entry_cost_search.bind("<KeyRelease>", filter_costs)

    def on_cost_select(event):
        selected = tree_cost.selection()
        if selected:
            item_vals = tree_cost.item(selected[0], "values")
            lbl_selected_item.config(
                text=item_vals[0], fg=FG_GREEN, font=("Helvetica", 10, "bold")
            )
            entry_new_cost.delete(0, tk.END)
            entry_new_cost.insert(0, item_vals[1])
            entry_new_cost.focus_set()

    tree_cost.bind("<<TreeviewSelect>>", on_cost_select)

    def update_cost(event=None):
        selected = tree_cost.selection()
        if not selected:
            return
        new_val_str = entry_new_cost.get().strip()
        if not new_val_str.isdigit():
            messagebox.showerror(
                "Error", "El costo debe ser un número entero.", parent=cost_window
            )
            return
        new_val = int(new_val_str)
        item_desc = tree_cost.item(selected[0], "values")[0]
        for i, (desc, val) in enumerate(cost_data):
            if desc == item_desc:
                cost_data[i] = (desc, new_val)
                break
        if update_file(target_filename, cost_data):
            filter_costs()
            entry_new_cost.delete(0, tk.END)

    def update_batch_cost():
        new_val_str = entry_new_cost.get().strip()
        if not new_val_str.isdigit():
            messagebox.showerror(
                "Error", "El costo debe ser un número entero.", parent=cost_window
            )
            return
        new_val = int(new_val_str)
        items_to_update = tree_cost.get_children()
        if not items_to_update:
            messagebox.showinfo(
                "Info", "No hay ítems filtrados para actualizar.", parent=cost_window
            )
            return
        count = len(items_to_update)
        confirm = messagebox.askyesno(
            "Confirmar",
            f"¿Actualizar costo a {new_val} para {count} ítems?",
            parent=cost_window,
        )
        if not confirm:
            return
        descriptions_to_update = set()
        for item_id in items_to_update:
            item_vals = tree_cost.item(item_id, "values")
            descriptions_to_update.add(item_vals[0])
        for i, (desc, val) in enumerate(cost_data):
            if desc in descriptions_to_update:
                cost_data[i] = (desc, new_val)
        if update_file(target_filename, cost_data):
            filter_costs()
            entry_new_cost.delete(0, tk.END)

    btn_update_cost = tk.Button(
        frame_cost_edit,
        text="Actualizar",
        command=update_cost,
        bg=BTN_BG,
        fg=BTN_FG,
        font=("Helvetica", 10, "bold"),
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
    )
    btn_update_cost.pack(side=tk.LEFT)

    btn_update_batch = tk.Button(
        frame_cost_edit,
        text="Actualizar Lote",
        command=update_batch_cost,
        bg=BTN_BG,
        fg=BTN_FG,
        font=("Helvetica", 10, "bold"),
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
    )
    btn_update_batch.pack(side=tk.LEFT, padx=(10, 0))

    entry_new_cost.bind("<Return>", update_cost)
    filter_costs()


def open_restrictions_manager():
    res_window = tk.Toplevel(root)
    res_window.title("Gestor de Restricciones")
    res_window.geometry("500x400")
    res_window.configure(bg=BG_COLOR)

    frame_top = tk.Frame(res_window, bg=BG_COLOR, pady=10)
    frame_top.pack(fill=tk.X, padx=10)
    tk.Label(
        frame_top, text="Archivo:", font=("Helvetica", 11), bg=BG_COLOR, fg=FG_RED
    ).pack(side=tk.LEFT)

    known_files = ["pdcentro.txt", "pdpr.txt", "pdst.txt"]
    all_files = sorted(list(set(known_files) | set(current_restrictions.keys())))

    combo_files = ttk.Combobox(
        frame_top, values=all_files, state="readonly", font=("Helvetica", 10)
    )
    combo_files.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
    if all_files:
        combo_files.current(0)

    frame_list = tk.Frame(res_window, bg=BG_COLOR, padx=10)
    frame_list.pack(fill=tk.BOTH, expand=True)

    listbox_res = tk.Listbox(
        frame_list,
        font=("Helvetica", 11),
        bg=ENTRY_BG,
        fg=FG_GREEN,
        selectbackground=FG_GREEN,
        selectforeground=ENTRY_BG,
    )
    listbox_res.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar_res = ttk.Scrollbar(
        frame_list, orient="vertical", command=listbox_res.yview
    )
    listbox_res.configure(yscrollcommand=scrollbar_res.set)
    scrollbar_res.pack(side=tk.RIGHT, fill=tk.Y)

    def load_keywords_for_file(event=None):
        filename = combo_files.get()
        listbox_res.delete(0, tk.END)
        if filename in current_restrictions:
            for word in current_restrictions[filename]:
                listbox_res.insert(tk.END, word)

    combo_files.bind("<<ComboboxSelected>>", load_keywords_for_file)

    frame_actions = tk.Frame(res_window, bg=BG_COLOR, pady=10)
    frame_actions.pack(fill=tk.X, padx=10)

    entry_new_res = tk.Entry(
        frame_actions,
        font=("Helvetica", 11),
        width=20,
        bg=ENTRY_BG,
        fg=FG_GREEN,
        insertbackground=FG_GREEN,
    )
    entry_new_res.pack(side=tk.LEFT, padx=(0, 10))

    def add_restriction():
        filename = combo_files.get()
        new_word = entry_new_res.get().strip().lower()
        if not new_word:
            return

        if filename not in current_restrictions:
            current_restrictions[filename] = []

        if new_word not in current_restrictions[filename]:
            current_restrictions[filename].append(new_word)
            save_restrictions()
            load_keywords_for_file()
            entry_new_res.delete(0, tk.END)
        else:
            messagebox.showinfo(
                "Info", "Esa palabra ya está restringida.", parent=res_window
            )

    def remove_restriction():
        filename = combo_files.get()
        selection = listbox_res.curselection()
        if not selection:
            return
        word_to_remove = listbox_res.get(selection[0])

        if (
            filename in current_restrictions
            and word_to_remove in current_restrictions[filename]
        ):
            current_restrictions[filename].remove(word_to_remove)
            save_restrictions()
            load_keywords_for_file()

    btn_add_res = tk.Button(
        frame_actions,
        text="Agregar",
        command=add_restriction,
        bg=BTN_BG,
        fg=BTN_FG,
        font=("Helvetica", 10, "bold"),
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
    )
    btn_add_res.pack(side=tk.LEFT)

    btn_del_res = tk.Button(
        frame_actions,
        text="Eliminar",
        command=remove_restriction,
        bg=BTN_BG,
        fg=BTN_FG,
        font=("Helvetica", 10, "bold"),
        activebackground=BTN_BG,
        activeforeground=BTN_FG,
    )
    btn_del_res.pack(side=tk.RIGHT)

    load_keywords_for_file()


def transfer_quantity(direction):
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, primero busque y seleccione un artículo."
        )
        return
    try:
        qty_str = entry_transfer_qty.get().strip()
        transfer_qty = int(qty_str) if qty_str else 1  # 1 por defecto
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
        entry_transfer_qty.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def adjust_quantity(target, action):
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, primero busque y seleccione un artículo."
        )
        return
    try:
        qty_str = entry_adjust_qty.get().strip()
        adjust_qty = int(qty_str) if qty_str else 1  # 1 por defecto
        if adjust_qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada",
            "Por favor, ingrese una cantidad numérica válida y positiva.",
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
            "Error",
            f"El artículo seleccionado '{search_term}' no se encontró en {target}.",
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
        entry_adjust_qty.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def create_new_item(event=None):
    global sticky_item
    new_item_desc = entry_new_item.get().strip()
    if not new_item_desc:
        messagebox.showwarning(
            "Entrada Vacía", "El nombre del nuevo ítem no puede estar vacío."
        )
        return

    try:
        qty_str = entry_new_qty_bodega.get().strip()
        initial_qty = int(qty_str) if qty_str else 0  # 0 por defecto en bodega
        if initial_qty < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada",
            "Por favor, ingrese una cantidad inicial válida (0 o mayor).",
        )
        return

    all_descriptions = {item[0].lower() for item in data_bodega} | {
        item[0].lower() for item in data_local
    }
    if new_item_desc.lower() in all_descriptions:
        messagebox.showerror(
            "Ítem Existente", f"El ítem '{new_item_desc}' ya existe en el inventario."
        )
        return

    # Sin confirmación para mayor agilidad
    data_bodega.append((new_item_desc, initial_qty))
    data_local.append((new_item_desc, 0))

    if update_file("bodegac.txt", data_bodega) and update_file("local.txt", data_local):
        sticky_item = new_item_desc
        entry_new_item.delete(0, tk.END)
        entry_new_qty_bodega.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def add_to_purchase_order(filename):
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, busque y seleccione un artículo."
        )
        return

    if filename in current_restrictions:
        for keyword in current_restrictions[filename]:
            if keyword.lower() in search_term.lower():
                messagebox.showwarning(
                    "Restricción de Proveedor",
                    f"No se permite agregar ítems con la palabra '{keyword.upper()}' a {filename}.",
                )
                return

    try:
        qty_str = entry_pedido_qty.get().strip()
        pedido_qty = int(qty_str) if qty_str else 1  # 1 por defecto
        if pedido_qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Error de Entrada", "Por favor, ingrese una cantidad válida."
        )
        return

    order_data = parse_file(filename)
    item_found_in_order = False
    for i, (desc, qty) in enumerate(order_data):
        if desc.strip().lower() == search_term.lower():
            order_data[i] = (desc, qty + pedido_qty)
            item_found_in_order = True
            break
    if not item_found_in_order:
        order_data.append((search_term, pedido_qty))

    if update_file(filename, order_data):
        entry_pedido_qty.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def delete_item():
    global sticky_item
    search_term = entry_search.get().strip()
    if not search_term:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, primero busque y seleccione un artículo."
        )
        return
    confirm = messagebox.askyesno(
        "Confirmar Eliminación", f"¿Está seguro de que desea eliminar '{search_term}'?"
    )
    if confirm:
        global data_bodega, data_local
        item_exists = any(
            item[0].strip().lower() == search_term.lower() for item in data_bodega
        ) or any(item[0].strip().lower() == search_term.lower() for item in data_local)
        if not item_exists:
            messagebox.showinfo(
                "No Encontrado", f"El ítem '{search_term}' no se encontró."
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
            sticky_item = ""  # Limpiamos el foco pegajoso porque el ítem se eliminó
            entry_search.delete(0, tk.END)
            entry_search.insert(0, last_search_term)
            search()


def edit_item(event=None):
    global sticky_item
    global data_bodega, data_local
    old_desc = entry_search.get().strip()
    new_desc = entry_edit_item.get().strip()
    if not old_desc:
        messagebox.showwarning(
            "Acción Requerida", "Por favor, busque y seleccione un artículo."
        )
        return
    if not new_desc:
        messagebox.showwarning("Entrada Vacía", "El nuevo nombre no puede estar vacío.")
        return
    if old_desc.lower() == new_desc.lower():
        messagebox.showinfo("Sin Cambios", "El nuevo nombre es igual al actual.")
        return
    all_descriptions = {item[0].lower() for item in data_bodega} | {
        item[0].lower() for item in data_local
    }
    if new_desc.lower() in all_descriptions:
        messagebox.showerror(
            "Ítem Existente", "El ítem ya existe. Por favor elija otro nombre."
        )
        return

    # Sin confirmación para mayor agilidad
    item_found_and_changed = False
    for i, (desc, qty) in enumerate(data_bodega):
        if desc.strip().lower() == old_desc.lower():
            data_bodega[i] = (new_desc, qty)
            item_found_and_changed = True
            break

    for i, (desc, qty) in enumerate(data_local):
        if desc.strip().lower() == old_desc.lower():
            data_local[i] = (new_desc, qty)
            item_found_and_changed = True
            break

    if not item_found_and_changed:
        messagebox.showinfo("No Encontrado", "No se encontró el ítem.")
        return

    provider_files = ["pdcentro.txt", "pdpr.txt", "pdst.txt"]
    for filename in provider_files:
        order_data = parse_file(filename)
        if not order_data:
            continue
        item_found_in_order = False
        for i, (desc, qty) in enumerate(order_data):
            if desc.strip().lower() == old_desc.lower():
                order_data[i] = (new_desc, qty)
                item_found_in_order = True
                break
        if item_found_in_order:
            update_file(filename, order_data)

    if update_file("bodegac.txt", data_bodega) and update_file("local.txt", data_local):
        sticky_item = new_desc
        entry_edit_item.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


# --- Carga de Datos ---
data_bodega = parse_file("bodegac.txt")
data_local = parse_file("local.txt")

# --- Configuración de la Interfaz Gráfica ---
root = tk.Tk()
root.title("Comparador de Inventario")
root.geometry("900x1000")
root.configure(bg=BG_COLOR)

# Configuración de Estilos (Modo Matrix)
style = ttk.Style()
style.theme_use("default")
style.configure(
    "Treeview",
    background=ENTRY_BG,
    foreground=FG_GREEN,
    fieldbackground=ENTRY_BG,
    borderwidth=0,
)
style.map(
    "Treeview", background=[("selected", FG_GREEN)], foreground=[("selected", ENTRY_BG)]
)
style.configure(
    "Treeview.Heading",
    background=BTN_BG,
    foreground=FG_RED,
    relief="flat",
    font=("Helvetica", 10, "bold"),
)
style.map("Treeview.Heading", background=[("active", "#333333")])
style.configure(
    "TCombobox", fieldbackground=ENTRY_BG, background=BTN_BG, foreground=FG_GREEN
)

# Variables para mostrar cantidades de pedidos
pd_centro_qty_var = tk.StringVar(value="-")
pd_pr_qty_var = tk.StringVar(value="-")
pd_st_qty_var = tk.StringVar(value="-")
search_mode_var = tk.StringVar(value="phrase")  # phrase, keywords, advanced
qty_op_var = tk.StringVar(value="Todos")  # Filtro de cantidad

# Variables para resumen de estadísticas
var_bodega_stats = tk.StringVar(value="Items: 0 | Unidades: 0 | Sin Stock: 0")
var_local_stats = tk.StringVar(value="Items: 0 | Unidades: 0 | Sin Stock: 0")

main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# --- Frame de Básqueda y Opciones ---
frame_search_top = tk.Frame(main_frame, bg=BG_COLOR)
frame_search_top.pack(fill=tk.X, pady=(0, 10))

entry_search_container = tk.Frame(
    frame_search_top, relief="solid", borderwidth=1, bg=FG_GREEN
)
entry_search_container.pack(side=tk.LEFT, expand=True, fill=tk.X)
entry_search = tk.Entry(
    entry_search_container,
    font=("Helvetica", 12),
    width=40,
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_search.pack(expand=True, fill=tk.BOTH, ipady=4, padx=2, pady=1)
entry_search.bind("<Return>", manual_search)

button_search = tk.Button(
    frame_search_top,
    text="Buscar",
    command=manual_search,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_search.pack(side=tk.LEFT, padx=(10, 0), ipady=3)

button_refresh = tk.Button(
    frame_search_top,
    text="Refrescar",
    command=refresh_data,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_refresh.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

# Opciones de Búsqueda (Radiobuttons) y Filtro Adicional
frame_search_options = tk.Frame(main_frame, bg=BG_COLOR)
frame_search_options.pack(fill=tk.X, pady=(0, 15))
tk.Label(
    frame_search_options,
    text="Tipo de Búsqueda:",
    font=("Helvetica", 10, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT)

rb_phrase = tk.Radiobutton(
    frame_search_options,
    text="Frase Exacta",
    variable=search_mode_var,
    value="phrase",
    bg=BG_COLOR,
    fg=FG_GREEN,
    selectcolor=ENTRY_BG,
    activebackground=BG_COLOR,
    activeforeground=FG_GREEN,
)
rb_phrase.pack(side=tk.LEFT, padx=5)
rb_keywords = tk.Radiobutton(
    frame_search_options,
    text="Palabras Clave",
    variable=search_mode_var,
    value="keywords",
    bg=BG_COLOR,
    fg=FG_GREEN,
    selectcolor=ENTRY_BG,
    activebackground=BG_COLOR,
    activeforeground=FG_GREEN,
)
rb_keywords.pack(side=tk.LEFT, padx=5)
rb_advanced = tk.Radiobutton(
    frame_search_options,
    text="Avanzada (Excluir con -)",
    variable=search_mode_var,
    value="advanced",
    bg=BG_COLOR,
    fg=FG_GREEN,
    selectcolor=ENTRY_BG,
    activebackground=BG_COLOR,
    activeforeground=FG_GREEN,
)
rb_advanced.pack(side=tk.LEFT, padx=5)

# Nuevo Filtro Adicional
tk.Label(
    frame_search_options,
    text="Filtro (+):",
    font=("Helvetica", 10, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(20, 5))
entry_filter = tk.Entry(
    frame_search_options,
    font=("Helvetica", 10),
    width=15,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_filter.pack(side=tk.LEFT, padx=0)
entry_filter.bind("<Return>", manual_search)

# Nuevo Filtro de Cantidad
tk.Label(
    frame_search_options,
    text="Cant:",
    font=("Helvetica", 10, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(15, 2))
combo_qty_op = ttk.Combobox(
    frame_search_options,
    textvariable=qty_op_var,
    values=["Todos", "=", ">", "<", ">=", "<="],
    width=5,
    state="readonly",
    font=("Helvetica", 10),
)
combo_qty_op.pack(side=tk.LEFT)
combo_qty_op.bind("<<ComboboxSelected>>", manual_search)
entry_qty_val = tk.Entry(
    frame_search_options,
    font=("Helvetica", 10),
    width=5,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_qty_val.pack(side=tk.LEFT, padx=(2, 0))
entry_qty_val.bind("<Return>", manual_search)

# Botones de Herramientas
frame_tools = tk.Frame(main_frame, bg=BG_COLOR)
frame_tools.pack(fill=tk.X, pady=(0, 15))

button_normalize = tk.Button(
    frame_tools,
    text="Normalizar",
    command=normalize_files,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_normalize.pack(side=tk.LEFT, padx=(0, 5), ipady=3)

button_sync_local = tk.Button(
    frame_tools,
    text="Exportar Local",
    command=sync_local_to_other,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_sync_local.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

button_cost_manager = tk.Button(
    frame_tools,
    text="Gestor Costos",
    command=open_cost_manager,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_cost_manager.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

button_restrictions = tk.Button(
    frame_tools,
    text="Restricciones",
    command=open_restrictions_manager,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_restrictions.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

button_format = tk.Button(
    frame_tools,
    text="Formato Título",
    command=format_all_files_title_case,
    font=("Helvetica", 11, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=12,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
button_format.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

# --- Frame de Resultados ---
frame_results = tk.Frame(main_frame, bg=BG_COLOR)
frame_results.pack(expand=True, fill=tk.BOTH)
frame_results.columnconfigure(0, weight=1)
frame_results.columnconfigure(1, weight=1)
frame_results.rowconfigure(1, weight=1)
frame_results.rowconfigure(2, weight=0)

label_bodega = tk.Label(
    frame_results,
    text="Contenido Bodega",
    font=("Helvetica", 14, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
)
label_bodega.grid(row=0, column=0, pady=(0, 5))
tree_bodega = ttk.Treeview(frame_results, columns=("Item", "Cantidad"), show="headings")
tree_bodega.heading("Item", text="Item")
tree_bodega.heading("Cantidad", text="Cantidad")
tree_bodega.column("Item", width=250)
tree_bodega.column("Cantidad", width=80, anchor=tk.CENTER)
tree_bodega.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

lbl_stats_bodega = tk.Label(
    frame_results,
    textvariable=var_bodega_stats,
    font=("Helvetica", 9, "bold"),
    bg="#FFFFFF",
    fg="#000000",
    relief="sunken",
    padx=5,
    pady=2,
)
lbl_stats_bodega.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(2, 10))

label_local = tk.Label(
    frame_results,
    text="Contenido Local",
    font=("Helvetica", 14, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
)
label_local.grid(row=0, column=1, pady=(0, 5))
tree_local = ttk.Treeview(frame_results, columns=("Item", "Cantidad"), show="headings")
tree_local.heading("Item", text="Item")
tree_local.heading("Cantidad", text="Cantidad")
tree_local.column("Item", width=250)
tree_local.column("Cantidad", width=80, anchor=tk.CENTER)
tree_local.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

lbl_stats_local = tk.Label(
    frame_results,
    textvariable=var_local_stats,
    font=("Helvetica", 9, "bold"),
    bg="#FFFFFF",
    fg="#000000",
    relief="sunken",
    padx=5,
    pady=2,
)
lbl_stats_local.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(2, 10))

tree_bodega.bind("<<TreeviewSelect>>", on_item_select)
tree_local.bind("<<TreeviewSelect>>", on_item_select)

tree_bodega.tag_configure("not_found", foreground=FG_RED)
tree_local.tag_configure("not_found", foreground=FG_RED)

# --- Zonas de Herramientas Inferiores ---
# Frame de Zona de Peligro (Eliminar) - Conserva su borde rojo en los 4 lados
frame_danger = tk.Frame(
    main_frame,
    bg=BG_COLOR,
    pady=10,
    padx=10,
    relief="solid",
    borderwidth=1,
    highlightbackground=FG_RED,
    highlightthickness=1,
)
frame_danger.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_danger,
    text="Zona de Peligro:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(0, 10))
btn_delete_item = tk.Button(
    frame_danger,
    text="Eliminar Ítem Seleccionado",
    command=delete_item,
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_delete_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)

# Frame de Edición de Ítem (Línea verde debajo)
border_edit = tk.Frame(main_frame, bg=FG_GREEN, height=1)
border_edit.pack(fill=tk.X, side=tk.BOTTOM)
frame_edit = tk.Frame(main_frame, bg=BG_COLOR, pady=10, padx=10)
frame_edit.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_edit,
    text="Nuevo Nombre:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(0, 5))
entry_edit_item = tk.Entry(
    frame_edit,
    font=("Helvetica", 11),
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_edit_item.pack(side=tk.LEFT, ipady=2, padx=1, pady=1, expand=True, fill=tk.X)
entry_edit_item.bind("<Return>", edit_item)
btn_edit_item = tk.Button(
    frame_edit,
    text="Renombrar Ítem",
    command=edit_item,
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_edit_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)

# Frame de Creación de Ítem (Línea verde debajo)
border_create = tk.Frame(main_frame, bg=FG_GREEN, height=1)
border_create.pack(fill=tk.X, side=tk.BOTTOM)
frame_create = tk.Frame(main_frame, bg=BG_COLOR, pady=10, padx=10)
frame_create.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_create,
    text="Crear Nuevo Ítem:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(0, 5))
entry_new_item = tk.Entry(
    frame_create,
    font=("Helvetica", 11),
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_new_item.pack(side=tk.LEFT, ipady=2, padx=1, pady=1, expand=True, fill=tk.X)
entry_new_item.bind("<Return>", create_new_item)

tk.Label(
    frame_create,
    text="Cant. Bodega:",
    font=("Helvetica", 10, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(10, 5))
entry_new_qty_bodega = tk.Entry(
    frame_create,
    font=("Helvetica", 11),
    width=5,
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_new_qty_bodega.pack(side=tk.LEFT, ipady=2, padx=1, pady=1)
entry_new_qty_bodega.bind("<Return>", create_new_item)

btn_create_item = tk.Button(
    frame_create,
    text="Crear Ítem",
    command=create_new_item,
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_create_item.pack(side=tk.LEFT, padx=(10, 0), ipady=2)


# Frame de Ajuste (Línea verde debajo)
border_adjust = tk.Frame(main_frame, bg=FG_GREEN, height=1)
border_adjust.pack(fill=tk.X, side=tk.BOTTOM)
frame_adjust = tk.Frame(main_frame, bg=BG_COLOR, pady=10, padx=10)
frame_adjust.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_adjust,
    text="Ajuste de Inventario:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(0, 5))
entry_adjust_qty = tk.Entry(
    frame_adjust,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_adjust_qty.pack(side=tk.LEFT, ipady=2, padx=1, pady=1)

btn_add_bodega = tk.Button(
    frame_adjust,
    text="+ Bodega",
    command=lambda: adjust_quantity("bodega", "add"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_add_bodega.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_remove_bodega = tk.Button(
    frame_adjust,
    text="- Bodega",
    command=lambda: adjust_quantity("bodega", "remove"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_remove_bodega.pack(side=tk.LEFT, padx=(0, 5), ipady=2)
btn_add_local = tk.Button(
    frame_adjust,
    text="+ Local",
    command=lambda: adjust_quantity("local", "add"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_add_local.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_remove_local = tk.Button(
    frame_adjust,
    text="- Local",
    command=lambda: adjust_quantity("local", "remove"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_remove_local.pack(side=tk.LEFT, ipady=2)

# Frame de Traslado (Línea verde debajo)
border_transfer = tk.Frame(main_frame, bg=FG_GREEN, height=1)
border_transfer.pack(fill=tk.X, side=tk.BOTTOM)
frame_transfer = tk.Frame(main_frame, bg=BG_COLOR, pady=10, padx=10)
frame_transfer.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
tk.Label(
    frame_transfer,
    text="Cantidad a Trasladar:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(side=tk.LEFT, padx=(0, 5))
entry_transfer_qty = tk.Entry(
    frame_transfer,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_transfer_qty.pack(side=tk.LEFT, ipady=2, padx=1, pady=1)
btn_to_local = tk.Button(
    frame_transfer,
    text="Bodega -> Local",
    command=lambda: transfer_quantity("to_local"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_to_local.pack(side=tk.LEFT, padx=(10, 5), ipady=2)
btn_to_bodega = tk.Button(
    frame_transfer,
    text="Local -> Bodega",
    command=lambda: transfer_quantity("to_bodega"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_to_bodega.pack(side=tk.LEFT, ipady=2)

# Frame de Pedidos a Proveedores (Línea verde debajo)
border_pedido = tk.Frame(main_frame, bg=FG_GREEN, height=1)
border_pedido.pack(fill=tk.X, side=tk.BOTTOM)
frame_pedido = tk.Frame(main_frame, bg=BG_COLOR, pady=10, padx=10)
frame_pedido.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

pedido_input_frame = tk.Frame(frame_pedido, bg=BG_COLOR)
pedido_input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20), anchor="n")
tk.Label(
    pedido_input_frame,
    text="Agregar a Pedido:",
    font=("Helvetica", 11, "bold"),
    bg=BG_COLOR,
    fg=FG_RED,
).pack(anchor="w")
entry_pedido_qty = tk.Entry(
    pedido_input_frame,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg=ENTRY_BG,
    fg=FG_GREEN,
    insertbackground=FG_GREEN,
)
entry_pedido_qty.pack(anchor="w", ipady=2, padx=1, pady=1)

providers_frame = tk.Frame(frame_pedido, bg=BG_COLOR)
providers_frame.pack(side=tk.LEFT)

# PD Centro
pd_centro_frame = tk.Frame(providers_frame, bg=BG_COLOR)
pd_centro_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_centro = tk.Button(
    pd_centro_frame,
    text="PD Centro",
    command=lambda: add_to_purchase_order("pdcentro.txt"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_pd_centro.pack(pady=(0, 2))
tk.Label(
    pd_centro_frame, text="En Pedido:", font=("Helvetica", 8), bg=BG_COLOR, fg=FG_GREEN
).pack()
lbl_pd_centro_qty = tk.Label(
    pd_centro_frame,
    textvariable=pd_centro_qty_var,
    font=("Helvetica", 10, "bold"),
    bg=ENTRY_BG,
    fg=FG_GREEN,
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_centro_qty.pack()

# PD PR
pd_pr_frame = tk.Frame(providers_frame, bg=BG_COLOR)
pd_pr_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_pr = tk.Button(
    pd_pr_frame,
    text="PD PR",
    command=lambda: add_to_purchase_order("pdpr.txt"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_pd_pr.pack(pady=(0, 2))
tk.Label(
    pd_pr_frame, text="En Pedido:", font=("Helvetica", 8), bg=BG_COLOR, fg=FG_GREEN
).pack()
lbl_pd_pr_qty = tk.Label(
    pd_pr_frame,
    textvariable=pd_pr_qty_var,
    font=("Helvetica", 10, "bold"),
    bg=ENTRY_BG,
    fg=FG_GREEN,
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_pr_qty.pack()

# PD ST
pd_st_frame = tk.Frame(providers_frame, bg=BG_COLOR)
pd_st_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_st = tk.Button(
    pd_st_frame,
    text="PD ST",
    command=lambda: add_to_purchase_order("pdst.txt"),
    font=("Helvetica", 10, "bold"),
    bg=BTN_BG,
    fg=BTN_FG,
    relief="flat",
    padx=10,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
)
btn_pd_st.pack(pady=(0, 2))
tk.Label(
    pd_st_frame, text="En Pedido:", font=("Helvetica", 8), bg=BG_COLOR, fg=FG_GREEN
).pack()
lbl_pd_st_qty = tk.Label(
    pd_st_frame,
    textvariable=pd_st_qty_var,
    font=("Helvetica", 10, "bold"),
    bg=ENTRY_BG,
    fg=FG_GREEN,
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_st_qty.pack()

root.mainloop()
