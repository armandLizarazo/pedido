import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime
import os
import json
import re

# Nombres de archivos por defecto
HISTORIAL_TXT_DEFAULT = "historial_eliminados.txt"
HISTORIAL_JSON_DEFAULT = "historial_datos.json"


def parsear_txt_a_lista(ruta_txt):
    """Parsea un archivo TXT y devuelve una lista de diccionarios con los registros."""
    if not os.path.exists(ruta_txt):
        return []

    try:
        with open(ruta_txt, "r", encoding="utf-8") as f:
            contenido = f.read()

        # Separar por bloques de líneas divisorias (flexibilidad de 40 a 80 caracteres '=')
        bloques = re.split(r"={40,}", contenido)
        registros = []

        for bloque in bloques:
            if not bloque.strip() or "Fecha:" not in bloque:
                continue

            # Extraer metadatos
            fecha_match = re.search(r"Fecha:\s*(.*)", bloque)
            archivo_match = re.search(r"Archivo:\s*(.*)", bloque)

            if fecha_match and archivo_match:
                fecha = fecha_match.group(1).strip()
                archivo = archivo_match.group(1).strip()

                # Extraer líneas eliminadas
                lineas_eliminadas = []
                items_L = re.findall(r"L(\d+):\s*(.*)", bloque)
                items_pipe = re.findall(r"(\d+)\s*\|\s*(.*)", bloque)

                found_items = items_L if items_L else items_pipe
                for num, cont in found_items:
                    lineas_eliminadas.append(
                        {"linea": int(num), "contenido": cont.strip()}
                    )

                registros.append(
                    {
                        "fecha": fecha,
                        "archivo": archivo,
                        "ruta_completa": "Convertido desde TXT",
                        "eliminados": lineas_eliminadas,
                        "total_conservados": 0,
                    }
                )
        return registros
    except Exception as e:
        print(f"Error parseando TXT: {e}")
        return []


