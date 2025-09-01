# Asegúrate de tener las librerías necesarias instaladas:
# pip install "qrcode[pil]"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont


class AppGeneradorQR:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Códigos QR con Etiqueta")
        self.root.geometry("450x600")  # Un poco más alto para el nuevo campo
        self.root.resizable(False, False)

        # Estilo
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Variable para guardar la imagen del QR
        self.qr_image = None

        # --- Contenido de la ventana ---
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill="both")

        # 1. Entrada de datos
        ttk.Label(
            main_frame, text="Introduce el texto o la URL:", font=("Helvetica", 12)
        ).pack(pady=(0, 5))
        self.entry_datos = ttk.Entry(main_frame, width=50, font=("Helvetica", 10))
        self.entry_datos.pack(pady=(0, 15), ipady=4)
        self.entry_datos.insert(0, "Escribe aquí tu información")

        # 2. Entrada para etiqueta de texto
        ttk.Label(
            main_frame, text="Etiqueta de texto (opcional):", font=("Helvetica", 12)
        ).pack(pady=(10, 5))
        self.entry_etiqueta = ttk.Entry(main_frame, width=50, font=("Helvetica", 10))
        self.entry_etiqueta.pack(pady=(0, 15), ipady=4)

        # 3. Ajuste de tamaño (campo de texto)
        size_frame = ttk.Frame(main_frame)
        size_frame.pack(pady=(0, 20))
        ttk.Label(size_frame, text="Tamaño (resolución):", font=("Helvetica", 12)).pack(
            side="left", padx=(0, 10)
        )
        self.tamano_var = tk.StringVar(value="10")
        self.entry_tamano = ttk.Entry(
            size_frame, width=10, font=("Helvetica", 10), textvariable=self.tamano_var
        )
        self.entry_tamano.pack(side="left")

        # 4. Botón para generar
        self.boton_generar = ttk.Button(
            main_frame, text="Generar Código QR", command=self.generar_qr
        )
        self.boton_generar.pack(pady=10)

        # 5. Vista previa del QR
        self.label_qr_preview = ttk.Label(
            main_frame, text="Aquí aparecerá la vista previa"
        )
        self.label_qr_preview.pack(pady=10)

        # 6. Botón para guardar
        self.boton_guardar = ttk.Button(
            main_frame, text="Guardar Imagen", state="disabled", command=self.guardar_qr
        )
        self.boton_guardar.pack(pady=10)

    def generar_qr(self):
        """Genera y muestra una vista previa del código QR, con etiqueta si se proporciona."""
        datos = self.entry_datos.get()
        if not datos:
            messagebox.showwarning(
                "Campo Vacío", "Por favor, introduce datos para generar el QR."
            )
            return

        try:
            tamano_caja = int(self.entry_tamano.get())
            if tamano_caja <= 0:
                messagebox.showwarning(
                    "Tamaño Inválido", "El tamaño debe ser un número entero positivo."
                )
                return
        except ValueError:
            messagebox.showwarning(
                "Entrada Inválida",
                "Por favor, introduce un número entero para el tamaño.",
            )
            return

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=tamano_caja,
                border=4,
            )
            qr.add_data(datos)
            qr.make(fit=True)

            # Generamos la imagen base del QR y la convertimos a RGB
            qr_img = qr.make_image(fill_color="black", back_color="white").convert(
                "RGB"
            )

            etiqueta_texto = self.entry_etiqueta.get()

            if etiqueta_texto:
                # Si hay texto, creamos una nueva imagen más grande con el texto debajo
                try:
                    font_size = max(
                        15, int(qr_img.width * 0.05)
                    )  # Tamaño de fuente proporcional y pequeño
                    font = ImageFont.truetype("arial.ttf", size=font_size)
                except IOError:
                    font = ImageFont.load_default()

                draw = ImageDraw.Draw(qr_img)
                text_bbox = draw.textbbox((0, 0), etiqueta_texto, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                padding = int(font_size / 2)

                final_image = Image.new(
                    "RGB",
                    (qr_img.width, qr_img.height + text_height + padding * 2),
                    "white",
                )
                final_image.paste(qr_img, (0, 0))

                draw = ImageDraw.Draw(final_image)
                text_x = (final_image.width - text_width) / 2
                text_y = qr_img.height + padding
                draw.text((text_x, text_y), etiqueta_texto, font=font, fill="black")

                self.qr_image = final_image
            else:
                self.qr_image = qr_img

            # Creamos una versión para mostrar en la vista previa (tamaño fijo)
            img_tk = self.qr_image.resize((250, 250), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img_tk)

            self.label_qr_preview.config(image=self.photo_image, text="")
            self.boton_guardar.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar el QR: {e}")

    def guardar_qr(self):
        """Abre un diálogo para guardar la imagen del QR."""
        if self.qr_image:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Guardar Código QR como...",
            )
            if filepath:
                try:
                    self.qr_image.save(filepath)
                    messagebox.showinfo("Éxito", f"Código QR guardado en:\n{filepath}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")


# --- Iniciar la aplicación ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AppGeneradorQR(root)
    root.mainloop()
