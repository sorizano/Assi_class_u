import streamlit as st
import pandas as pd
import logic

st.set_page_config(page_title="Generador de Horarios", layout="wide")

st.title("🎓 Sistema de Programación - Módulo de Integración")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    file_oferta = st.file_uploader("1. Oferta Académica", type=['xlsx', 'csv'])
    file_malla = st.file_uploader("5. Plan de Estudios (Malla)", type=['xlsx', 'csv'])
    # (Omito los otros inputs por brevedad, pero deberían estar si vas a cargar todo)
    st.info("Para esta prueba, necesitamos obligatoriamente Oferta y Malla.")

# --- LÓGICA ---
if file_oferta and file_malla:
    data_context = {}
    
    with st.spinner('Cargando archivos...'):
        data_context['oferta'] = logic.DataLoader.load_file(file_oferta)
        data_context['malla'] = logic.DataLoader.load_file(file_malla)
        
    st.success(f"Archivos cargados: Oferta ({len(data_context['oferta'])}) y Malla ({len(data_context['malla'])})")
    
    if st.button("🔄 Ejecutar Cruce Oferta-Malla"):
        resultado = logic.programar_horarios(data_context)
        
        st.subheader("Resultados del Procesamiento")
        
        # 1. Métricas
        if "full_data_stats" in resultado:
            st.write("Distribución de cursos detectada:")
            cols = st.columns(len(resultado["full_data_stats"]))
            for idx, (label, count) in enumerate(resultado["full_data_stats"].items()):
                cols[idx].metric(label, count)
        
        # 2. Tabla de Datos
        if "data_preview" in resultado:
            st.write("Vista previa de los datos enriquecidos (con Ciclo y Tipo):")
            df_res = pd.DataFrame(resultado["data_preview"])
            st.dataframe(df_res, use_container_width=True)
            
            # Validación visual
            st.caption("Verifica en la tabla de arriba que la columna 'TIPO_CALCULADO' coincida con tu lógica de negocio.")
            
else:
    st.warning("Por favor carga al menos 'Oferta' y 'Malla' para probar la lógica.")