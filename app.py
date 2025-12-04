import streamlit as st
import pandas as pd
import logic

st.set_page_config(page_title="Gestor de Horarios", layout="wide", page_icon="📅")

st.title("📅 Sistema Modular de Programación de Horarios")

# --- SIDEBAR: Carga de Archivos ---
with st.sidebar:
    st.header("1. Carga de Datos")
    st.markdown("Sube los archivos necesarios para construir el modelo.")
    
    files = {}
    files['oferta'] = st.file_uploader("Oferta Académica", type=['xlsx', 'csv'])
    files['requerimientos'] = st.file_uploader("Requerimientos", type=['xlsx', 'csv'])
    files['aulas'] = st.file_uploader("Aulas / Infraestructura", type=['xlsx', 'csv'])
    files['disponibilidad'] = st.file_uploader("Disponibilidad Docente", type=['xlsx', 'csv'])
    files['malla'] = st.file_uploader("Malla Curricular", type=['xlsx', 'csv'])

# --- PROCESAMIENTO INICIAL ---
data_context = {}
loaded = False

if all(files.values()):
    with st.spinner('Procesando archivos base...'):
        for name, file in files.items():
            data_context[name] = logic.DataLoader.load_file(file)
    loaded = True
    st.success("Archivos cargados correctamente en memoria.")

# --- INTERFAZ PRINCIPAL (TABS) ---
tab1, tab2 = st.tabs(["📂 Explorador de Archivos", "🧠 Lógica de Cruces (Malla)"])

with tab1:
    if not loaded:
        st.info("Sube todos los archivos en el menú lateral para ver el resumen.")
    else:
        st.subheader("Resumen de Datos Cargados")
        col1, col2 = st.columns(2)
        
        # Iteramos para mostrar tarjetas bonitas como pediste
        for idx, (name, df) in enumerate(data_context.items()):
            summary = logic.DataLoader.get_summary(df, name.upper())
            
            # Distribuimos en dos columnas
            target_col = col1 if idx % 2 == 0 else col2
            
            with target_col:
                with st.expander(f"📄 {name.upper()} ({summary.get('Filas',0)} filas)", expanded=False):
                    if "Error" in summary:
                        st.error(summary["Error"])
                    else:
                        st.dataframe(df.head(3), use_container_width=True)
                        st.caption(f"Columnas detectadas: {summary['Cols_Preview']}...")
                        if summary['Nulos'] > 0:
                            st.warning(f"⚠️ {summary['Nulos']} datos nulos detectados")

with tab2:
    st.header("Definición de Restricciones por Ciclo")
    st.markdown("""
    Aquí cruzamos la **Oferta** con la **Malla**.
    * **Especialidad:** Se valida ciclo único.
    * **Generales:** Se identifican TODAS las carreras afectadas para evitar choques en cualquiera de ellas.
    """)
    
    if loaded:
        if st.button("🔄 Ejecutar Análisis de Cruces"):
            df_analisis = logic.detectar_restricciones_malla(data_context['oferta'], data_context['malla'])
            
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Cursos Oferta", len(df_analisis))
            c2.metric("Cursos Generales/Transversales", len(df_analisis[df_analisis['Tipo_Detectado'].str.contains('GENERAL')]))
            c3.metric("Cursos Especialidad", len(df_analisis[df_analisis['Tipo_Detectado'] == 'ESPECIALIDAD']))
            
            st.divider()
            
            # Mostrar tabla interactiva
            st.subheader("Detalle de Impacto por Curso")
            
            # Agregamos color para diferenciar visualmente
            def color_tipo(val):
                color = '#ffeba8' if 'GENERAL' in val else '#ccedff'
                return f'background-color: {color}'

            st.dataframe(
                df_analisis[['Codigo', 'Nombre', 'Tipo_Detectado', 'Restriccion_Visual']].style.map(color_tipo, subset=['Tipo_Detectado']),
                use_container_width=True,
                height=500
            )
            
            # Debugger: Ver data cruda de un curso
            st.divider()
            st.write("🕵️‍♂️ Inspector de Restricciones (Data cruda para el algoritmo)")
            curso_select = st.selectbox("Selecciona un curso para ver sus restricciones detalladas:", df_analisis['Codigo'].unique())
            datos_raw = df_analisis[df_analisis['Codigo'] == curso_select]['Data_Raw'].iloc[0]
            st.json(datos_raw)

    else:
        st.warning("Carga los archivos primero.")