def guardar_en_historial(datos_proceso):
    """Guarda registros en el TXT y JSON por defecto del sistema."""
    # Guardar en TXT
    with open(HISTORIAL_TXT_DEFAULT, "a", encoding="utf-8") as h:
        h.write(f"\n{'='*60}\n")
        h.write(f"Fecha: {datos_proceso['fecha']}\n")
        h.write(f"Archivo: {datos_proceso['archivo']}\n")
        h.write(f"Eliminados: {len(datos_proceso['eliminados'])}\n")
        h.write("--- DETALLE ---\n")
        for item in datos_proceso["eliminados"]:
            h.write(f"L{item['linea']}: {item['contenido']}\n")

    # Actualizar JSON por defecto
    historial = []
    if os.path.exists(HISTORIAL_JSON_DEFAULT):
        try:
            with open(HISTORIAL_JSON_DEFAULT, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except:
            historial = []

    historial.insert(0, datos_proceso)
    with open(HISTORIAL_JSON_DEFAULT, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)


class VentanaHistorial(tk.Toplevel):
    def __init__(self, parent, archivo_inicial=HISTORIAL_JSON_DEFAULT):
        super().__init__(parent)
        self.title("Buscador y Gestor de Reportes")
        self.geometry("1000x800")
        self.ruta_actual = archivo_inicial
        self.datos = []
        self.setup_ui()
        self.cargar_archivo(self.ruta_actual)

    def setup_ui(self):
        # Panel Superior: Archivo actual y Cargar otro
        top_bar = tk.Frame(self, bg="#e0e0e0", pady=5)
        top_bar.pack(fill=tk.X)

        self.lbl_archivo_abierto = tk.Label(
            top_bar,
            text=f"Archivo: {self.ruta_actual}",
            bg="#e0e0e0",
            font=("Arial", 9, "italic"),
        )
        self.lbl_archivo_abierto.pack(side=tk.LEFT, padx=10)

        tk.Button(
            top_bar, text="📂 Abrir otro JSON", command=self.seleccionar_otro_json
        ).pack(side=tk.RIGHT, padx=10)

        # Filtros
        f_frame = tk.LabelFrame(self, text=" Herramientas de Filtro ", padx=10, pady=10)
        f_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(f_frame, text="Nombre Archivo:").grid(row=0, column=0)
        self.ent_archivo = tk.Entry(f_frame, width=20)
        self.ent_archivo.grid(row=0, column=1, padx=5)

        tk.Label(f_frame, text="Texto en Borrados:").grid(row=0, column=2)
        self.ent_keyword = tk.Entry(f_frame, width=25)
        self.ent_keyword.grid(row=0, column=3, padx=5)

        tk.Button(
            f_frame,
            text="🔍 Buscar",
            command=self.filtrar,
            bg="#2196F3",
            fg="white",
            width=12,
        ).grid(row=0, column=4, padx=10)

        # Tabla
        t_frame = tk.Frame(self)
        t_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.tree = ttk.Treeview(
            t_frame, columns=("fecha", "archivo", "del"), show="headings"
        )
        self.tree.heading("fecha", text="Fecha y Hora")
        self.tree.heading("archivo", text="Archivo Procesado")
        self.tree.heading("del", text="Líneas Eliminadas")

        self.tree.column("fecha", width=180)
        self.tree.column("archivo", width=400)

        vsb = ttk.Scrollbar(t_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Detalle
        tk.Label(
            self, text="Contenido del reporte seleccionado:", font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 0))
        self.det_text = scrolledtext.ScrolledText(
            self, height=15, font=("Consolas", 10), bg="#1e1e1e", fg="#cecece"
        )
        self.det_text.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def cargar_archivo(self, ruta):
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    self.datos = json.load(f)

                # Validar que los datos sean una lista
                if not isinstance(self.datos, list):
                    raise ValueError(
                        "El archivo no contiene una lista de reportes válida."
                    )

                self.ruta_actual = ruta
                self.lbl_archivo_abierto.config(
                    text=f"Archivo: {os.path.basename(ruta)}"
                )

                # Reiniciar filtros y detalle al cargar nuevo archivo
                self.ent_archivo.delete(0, tk.END)
                self.ent_keyword.delete(0, tk.END)
                self.det_text.delete(1.0, tk.END)

                self.actualizar_tabla(self.datos)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el JSON: {e}")
        else:
            self.datos = []
            self.actualizar_tabla([])

    def seleccionar_otro_json(self):
        f = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
        if f:
            self.cargar_archivo(f)

    def filtrar(self):
        arch = self.ent_archivo.get().lower()
        key = self.ent_keyword.get().lower()
        res = [
            r
            for r in self.datos
            if arch in r["archivo"].lower()
            and (
                not key
                or any(key in item["contenido"].lower() for item in r["eliminados"])
            )
        ]
        self.actualizar_tabla(res)

    def actualizar_tabla(self, lista):
        # Limpiar tabla actual
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not lista:
            return

        # Ordenar por fecha descendente
        try:
            lista_ord = sorted(
                lista, key=lambda x: str(x.get("fecha", "")), reverse=True
            )
            for r in lista_ord:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        r.get("fecha", "N/A"),
                        r.get("archivo", "N/A"),
                        len(r.get("eliminados", [])),
                    ),
                )
        except Exception as e:
            print(f"Error al actualizar tabla: {e}")

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        # Obtener valores de la fila seleccionada
        vals = self.tree.item(sel[0])["values"]
        fecha_sel = str(vals[0])
        archivo_sel = str(vals[1])

        # Buscar en los datos cargados
        reg = next(
            (
                r
                for r in self.datos
                if str(r.get("fecha")) == fecha_sel and r.get("archivo") == archivo_sel
            ),
            None,
        )

        if reg:
            self.det_text.delete(1.0, tk.END)
            self.det_text.insert(tk.END, f"REPORTE DE ELIMINACIÓN\n{'-'*40}\n")
            self.det_text.insert(
                tk.END,
                f"Archivo: {reg.get('archivo')}\nFecha:   {reg.get('fecha')}\n\n",
            )

            eliminados = reg.get("eliminados", [])
            if eliminados:
                for item in eliminados:
                    self.det_text.insert(
                        tk.END, f"[L{item.get('linea')}] {item.get('contenido')}\n"
                    )
            else:
                self.det_text.insert(
                    tk.END, "No hay líneas registradas como eliminadas en este bloque."
                )


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CleanScript Pro v4.0")
        self.root.geometry("850x650")
        self.archivos_limpiar = []
        self.setup_ui()

    def setup_ui(self):
        # Menu Superior
        menu_frame = tk.Frame(self.root, pady=15, bg="#f5f5f5")
        menu_frame.pack(fill=tk.X)

        tk.Button(
            menu_frame,
            text="📂 Seleccionar para Limpiar",
            command=self.seleccionar_archivos,
        ).pack(side=tk.LEFT, padx=10)
        self.btn_run = tk.Button(
            menu_frame,
            text="⚡ Ejecutar Limpieza",
            command=self.ejecutar_limpieza,
            state=tk.DISABLED,
            bg="#2e7d32",
            fg="white",
        )
        self.btn_run.pack(side=tk.LEFT, padx=5)

        # Acciones de Historial
        tk.Button(
            menu_frame,
            text="📊 Ver Consultas",
            command=self.abrir_historial,
            bg="#455a64",
            fg="white",
        ).pack(side=tk.RIGHT, padx=10)
        tk.Button(
            menu_frame,
            text="🛠 Convertir TXT a JSON",
            command=self.convertir_archivo,
            bg="#fb8c00",
            fg="black",
        ).pack(side=tk.RIGHT, padx=5)

        self.log = scrolledtext.ScrolledText(
            self.root, bg="white", font=("Consolas", 10)
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.log.insert(
            tk.END,
            "Bienvenido. Use 'Seleccionar para Limpiar' para procesar archivos\no 'Convertir TXT a JSON' para recuperar reportes antiguos.\n",
        )

    def seleccionar_archivos(self):
        f = filedialog.askopenfilenames(filetypes=[("Texto", "*.txt")])
        if f:
            self.archivos_limpiar = list(f)
            self.btn_run.config(state=tk.NORMAL)
            self.log.insert(tk.END, f"\n>> {len(f)} archivos listos para limpieza.\n")

    def ejecutar_limpieza(self):
        self.log.delete(1.0, tk.END)
        for path in self.archivos_limpiar:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                clean, deleted = [], []
                for n, l in enumerate(lines, 1):
                    if l.strip().startswith("#") or (
                        l.startswith("    ") and l.rstrip().endswith(" ok")
                    ):
                        deleted.append({"linea": n, "contenido": l.strip()})
                    else:
                        clean.append(l)

                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(clean)

                datos = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "archivo": os.path.basename(path),
                    "ruta_completa": path,
                    "eliminados": deleted,
                    "total_conservados": len(clean),
                }
                guardar_en_historial(datos)
                self.log.insert(
                    tk.END,
                    f"✓ {datos['archivo']} procesado (Borrados: {len(deleted)})\n",
                )
            except Exception as e:
                self.log.insert(tk.END, f"✕ Error en {path}: {e}\n")

        self.btn_run.config(state=tk.DISABLED)
        messagebox.showinfo("Listo", "Proceso terminado con éxito.")

    def convertir_archivo(self):
        """Función: Selecciona un TXT y lo convierte en JSON."""
        archivo_txt = filedialog.askopenfilename(
            title="Selecciona el archivo de reporte (.txt)",
            filetypes=[("Archivos TXT", "*.txt")],
        )
        if not archivo_txt:
            return

        registros = parsear_txt_a_lista(archivo_txt)
        if not registros:
            messagebox.showwarning(
                "Advertencia",
                "No se encontraron registros válidos en el archivo TXT seleccionado.",
            )
            return

        archivo_json_dest = filedialog.asksaveasfilename(
            title="Guardar como JSON compatible",
            defaultextension=".json",
            initialfile="reporte_convertido.json",
            filetypes=[("Archivos JSON", "*.json")],
        )

        if archivo_json_dest:
            with open(archivo_json_dest, "w", encoding="utf-8") as f:
                json.dump(registros, f, indent=4, ensure_ascii=False)
            messagebox.showinfo(
                "Éxito",
                f"Se han convertido {len(registros)} registros a JSON.\nAhora puedes abrir este archivo desde 'Ver Consultas'.",
            )

    def abrir_historial(self):
        VentanaHistorial(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
