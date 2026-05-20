import streamlit as st
import pandas as pd
import io

# Configuración de la página: diseño más amplio y limpio
st.set_page_config(
    page_title="Gestor y Consultor de Datos", page_icon="📊", layout="wide"
)

st.title("📊 Gestor y Consultor de Datos")
st.write("Extrae, explora y realiza consultas sobre tus archivos Excel o CSV.")

# 1. Seleccionar Archivo (Ahora acepta Excel y CSV)
uploaded_file = st.file_uploader(
    "1. Carga un archivo (.xlsx o .csv)", type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        # Identificar el tipo de archivo cargado
        file_extension = uploaded_file.name.split(".")[-1]

        if file_extension == "xlsx":
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            selected_sheet = st.selectbox(
                "2. Seleccionar hoja de cálculo:", sheet_names
            )

            # Leer los datos de la hoja seleccionada
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            export_name = f"{selected_sheet}.csv"
        else:
            # Si es un CSV, lo leemos directamente
            df = pd.read_csv(uploaded_file)
            export_name = uploaded_file.name

        st.success("Archivo cargado y procesado correctamente.")

        # Crear dos columnas para mantener el diseño ordenado
        col1, col2 = st.columns([1, 1])

        with col1:
            # --- SECCIÓN DE EXPORTACIÓN ---
            st.subheader("⚙️ Exportación a CSV")
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="🚀 Descargar archivo .csv",
                data=csv_data,
                file_name=export_name,
                mime="text/csv",
            )

        st.divider()

        # --- SECCIÓN DE CONSULTAS ---
        st.subheader("🔍 Panel de Consultas")

        # A. Búsqueda rápida (Filtra en cualquier columna)
        search_term = st.text_input(
            "Búsqueda rápida (escribe para filtrar texto en cualquier columna):"
        )

        # B. Consultas Avanzadas (Oculto por defecto en un expander para mantener la UI limpia)
        with st.expander("🛠️ Consultas Avanzadas (Filtros matemáticos o lógicos)"):
            st.write("**Columnas disponibles para consultar:**")
            st.code(", ".join(list(df.columns)))
            st.info("Ejemplo de uso: `Precio > 50000` o `Estado == 'Activo'`")
            advanced_query = st.text_input("Escribe tu expresión de consulta:")

        # Aplicar los filtros sobre una copia de los datos
        filtered_df = df.copy()

        # Ejecutar búsqueda rápida
        if search_term:
            # Busca la coincidencia en todas las columnas convirtiéndolas a texto
            mask = (
                filtered_df.astype(str)
                .apply(lambda x: x.str.contains(search_term, case=False, na=False))
                .any(axis=1)
            )
            filtered_df = filtered_df[mask]

        # Ejecutar consulta avanzada
        if advanced_query:
            try:
                filtered_df = filtered_df.query(advanced_query)
            except Exception as e:
                st.error(
                    f"Error en la consulta avanzada. Revisa la sintaxis. Detalle: {e}"
                )

        # Mostrar la tabla interactiva con los resultados
        st.write(f"**Mostrando {len(filtered_df)} de {len(df)} registros totales.**")
        st.dataframe(filtered_df, use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los datos: {e}")
