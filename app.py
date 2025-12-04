import streamlit as st
import pandas as pd
import logic  # Importamos nuestro módulo de lógica

# Configuración de la página
st.set_page_config(page_title="Generador de Horarios Universitarios", layout="wide")

st.title("🎓 Sistema de Programación de Horarios")
st.markdown("""
Sube los archivos requeridos para iniciar el análisis y la programación.
""")

# --- SECCIÓN LATERAL: CARGA DE ARCHIVOS ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    
    file_oferta = st.file_uploader("1. Oferta Académica (oferta)", type=['xlsx', 'csv'])
    file_reqs = st.file_uploader("2. Requerimientos (requerimientos)", type=['xlsx', 'csv'])
    file_aulas = st.file_uploader("3. Infraestructura (aulas)", type=['xlsx', 'csv'])
    file_disp = st.file_uploader("4. Disponibilidad Docente (disponibilidad)", type=['xlsx', 'csv'])
    file_malla = st.file_uploader("5. Plan de Estudios (malla)", type=['xlsx', 'csv'])

# --- LÓGICA DE PROCESAMIENTO ---

# Diccionario para almacenar los dataframes
data_context = {}

# Verificamos si los archivos están cargados y los procesamos
if file_oferta and file_reqs and file_aulas and file_disp and file_malla:
    
    st.success("✅ Todos los archivos han sido cargados. Analizando estructura...")
    
    # Cargamos los datos usando el módulo logic.py
    with st.spinner('Procesando archivos...'):
        data_context['oferta'] = logic.DataLoader.load_file(file_oferta)
        data_context['requerimientos'] = logic.DataLoader.load_file(file_reqs)
        data_context['aulas'] = logic.DataLoader.load_file(file_aulas)
        data_context['disponibilidad'] = logic.DataLoader.load_file(file_disp)
        data_context['malla'] = logic.DataLoader.load_file(file_malla)

    # --- PESTAÑAS DE VISUALIZACIÓN ---
    tab1, tab2 = st.tabs(["📊 Resumen de Datos", "⚙️ Motor de Programación"])

    with tab1:
        st.subheader("Análisis de Archivos Cargados")
        
        # Crear columnas para mostrar métricas
        col1, col2, col3 = st.columns(3)
        
        # Iterar sobre los datos cargados para mostrar tarjetas de resumen
        for idx, (key, df) in enumerate(data_context.items()):
            summary = logic.DataLoader.get_summary(df, key)
            
            # Usar un contenedor expandible para cada archivo
            with st.expander(f"Archivo: {key.upper()} ({summary.get('Filas', 0)} registros)", expanded=(idx==0)):
                if "Error" in summary:
                    st.error(summary["Error"])
                else:
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        st.metric("Filas", summary["Filas"])
                        st.metric("Columnas", summary["Columnas"])
                    with c2:
                        st.write("**Columnas detectadas:**")
                        st.code(str(summary["Columnas Clave Detectadas"]))
                        st.warning(f"Celdas vacías detectadas: {summary['Datos Nulos']}")
                    
                    st.write("Vista Previa:")
                    st.dataframe(df.head(3), use_container_width=True)

    with tab2:
        st.subheader("Ejecución del Algoritmo")
        st.info("Presiona el botón para iniciar la lógica de programación (aún vacía).")
        
        if st.button("🚀 Programar Horarios"):
            # Llamada a la función modular en logic.py
            resultado = logic.programar_horarios(data_context)
            
            st.json(resultado)
            st.balloons()

else:
    st.info("👈 Por favor, carga los 5 archivos requeridos en la barra lateral para continuar.")

# Footer simple
st.markdown("---")
st.caption("Sistema Modular de Horarios v1.0")