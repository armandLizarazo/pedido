import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class CajaApp(tk.Tk):
    """
    Una aplicación de escritorio con interfaz gráfica para calcular costos de venta
    y contar billetes, reemplazando la versión de consola.
    """
    def __init__(self):
        super().__init__()

        # --- Configuración de la ventana principal ---
        self.title("Asistente de Caja v1.0")
        self.geometry("600x450")
        self.resizable(False, False)

        # --- Estilo ---
        style = ttk.Style(self)
        style.theme_use('clam') # Un tema moderno

        # --- Creación de las pestañas ---
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Pestañas individuales ---
        self.tab_calculadora = ttk.Frame(notebook)
        self.tab_contador = ttk.Frame(notebook)

        notebook.add(self.tab_calculadora, text='Calculadora de Costo')
        notebook.add(self.tab_contador, text='Contador de Billetes')

        # --- Inicializar el contenido de cada pestaña ---
        self.crear_widgets_calculadora()
        self.crear_widgets_contador()

    # --- Lógica de la calculadora de costo ---
    def calcular_costo_base(self, venta, utilidad_porcentaje):
        """
        Calcula el costo base dado el valor de la venta y el porcentaje de utilidad.
        """
        try:
            utilidad_decimal = float(utilidad_porcentaje) / 100
            costo_base = float(venta) / (1 + utilidad_decimal)
            return costo_base
        except (ValueError, ZeroDivisionError):
            return None

    def ejecutar_calculo(self):
        """
        Se ejecuta al presionar el botón de calcular.
        Toma los valores de la UI, calcula y muestra el resultado.
        """
        try:
            venta_str = self.venta_entry.get().replace(".", "").replace(",", ".")
            utilidad_str = self.utilidad_entry.get().replace(",", ".")
            
            venta = float(venta_str)
            utilidad = float(utilidad_str)

            costo_base = self.calcular_costo_base(venta, utilidad)

            if costo_base is not None:
                # Formato para moneda colombiana, sin decimales para el costo.
                resultado_formato = f"${costo_base:,.0f}".replace(",", ".")
                self.resultado_label.config(text=f"Costo Base: {resultado_formato}")
                self.copiar_al_portapapeles(f"{costo_base:.0f}")
                messagebox.showinfo("Copiado", f"El resultado '{costo_base:.0f}' ha sido copiado al portapapeles.")
            else:
                self.resultado_label.config(text="Error en el cálculo")

        except ValueError:
            messagebox.showerror("Error de Entrada", "Por favor, ingrese valores numéricos válidos para la venta y la utilidad.")

    def seleccionar_tipo_venta(self):
        """
        Actualiza el campo de utilidad basado en la selección del radio button.
        """
        if self.tipo_venta_var.get() == "recargas":
            self.utilidad_entry.config(state='disabled')
            self.utilidad_var.set("6")
        else:
            self.utilidad_entry.config(state='normal')
            self.utilidad_var.set("") # Limpia el campo para entrada manual

    def copiar_al_portapapeles(self, texto):
        """
        Limpia el portapapeles y copia el nuevo texto.
        """
        self.clipboard_clear()
        self.clipboard_append(texto)
        self.update() # Requerido para que funcione en algunos sistemas

    # --- Lógica del contador de billetes ---
    def actualizar_totales(self, *args):
        """
        Actualiza los subtotales por denominación y el total general en tiempo real.
        """
        total_general = 0
        for denom, widgets in self.billetes_widgets.items():
            try:
                cantidad = int(widgets["var"].get())
                if cantidad < 0: # No permitir negativos
                    cantidad = 0
                    widgets["var"].set("0")
                subtotal = cantidad * denom
                widgets["subtotal"].set(f"${subtotal:,.0f}".replace(",", "."))
                total_general += subtotal
            except (ValueError, TclError):
                widgets["subtotal"].set("$0")
        
        self.total_general_var.set(f"Total General: ${total_general:,.0f}".replace(",", "."))
        self.total_a_guardar = total_general # Guardar para el archivo

    def guardar_conteo(self):
        """
        Guarda el conteo actual en el archivo 'registro_caja.txt'.
        """
        nombre_conteo = self.nombre_conteo_entry.get()
        if not nombre_conteo:
            messagebox.showwarning("Falta Información", "Por favor, ingrese un nombre para el conteo.")
            return

        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("registro_caja.txt", "a", encoding="utf-8") as archivo:
                archivo.write(f"\n--- Conteo: {nombre_conteo} ---\n")
                archivo.write(f"Fecha: {fecha_actual}\n")
                
                tabla_texto = []
                for denom, widgets in self.billetes_widgets.items():
                    cantidad = widgets["var"].get()
                    subtotal_str = widgets["subtotal"].get().replace("$", "").replace(".", "")
                    denom_str = f"{denom:,.0f}".replace(",", ".")
                    tabla_texto.append(f"  - Billetes de ${denom_str}: {cantidad} -> Total: ${subtotal_str}\n")
                
                archivo.writelines(tabla_texto)
                archivo.write(f"Monto total contado: {self.total_general_var.get().split(': ')[1]}\n")
                archivo.write("-" * 30 + "\n")
            
            messagebox.showinfo("Éxito", f"El conteo '{nombre_conteo}' ha sido guardado en 'registro_caja.txt'.")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo.\nError: {e}")

    # --- Creación de Widgets (Componentes de la UI) ---
    def crear_widgets_calculadora(self):
        """
        Crea todos los componentes para la pestaña de la calculadora.
        """
        frame = ttk.Frame(self.tab_calculadora, padding="20")
        frame.pack(fill="both", expand=True)

        # Tipo de Venta
        self.tipo_venta_var = tk.StringVar(value="recargas")
        ttk.Label(frame, text="Tipo de Venta:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Radiobutton(frame, text="Recargas (6% utilidad)", variable=self.tipo_venta_var, value="recargas", command=self.seleccionar_tipo_venta).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Otra Venta", variable=self.tipo_venta_var, value="otra", command=self.seleccionar_tipo_venta).grid(row=1, column=1, sticky="w")

        # Entradas de datos
        ttk.Label(frame, text="Valor de la Venta:").grid(row=2, column=0, sticky="w", pady=5)
        self.venta_entry = ttk.Entry(frame, width=25)
        self.venta_entry.grid(row=2, column=1, sticky="ew")

        ttk.Label(frame, text="Porcentaje de Utilidad (%):").grid(row=3, column=0, sticky="w", pady=5)
        self.utilidad_var = tk.StringVar()
        self.utilidad_entry = ttk.Entry(frame, width=25, textvariable=self.utilidad_var)
        self.utilidad_entry.grid(row=3, column=1, sticky="ew")
        
        self.seleccionar_tipo_venta() # Llama para establecer estado inicial

        # Botón y Resultado
        ttk.Button(frame, text="Calcular y Copiar", command=self.ejecutar_calculo).grid(row=4, column=0, columnspan=2, pady=20)
        
        self.resultado_label = ttk.Label(frame, text="Costo Base: $0", font=("Helvetica", 14, "bold"))
        self.resultado_label.grid(row=5, column=0, columnspan=2, pady=10)

    def crear_widgets_contador(self):
        """
        Crea todos los componentes para la pestaña del contador de billetes.
        """
        main_frame = ttk.Frame(self.tab_contador, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Frame para las denominaciones y el total
        conteo_frame = ttk.LabelFrame(main_frame, text="Denominaciones", padding="10")
        conteo_frame.pack(fill="x")
        
        # Frame para guardar
        guardar_frame = ttk.LabelFrame(main_frame, text="Guardar Conteo", padding="10")
        guardar_frame.pack(fill="x", pady=10)

        # Crear entradas para cada billete
        self.billetes_widgets = {}
        denominaciones = [100000, 50000, 20000, 10000, 5000, 2000]
        
        for i, denom in enumerate(denominaciones):
            # Etiqueta de la denominación
            ttk.Label(conteo_frame, text=f"${denom:,.0f}".replace(",", ".")).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            # Entrada para la cantidad
            cantidad_var = tk.StringVar(value="0")
            cantidad_var.trace_add("write", self.actualizar_totales)
            cantidad_entry = ttk.Entry(conteo_frame, textvariable=cantidad_var, width=10)
            cantidad_entry.grid(row=i, column=1, padx=5)
            
            # Etiqueta para el subtotal
            subtotal_var = tk.StringVar(value="$0")
            ttk.Label(conteo_frame, textvariable=subtotal_var, width=15).grid(row=i, column=2, sticky="e", padx=5)
            
            self.billetes_widgets[denom] = {"var": cantidad_var, "entry": cantidad_entry, "subtotal": subtotal_var}

        # Total General
        self.total_general_var = tk.StringVar(value="Total General: $0")
        ttk.Label(conteo_frame, textvariable=self.total_general_var, font=("Helvetica", 12, "bold")).grid(row=len(denominaciones), column=0, columnspan=3, pady=10)

        # Sección para guardar
        ttk.Label(guardar_frame, text="Nombre del Conteo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.nombre_conteo_entry = ttk.Entry(guardar_frame, width=30)
        self.nombre_conteo_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Button(guardar_frame, text="Guardar en Archivo", command=self.guardar_conteo).grid(row=1, column=0, columnspan=2, pady=10)

        self.actualizar_totales() # Llama para inicializar los totales

if __name__ == "__main__":
    app = CajaApp()
    app.mainloop()

