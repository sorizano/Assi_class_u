import streamlit as st
import pandas as pd
import logic  # Asegúrate de que logic.py esté en la misma carpeta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestor de Horarios Universitarios", 
    layout="wide", 
    page_icon="🎓"
)

st.title("🎓 Sistema Modular de Programación de Horarios")

# --- BARRA LATERAL: CARGA DE DATOS ---
with st.sidebar:
    st.header("📂 1. Carga de Archivos Base")
    st.markdown("---")
    
    files = {}
    files['oferta'] = st.file_uploader("Oferta Académica (Obligatorio)", type=['xlsx', 'csv'])
    files['malla'] = st.file_uploader("Malla Curricular (Obligatorio)", type=['xlsx', 'csv'])
    files['requerimientos'] = st.file_uploader("Requerimientos (Opcional)", type=['xlsx', 'csv'])
    files['aulas'] = st.file_uploader("Infraestructura/Aulas (Opcional)", type=['xlsx', 'csv'])
    files['disponibilidad'] = st.file_uploader("Disponibilidad Docente (Opcional)", type=['xlsx', 'csv'])

# --- PROCESAMIENTO GLOBAL ---
data_context = {}
archivos_cargados = False

# Cargamos todo lo que el usuario haya subido para el explorador
if any(files.values()):
    with st.spinner('Leyendo archivos...'):
        for name, file_obj in files.items():
            if file_obj:
                data_context[name] = logic.DataLoader.load_file(file_obj)
    archivos_cargados = True

# Verificamos si tenemos lo mínimo para la lógica avanzada
listo_para_procesar = 'oferta' in data_context and 'malla' in data_context and data_context['oferta'] is not None and data_context['malla'] is not None

# --- ESTRUCTURA DE PESTAÑAS ---
tab1, tab2, tab3 = st.tabs([
    "📂 Explorador de Datos", 
    "⏱️ Análisis de Carga (Horas)", 
    "🧬 Cruce con Malla (Restricciones)"
])

# --- PESTAÑA 1: EXPLORADOR DE ARCHIVOS ---
with tab1:
    st.subheader("Vista Previa de Archivos Cargados")
    if not archivos_cargados:
        st.info("👈 Sube tus archivos en el panel lateral para comenzar.")
    else:
        # Diseño en columnas para las tarjetas
        col1, col2 = st.columns(2)
        
        for idx, (name, df) in enumerate(data_context.items()):
            # Obtenemos resumen desde logic.py
            summary = logic.DataLoader.get_summary(df, name.upper())
            
            # Alternar columnas para visualización tipo tarjeta
            target_col = col1 if idx % 2 == 0 else col2
            
            with target_col:
                with st.expander(f"📄 {name.upper()} ({summary.get('Filas', 0)} filas)", expanded=False):
                    if "Error" in summary:
                        st.error(summary["Error"])
                    else:
                        st.dataframe(df.head(5), use_container_width=True)
                        st.caption(f"Columnas detectadas: {summary.get('Cols_Preview')}")
                        if summary.get('Nulos', 0) > 0:
                            st.warning(f"⚠️ {summary['Nulos']} celdas vacías detectadas.")

# --- LÓGICA DE NEGOCIO (Solo si hay Oferta y Malla) ---
if listo_para_procesar:
    # Ejecutamos la lógica central una sola vez
    df_resultado = logic.detectar_restricciones_malla(data_context['oferta'], data_context['malla'])

    # --- PESTAÑA 2: ANÁLISIS DE HORAS ---
    with tab2:
        st.subheader("Validación de Reglas de Negocio (Horas)")
        st.markdown("Verifica aquí que la suma de horas (Ht + Hp) según el 'Tipo de Sección' sea correcta.")
        
        # Métricas Generales
        total_horas = df_resultado['Horas_Totales'].sum()
        cursos_totales = len(df_resultado)
        promedio = df_resultado['Horas_Totales'].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Horas a Programar", f"{total_horas:,.0f}")
        m2.metric("Total Cursos/Secciones", cursos_totales)
        m3.metric("Promedio Horas x Curso", f"{promedio:.1f}")
        
        st.divider()
        
        # Tabla de Verificación
        st.write("🔍 **Tabla de Auditoría de Horas:**")
        cols_audit = ['Codigo', 'Curso', 'Tipo_Seccion', 'Ht', 'Hp', 'Horas_Totales']
        
        # Filtramos columnas que existan para evitar errores
        cols_existentes = [c for c in cols_audit if c in df_resultado.columns]
        
        st.dataframe(
            df_resultado[cols_existentes].head(100),
            use_container_width=True,
            height=400
        )

    # --- PESTAÑA 3: CRUCE CON MALLA ---
    with tab3:
        st.subheader("Restricciones Académicas Detectadas")
        st.markdown("""
        Esta tabla muestra cómo cada curso de la oferta impacta en los ciclos de la universidad.
        * **General:** Impacta a múltiples carreras (no debe cruzarse con ninguna).
        * **Especialidad:** Impacta a un ciclo específico de una carrera.
        """)
        
        # Filtros
        col_filtro, col_vacio = st.columns([1, 2])
        with col_filtro:
            tipos_disp = df_resultado['Tipo_Detectado'].unique()
            filtro = st.multiselect("Filtrar por Tipo:", tipos_disp, default=tipos_disp)
        
        # Aplicar filtro
        df_view = df_resultado[df_resultado['Tipo_Detectado'].isin(filtro)]
        
        # Definir columnas finales y colores
        cols_finales = ['Codigo', 'Curso', 'Tipo_Detectado', 'Horas_Totales', 'Info_Malla']
        cols_seguras = [c for c in cols_finales if c in df_view.columns]

        def color_tipo(val):
            if 'GENERAL' in str(val).upper():
                return 'background-color: #ffeeba; color: black' # Amarillo suave
            elif 'ESPECIALIDAD' in str(val).upper():
                return 'background-color: #d1e7dd; color: black' # Verde suave
            elif 'NO ENCONTRADO' in str(val).upper():
                return 'background-color: #f8d7da; color: black' # Rojo suave
            return ''

        # Mostrar Tabla
        try:
            st.dataframe(
                df_view[cols_seguras].style.map(color_tipo, subset=['Tipo_Detectado']),
                use_container_width=True,
                height=600
            )
        except Exception as e:
            st.error(f"Error al renderizar la tabla: {e}")
            st.dataframe(df_view[cols_seguras]) # Fallback sin estilos

elif archivos_cargados and not listo_para_procesar:
    with tab2:
        st.warning("⚠️ Necesitas cargar obligatoriamente **Oferta** y **Malla** para ver el análisis de horas.")
    with tab3:
        st.warning("⚠️ Necesitas cargar obligatoriamente **Oferta** y **Malla** para calcular los cruces.")

else:
    # Mensaje inicial cuando no hay nada
    pass