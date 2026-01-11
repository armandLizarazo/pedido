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
# Variable global para restricciones
current_restrictions = {}

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
    messagebox.showinfo("Refrescar", "Los datos han sido actualizados.")


def on_item_select(event):
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


def manual_search():
    global last_search_term
    last_search_term = entry_search.get().strip()
    search()


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
        # Ejemplo: "iphone 15 -pro" -> Busca "iphone" Y "15" PERO NO "pro"
        parts = term_lower.split()
        if not parts:
            return True

        match = True
        for part in parts:
            if part.startswith("-") and len(part) > 1:
                # Exclusión: Si la palabra (sin el -) está en la descripción, NO es match
                exclude_word = part[1:]
                if exclude_word in desc_lower:
                    match = False
                    break
            else:
                # Inclusión: La palabra debe estar
                if part not in desc_lower:
                    match = False
                    break
        return match

    return False


def search():
    search_term = entry_search.get().strip()
    mode = search_mode_var.get()

    for item in tree_bodega.get_children():
        tree_bodega.delete(item)
    for item in tree_local.get_children():
        tree_local.delete(item)

    pd_centro_qty_var.set("-")
    pd_pr_qty_var.set("-")
    pd_st_qty_var.set("-")

    if not search_term:
        return

    # Buscar y mostrar coincidencias en bodega
    for description, quantity in data_bodega:
        if check_match(description, search_term, mode):
            tree_bodega.insert("", tk.END, values=(description, quantity))

    # Buscar y mostrar coincidencias en local
    for description, quantity in data_local:
        if check_match(description, search_term, mode):
            tree_local.insert("", tk.END, values=(description, quantity))


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
            messagebox.showinfo(
                "Éxito", "Los archivos han sido normalizados correctamente."
            )
    else:
        messagebox.showinfo("Normalización", "Los inventarios ya están sincronizados.")


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
            messagebox.showinfo("Éxito", "Sincronización completada.")
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
    cost_window.configure(bg="#f0f0f0")
    cost_data = parse_file(target_filename)

    frame_cost_search = tk.Frame(cost_window, bg="#f0f0f0", pady=10)
    frame_cost_search.pack(fill=tk.X, padx=10)
    entry_cost_search = tk.Entry(
        frame_cost_search, font=("Helvetica", 12), relief="solid", borderwidth=1
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

    frame_cost_edit = tk.Frame(cost_window, bg="#e2e6ea", pady=15, padx=10)
    frame_cost_edit.pack(fill=tk.X, side=tk.BOTTOM)
    lbl_selected_item = tk.Label(
        frame_cost_edit,
        text="Seleccione un ítem",
        font=("Helvetica", 10, "italic"),
        bg="#e2e6ea",
        fg="#555",
    )
    lbl_selected_item.pack(anchor="w", pady=(0, 5))
    tk.Label(
        frame_cost_edit,
        text="Nuevo Costo:",
        font=("Helvetica", 11, "bold"),
        bg="#e2e6ea",
    ).pack(side=tk.LEFT)
    entry_new_cost = tk.Entry(frame_cost_edit, font=("Helvetica", 11), width=15)
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
                text=item_vals[0], fg="black", font=("Helvetica", 10, "bold")
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
            messagebox.showinfo(
                "Éxito", f"Se actualizaron {count} ítems.", parent=cost_window
            )

    btn_update_cost = tk.Button(
        frame_cost_edit,
        text="Actualizar",
        command=update_cost,
        bg="#a3e9a4",
        fg="black",
        font=("Helvetica", 10, "bold"),
        activebackground="black",
        activeforeground="white",
    )
    btn_update_cost.pack(side=tk.LEFT)

    btn_update_batch = tk.Button(
        frame_cost_edit,
        text="Actualizar Lote",
        command=update_batch_cost,
        bg="#a6e0eb",
        fg="black",
        font=("Helvetica", 10, "bold"),
        activebackground="black",
        activeforeground="white",
    )
    btn_update_batch.pack(side=tk.LEFT, padx=(10, 0))

    entry_new_cost.bind("<Return>", update_cost)
    filter_costs()


def open_restrictions_manager():
    res_window = tk.Toplevel(root)
    res_window.title("Gestor de Restricciones")
    res_window.geometry("500x400")
    res_window.configure(bg="#f0f0f0")

    frame_top = tk.Frame(res_window, bg="#f0f0f0", pady=10)
    frame_top.pack(fill=tk.X, padx=10)
    tk.Label(frame_top, text="Archivo:", font=("Helvetica", 11), bg="#f0f0f0").pack(
        side=tk.LEFT
    )

    known_files = ["pdcentro.txt", "pdpr.txt", "pdst.txt"]
    all_files = sorted(list(set(known_files) | set(current_restrictions.keys())))

    combo_files = ttk.Combobox(
        frame_top, values=all_files, state="readonly", font=("Helvetica", 10)
    )
    combo_files.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
    if all_files:
        combo_files.current(0)

    frame_list = tk.Frame(res_window, bg="#f0f0f0", padx=10)
    frame_list.pack(fill=tk.BOTH, expand=True)

    listbox_res = tk.Listbox(frame_list, font=("Helvetica", 11))
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

    frame_actions = tk.Frame(res_window, bg="#f0f0f0", pady=10)
    frame_actions.pack(fill=tk.X, padx=10)

    entry_new_res = tk.Entry(frame_actions, font=("Helvetica", 11), width=20)
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
        bg="#a3e9a4",
        fg="black",
        font=("Helvetica", 10, "bold"),
        activebackground="black",
        activeforeground="white",
    )
    btn_add_res.pack(side=tk.LEFT)

    btn_del_res = tk.Button(
        frame_actions,
        text="Eliminar",
        command=remove_restriction,
        bg="#ffb3b3",
        fg="black",
        font=("Helvetica", 10, "bold"),
        activebackground="black",
        activeforeground="white",
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
        messagebox.showinfo("Éxito", f"Se trasladaron {transfer_qty} unidades.")
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
        adjust_qty = int(entry_adjust_qty.get())
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
        messagebox.showinfo("Éxito", f"Se {action_text} {adjust_qty} unidades.")
        entry_adjust_qty.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def create_new_item():
    new_item_desc = entry_new_item.get().strip()
    if not new_item_desc:
        messagebox.showwarning(
            "Entrada Vacía", "El nombre del nuevo ítem no puede estar vacío."
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
    confirm = messagebox.askyesno(
        "Confirmar Creación",
        f"¿Desea crear el nuevo ítem '{new_item_desc}' con cantidad 0?",
    )
    if confirm:
        data_bodega.append((new_item_desc, 0))
        data_local.append((new_item_desc, 0))
        if update_file("bodegac.txt", data_bodega) and update_file(
            "local.txt", data_local
        ):
            messagebox.showinfo("Éxito", "El ítem ha sido creado exitosamente.")
            entry_new_item.delete(0, tk.END)
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
        pedido_qty = int(entry_pedido_qty.get())
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
        messagebox.showinfo(
            "Éxito", f"Se agregaron {pedido_qty} unidades a {filename}."
        )
        entry_pedido_qty.delete(0, tk.END)
        entry_search.delete(0, tk.END)
        entry_search.insert(0, last_search_term)
        search()


def delete_item():
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
            messagebox.showinfo("Éxito", "El ítem ha sido eliminado exitosamente.")
            entry_search.delete(0, tk.END)
            entry_search.insert(0, last_search_term)
            search()


def edit_item():
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
    confirm = messagebox.askyesno(
        "Confirmar Edición", f"¿Desea renombrar '{old_desc}' a '{new_desc}'?"
    )
    if confirm:
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

        if update_file("bodegac.txt", data_bodega) and update_file(
            "local.txt", data_local
        ):
            messagebox.showinfo("Éxito", "El ítem ha sido renombrado.")
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
root.geometry("900x1000")  # Ajustado alto
root.configure(bg="#f0f0f0")

# Variables para mostrar cantidades de pedidos
pd_centro_qty_var = tk.StringVar(value="-")
pd_pr_qty_var = tk.StringVar(value="-")
pd_st_qty_var = tk.StringVar(value="-")
search_mode_var = tk.StringVar(value="phrase")  # phrase, keywords, advanced

main_frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# --- Frame de Básqueda y Opciones ---
frame_search_top = tk.Frame(main_frame, bg="#f0f0f0")
frame_search_top.pack(fill=tk.X, pady=(0, 10))

entry_search_container = tk.Frame(
    frame_search_top, relief="solid", borderwidth=1, bg="white"
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

button_search = tk.Button(
    frame_search_top,
    text="Buscar",
    command=manual_search,
    font=("Helvetica", 11, "bold"),
    bg="#cce0ff",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
    borderwidth=0,
)
button_search.pack(side=tk.LEFT, padx=(10, 0), ipady=3)

button_refresh = tk.Button(
    frame_search_top,
    text="Refrescar",
    command=refresh_data,
    font=("Helvetica", 11, "bold"),
    bg="#ccebdc",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
    borderwidth=0,
)
button_refresh.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

# Opciones de Búsqueda (Radiobuttons)
frame_search_options = tk.Frame(main_frame, bg="#f0f0f0")
frame_search_options.pack(fill=tk.X, pady=(0, 15))
tk.Label(
    frame_search_options, text="Tipo de Búsqueda:", font=("Helvetica", 10), bg="#f0f0f0"
).pack(side=tk.LEFT)

rb_phrase = tk.Radiobutton(
    frame_search_options,
    text="Frase Exacta",
    variable=search_mode_var,
    value="phrase",
    bg="#f0f0f0",
)
rb_phrase.pack(side=tk.LEFT, padx=5)
rb_keywords = tk.Radiobutton(
    frame_search_options,
    text="Palabras Clave",
    variable=search_mode_var,
    value="keywords",
    bg="#f0f0f0",
)
rb_keywords.pack(side=tk.LEFT, padx=5)
rb_advanced = tk.Radiobutton(
    frame_search_options,
    text="Avanzada (Excluir con -)",
    variable=search_mode_var,
    value="advanced",
    bg="#f0f0f0",
)
rb_advanced.pack(side=tk.LEFT, padx=5)

# Botones de Herramientas
frame_tools = tk.Frame(main_frame, bg="#f0f0f0")
frame_tools.pack(fill=tk.X, pady=(0, 15))

button_normalize = tk.Button(
    frame_tools,
    text="Normalizar",
    command=normalize_files,
    font=("Helvetica", 11, "bold"),
    bg="#ffc107",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
)
button_normalize.pack(side=tk.LEFT, padx=(0, 5), ipady=3)

button_sync_local = tk.Button(
    frame_tools,
    text="Exportar Local",
    command=sync_local_to_other,
    font=("Helvetica", 11, "bold"),
    bg="#e2e6ea",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
    borderwidth=0,
)
button_sync_local.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

button_cost_manager = tk.Button(
    frame_tools,
    text="Gestor Costos",
    command=open_cost_manager,
    font=("Helvetica", 11, "bold"),
    bg="#ffeeba",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
    borderwidth=0,
)
button_cost_manager.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

button_restrictions = tk.Button(
    frame_tools,
    text="Restricciones",
    command=open_restrictions_manager,
    font=("Helvetica", 11, "bold"),
    bg="#f8d7da",
    fg="black",
    relief="flat",
    padx=12,
    activebackground="black",
    activeforeground="white",
    borderwidth=0,
)
button_restrictions.pack(side=tk.LEFT, padx=(5, 0), ipady=3)

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

# --- BINDINGS PARA SELECCIÓN ---
tree_bodega.bind("<<TreeviewSelect>>", on_item_select)
tree_local.bind("<<TreeviewSelect>>", on_item_select)

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
    text="Eliminar Ítem Seleccionado",
    command=delete_item,
    font=("Helvetica", 10, "bold"),
    bg="#ffb3b3",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    bg="#a3e9a4",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
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
    activebackground="black",
    activeforeground="white",
)
btn_to_bodega.pack(side=tk.LEFT, ipady=2)

# --- Frame de Pedidos a Proveedores ---
frame_pedido = tk.Frame(main_frame, bg="#d1ecf1", pady=10, padx=10)
frame_pedido.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

pedido_input_frame = tk.Frame(frame_pedido, bg=frame_pedido["bg"])
pedido_input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20), anchor="n")
tk.Label(
    pedido_input_frame,
    text="Agregar a Pedido:",
    font=("Helvetica", 11, "bold"),
    bg=frame_pedido["bg"],
    fg="#0c5460",
).pack(anchor="w")
entry_pedido_container = tk.Frame(
    pedido_input_frame, relief="solid", borderwidth=1, bg="white"
)
entry_pedido_container.pack(anchor="w", pady=(5, 0))
entry_pedido_qty = tk.Entry(
    entry_pedido_container,
    font=("Helvetica", 11),
    width=10,
    relief="flat",
    borderwidth=0,
    bg="white",
)
entry_pedido_qty.pack(ipady=2, padx=1, pady=1)

