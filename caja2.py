import tkinter as tk
from tkinter import ttk

class CalculadoraEfectivo(tk.Tk):
    """
    Una sencilla aplicación de GUI para contar efectivo basada en denominaciones.
    """
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Efectivo")
        self.geometry("350x600")
        self.resizable(False, False)

        # Denominaciones comunes en Colombia (COP)
        self.denominaciones = {
            "Billetes de $100.000:": 100000,
            "Billetes de $50.000:": 50000,
            "Billetes de $20.000:": 20000,
            "Billetes de $10.000:": 10000,
            "Billetes de $5.000:": 5000,
            "Billetes de $2.000:": 2000,
            "Billetes de $1.000:": 1000,
            "Monedas de $1.000:": 1000,
            "Monedas de $500:": 500,
            "Monedas de $200:": 200,
            "Monedas de $100:": 100,
            "Monedas de $50:": 50,
        }
        self.entries = {}
        self.create_widgets()

    def create_widgets(self):
        """Crea y organiza los widgets en la ventana."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Crear campos de entrada para cada denominación
        row = 0
        for label_text, value in self.denominaciones.items():
            ttk.Label(main_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(main_frame, width=12, justify='right')
            entry.grid(row=row, column=1, sticky="e", pady=4)
            self.entries[value] = entry
            row += 1
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, pady=10, sticky='ew')
        row += 1

        # Botón para calcular
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10))
        btn_calcular = ttk.Button(main_frame, text="Calcular Total", command=self.calcular_total)
        btn_calcular.grid(row=row, column=0, columnspan=2, pady=10, ipady=5)
        
        row += 1
        
        # Etiqueta para mostrar el resultado
        self.total_label = ttk.Label(main_frame, text="Total: $0", font=("Helvetica", 16, "bold"), anchor="center")
        self.total_label.grid(row=row, column=0, columnspan=2, pady=10)

    def calcular_total(self):
        """Calcula el total del efectivo a partir de las cantidades ingresadas."""
        total = 0
        for value, entry in self.entries.items():
            try:
                # Obtener la cantidad del campo de entrada, si está vacío, usar 0
                cantidad = int(entry.get() or 0)
                total += cantidad * value
            except ValueError:
                # Si el usuario ingresa texto no numérico, se ignora esa línea
                pass
        
        # Formatear el total con separadores de miles y mostrarlo
        self.total_label.config(text=f"Total: ${total:,.0f}")

if __name__ == "__main__":
    app = CalculadoraEfectivo()
    app.mainloop()
