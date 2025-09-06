import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from tkcalendar import DateEntry

# --- LÓGICA DE ANÁLISIS DE DATOS (Funciones de Pandas) ---


def cargar_datos(ruta_archivo):
    """Carga y procesa los datos desde un archivo CSV."""
    nombres_columnas = [
        "Timestamp",
        "ID_Venta",
        "Descripcion",
        "Cantidad",
        "CostoUnitario",
        "PrecioUnitario",
        "TotalVenta",
        "Ganancia",
        "Fuente",
        "Cliente",
    ]
    try:
        datos = pd.read_csv(
            ruta_archivo,
            header=None,
            names=nombres_columnas,
        )
        datos["Timestamp"] = pd.to_datetime(datos["Timestamp"], errors="coerce")
        columnas_numericas = [
            "Cantidad",
            "CostoUnitario",
            "PrecioUnitario",
            "TotalVenta",
            "Ganancia",
        ]
        for col in columnas_numericas:
            datos[col] = pd.to_numeric(datos[col], errors="coerce")
        datos.dropna(subset=["Timestamp"] + columnas_numericas, inplace=True)
        return datos
    except FileNotFoundError:
        messagebox.showerror(
            "Error", f"El archivo no fue encontrado en la ruta:\n{ruta_archivo}"
        )
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al cargar el archivo:\n{e}")
        return None


def aplicar_filtros(df, fecha_inicio, fecha_fin, palabra_clave, producto_seleccionado):
    """
    Aplica todos los filtros seleccionados al DataFrame.
    """
    df_filtrado = df.copy()

    if fecha_inicio:
        df_filtrado = df_filtrado[
            df_filtrado["Timestamp"] >= pd.to_datetime(fecha_inicio)
        ]
    if fecha_fin:
        df_filtrado = df_filtrado[
            df_filtrado["Timestamp"] < pd.to_datetime(fecha_fin) + pd.Timedelta(days=1)
        ]

    if palabra_clave:
        df_filtrado = df_filtrado[
            df_filtrado["Descripcion"].str.contains(palabra_clave, case=False, na=False)
        ]

    if producto_seleccionado and producto_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Descripcion"] == producto_seleccionado]

    return df_filtrado


def generar_reporte_agregado(
    df, agrupar_por, valores, funcion_agregacion, orden, ordenar_por
):
    """Genera un reporte agregado (tabla dinámica) con ordenamiento flexible."""
    if df is None or df.empty:
        return None
    mapa_funciones = {
        "Suma": "sum",
        "Promedio": "mean",
        "Conteo": "count",
        "Máximo": "max",
        "Mínimo": "min",
    }
    agg_func = mapa_funciones.get(funcion_agregacion, "sum")

    try:
        tabla_dinamica = df.pivot_table(
            index=agrupar_por, values=valores, aggfunc=agg_func
        ).reset_index()

        columna_a_ordenar = agrupar_por if ordenar_por == "Nombre" else valores
        ascending_bool = True if orden == "Ascendente" else False
        tabla_dinamica_ordenada = tabla_dinamica.sort_values(
            by=columna_a_ordenar, ascending=ascending_bool
        )

        return tabla_dinamica_ordenada
    except Exception as e:
        messagebox.showerror("Error de Reporte", f"No se pudo generar el reporte:\n{e}")
        return None


# --- CLASE PRINCIPAL DE LA APLICACIÓN (Interfaz Gráfica con Tkinter) ---


class AnalizadorVentasApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador de Ventas")
        self.geometry("1050x750")

        self.datos_originales = None
        self.ruta_archivo = "registro_ventas.csv"

        # Variables para los labels de resumen
        self.total_items_var = tk.StringVar(value="Items Únicos: ---")
        self.total_cantidad_var = tk.StringVar(value="Cantidad Total: ---")
        self.total_venta_var = tk.StringVar(value="Venta Total: ---")
        self.total_ganancia_var = tk.StringVar(value="Ganancia Total: ---")

        self._crear_widgets()
        self.cargar_archivo_por_defecto()

    def _crear_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        controles_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        controles_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            controles_frame, text="Cargar Archivo CSV", command=self.cargar_archivo
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.lbl_archivo = ttk.Label(
            controles_frame,
            text=f"Archivo: {self.ruta_archivo.split('/')[-1]}",
            font=("Arial", 8),
        )
        self.lbl_archivo.grid(row=0, column=1, columnspan=2, padx=5, sticky="w")

        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filtros_frame, text="Fecha Inicio:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cal_inicio = DateEntry(filtros_frame, date_pattern="y-mm-dd", width=12)
        self.cal_inicio.grid(row=0, column=1, padx=5, pady=5)
        self.cal_inicio.set_date(None)
        self.cal_inicio.bind("<<DateEntrySelected>>", self.actualizar_lista_productos)

        ttk.Label(filtros_frame, text="Fecha Fin:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.cal_fin = DateEntry(filtros_frame, date_pattern="y-mm-dd", width=12)
        self.cal_fin.grid(row=0, column=3, padx=5, pady=5)
        self.cal_fin.set_date(None)
        self.cal_fin.bind("<<DateEntrySelected>>", self.actualizar_lista_productos)

        ttk.Label(filtros_frame, text="Palabra Clave (Búsqueda):").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_palabra_clave = ttk.Entry(filtros_frame, width=20)
        self.entry_palabra_clave.grid(row=1, column=1, padx=5, pady=5, columnspan=1)

        ttk.Label(filtros_frame, text="Seleccionar Producto (Opcional):").grid(
            row=1, column=2, padx=5, pady=5, sticky="w"
        )
        self.combo_producto = ttk.Combobox(filtros_frame, width=30, state="readonly")
        self.combo_producto.grid(row=1, column=3, padx=5, pady=5, columnspan=2)
        self.combo_producto["values"] = ["Todos"]
        self.combo_producto.set("Todos")

        reporte_frame = ttk.LabelFrame(
            main_frame, text="Configuración del Reporte", padding="10"
        )
        reporte_frame.pack(fill=tk.X, pady=5)

        opciones_agrupar = ["Descripcion", "Cliente", "Fuente"]
        opciones_valores = ["Ganancia", "TotalVenta", "Cantidad", "PrecioUnitario"]
        opciones_funcion = ["Suma", "Promedio", "Conteo", "Máximo", "Mínimo"]

        ttk.Label(reporte_frame, text="Agrupar por:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.combo_agrupar = ttk.Combobox(
            reporte_frame, values=opciones_agrupar, state="readonly"
        )
        self.combo_agrupar.set("Descripcion")
        self.combo_agrupar.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(reporte_frame, text="Calcular:").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.combo_valores = ttk.Combobox(
            reporte_frame, values=opciones_valores, state="readonly"
        )
        self.combo_valores.set("Ganancia")
        self.combo_valores.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(reporte_frame, text="con la operación:").grid(
            row=0, column=4, padx=5, pady=5, sticky="w"
        )
        self.combo_funcion = ttk.Combobox(
            reporte_frame, values=opciones_funcion, state="readonly"
        )
        self.combo_funcion.set("Suma")
        self.combo_funcion.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(reporte_frame, text="Ordenar por:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.ordenar_por_var = tk.StringVar(value="Valor")
        ttk.Radiobutton(
            reporte_frame, text="Valor", variable=self.ordenar_por_var, value="Valor"
        ).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(
            reporte_frame, text="Nombre", variable=self.ordenar_por_var, value="Nombre"
        ).grid(row=1, column=2, padx=5, pady=5, sticky="w")

        ttk.Label(reporte_frame, text="en orden:").grid(
            row=1, column=3, padx=5, pady=5, sticky="w"
        )
        self.combo_orden = ttk.Combobox(
            reporte_frame,
            values=["Descendente", "Ascendente"],
            state="readonly",
            width=12,
        )
        self.combo_orden.set("Descendente")
        self.combo_orden.grid(row=1, column=4, padx=5, pady=5)

        ttk.Button(
            reporte_frame, text="📊 Generar Reporte", command=self.generar_reporte
        ).grid(row=0, column=6, rowspan=2, padx=20, pady=5, sticky="e")

        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        resultados_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(resultados_frame, show="headings")
        vsb = ttk.Scrollbar(
            resultados_frame, orient="vertical", command=self.tree.yview
        )
        hsb = ttk.Scrollbar(
            resultados_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill=tk.BOTH, expand=True)

        resumen_frame = ttk.LabelFrame(
            main_frame, text="Resumen del Reporte", padding="10"
        )
        resumen_frame.pack(fill=tk.X, pady=(5, 0))

        style = ttk.Style()
        style.configure("Resumen.TLabel", font=("Arial", 10, "bold"))
        ttk.Label(
            resumen_frame, textvariable=self.total_items_var, style="Resumen.TLabel"
        ).pack(side=tk.LEFT, padx=15)
        ttk.Label(
            resumen_frame, textvariable=self.total_cantidad_var, style="Resumen.TLabel"
        ).pack(side=tk.LEFT, padx=15)
        ttk.Label(
            resumen_frame, textvariable=self.total_venta_var, style="Resumen.TLabel"
        ).pack(side=tk.LEFT, padx=15)
        ttk.Label(
            resumen_frame, textvariable=self.total_ganancia_var, style="Resumen.TLabel"
        ).pack(side=tk.LEFT, padx=15)

    def cargar_archivo(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        self.ruta_archivo = filepath
        self.datos_originales = cargar_datos(self.ruta_archivo)
        self.lbl_archivo.config(text=f"Archivo: {self.ruta_archivo.split('/')[-1]}")
        if self.datos_originales is not None:
            messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
            self.actualizar_lista_productos()

    def cargar_archivo_por_defecto(self):
        """Carga el archivo CSV por defecto al iniciar la aplicación."""
        self.datos_originales = cargar_datos(self.ruta_archivo)
        if self.datos_originales is not None:
            self.lbl_archivo.config(text=f"Archivo: {self.ruta_archivo.split('/')[-1]}")
            self.actualizar_lista_productos()

    def actualizar_lista_productos(self, event=None):
        if self.datos_originales is None:
            return
        df_filtrado_fecha = self.datos_originales.copy()
        try:
            fecha_inicio = self.cal_inicio.get_date()
            df_filtrado_fecha = df_filtrado_fecha[
                df_filtrado_fecha["Timestamp"] >= pd.to_datetime(fecha_inicio)
            ]
        except tk.TclError:
            pass
        try:
            fecha_fin = self.cal_fin.get_date()
            df_filtrado_fecha = df_filtrado_fecha[
                df_filtrado_fecha["Timestamp"]
                < pd.to_datetime(fecha_fin) + pd.Timedelta(days=1)
            ]
        except tk.TclError:
            pass
        productos_unicos = sorted(df_filtrado_fecha["Descripcion"].unique().tolist())
        self.combo_producto["values"] = ["Todos"] + productos_unicos
        self.combo_producto.set("Todos")

    def generar_reporte(self):
        if self.datos_originales is None:
            messagebox.showwarning("Atención", "Primero debe cargar un archivo CSV.")
            return

        try:
            fecha_inicio = self.cal_inicio.get_date()
        except tk.TclError:
            fecha_inicio = None
        try:
            fecha_fin = self.cal_fin.get_date()
        except tk.TclError:
            fecha_fin = None

        palabra_clave = self.entry_palabra_clave.get()
        producto_seleccionado = self.combo_producto.get()
        agrupar_por = self.combo_agrupar.get()
        valores = self.combo_valores.get()
        funcion = self.combo_funcion.get()
        orden = self.combo_orden.get()
        ordenar_por = self.ordenar_por_var.get()

        if not all([agrupar_por, valores, funcion, orden, ordenar_por]):
            messagebox.showwarning(
                "Atención", "Debe seleccionar todas las opciones del reporte."
            )
            return

        datos_filtrados = aplicar_filtros(
            self.datos_originales,
            fecha_inicio,
            fecha_fin,
            palabra_clave,
            producto_seleccionado,
        )

        if datos_filtrados is not None and not datos_filtrados.empty:
            total_items = datos_filtrados[agrupar_por].nunique()
            total_cantidad = datos_filtrados["Cantidad"].sum()
            total_venta = datos_filtrados["TotalVenta"].sum()
            total_ganancia = datos_filtrados["Ganancia"].sum()
            self.total_items_var.set(f"Items Únicos: {total_items}")
            self.total_cantidad_var.set(f"Cantidad Total: {int(total_cantidad)}")
            self.total_venta_var.set(f"Venta Total: ${total_venta:,.2f}")
            self.total_ganancia_var.set(f"Ganancia Total: ${total_ganancia:,.2f}")
        else:
            self.total_items_var.set("Items Únicos: ---")
            self.total_cantidad_var.set("Cantidad Total: ---")
            self.total_venta_var.set("Venta Total: ---")
            self.total_ganancia_var.set("Ganancia Total: ---")

        reporte_df = generar_reporte_agregado(
            datos_filtrados, agrupar_por, valores, funcion, orden, ordenar_por
        )
        self.mostrar_en_tabla(reporte_df)

    def mostrar_en_tabla(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if df is None or df.empty:
            messagebox.showinfo(
                "Sin Resultados", "No se encontraron datos con los filtros aplicados."
            )
            self.tree["columns"] = []
            return
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))


if __name__ == "__main__":
    app = AnalizadorVentasApp()
    app.mainloop()