providers_frame = tk.Frame(frame_pedido, bg=frame_pedido["bg"])
providers_frame.pack(side=tk.LEFT)

# PD Centro
pd_centro_frame = tk.Frame(providers_frame, bg=providers_frame["bg"])
pd_centro_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_centro = tk.Button(
    pd_centro_frame,
    text="PD Centro",
    command=lambda: add_to_purchase_order("pdcentro.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#a3e9a4",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="black",
    activeforeground="white",
)
btn_pd_centro.pack(pady=(0, 2))
tk.Label(
    pd_centro_frame, text="En Pedido:", font=("Helvetica", 8), bg=providers_frame["bg"]
).pack()
lbl_pd_centro_qty = tk.Label(
    pd_centro_frame,
    textvariable=pd_centro_qty_var,
    font=("Helvetica", 10, "bold"),
    bg="white",
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_centro_qty.pack()

# PD PR
pd_pr_frame = tk.Frame(providers_frame, bg=providers_frame["bg"])
pd_pr_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_pr = tk.Button(
    pd_pr_frame,
    text="PD PR",
    command=lambda: add_to_purchase_order("pdpr.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#a8d8ff",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="black",
    activeforeground="white",
)
btn_pd_pr.pack(pady=(0, 2))
tk.Label(
    pd_pr_frame, text="En Pedido:", font=("Helvetica", 8), bg=providers_frame["bg"]
).pack()
lbl_pd_pr_qty = tk.Label(
    pd_pr_frame,
    textvariable=pd_pr_qty_var,
    font=("Helvetica", 10, "bold"),
    bg="white",
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_pr_qty.pack()

# PD ST
pd_st_frame = tk.Frame(providers_frame, bg=providers_frame["bg"])
pd_st_frame.pack(side=tk.LEFT, padx=(0, 10))
btn_pd_st = tk.Button(
    pd_st_frame,
    text="PD ST",
    command=lambda: add_to_purchase_order("pdst.txt"),
    font=("Helvetica", 10, "bold"),
    bg="#d3d3d3",
    fg="black",
    relief="flat",
    padx=10,
    activebackground="black",
    activeforeground="white",
)
btn_pd_st.pack(pady=(0, 2))
tk.Label(
    pd_st_frame, text="En Pedido:", font=("Helvetica", 8), bg=providers_frame["bg"]
).pack()
lbl_pd_st_qty = tk.Label(
    pd_st_frame,
    textvariable=pd_st_qty_var,
    font=("Helvetica", 10, "bold"),
    bg="white",
    relief="solid",
    borderwidth=1,
    width=10,
)
lbl_pd_st_qty.pack()

root.mainloop()
