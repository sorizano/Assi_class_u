import pandas as pd
import numpy as np

class DataLoader:
    """Clase encargada de la carga y limpieza inicial de datos."""
    
    @staticmethod
    def clean_col_names(df):
        """Elimina espacios en blanco al inicio/final de los nombres de columnas."""
        df.columns = df.columns.str.strip()
        return df

    @staticmethod
    def load_file(uploaded_file):
        if uploaded_file is None:
            return None
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                try:
                    df = pd.read_csv(uploaded_file)
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1', sep=',')
                except pd.errors.ParserError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1', sep=';')
            
            return DataLoader.clean_col_names(df)
        except Exception as e:
            return f"Error al cargar: {str(e)}"

    @staticmethod
    def get_summary(df, name):
        if not isinstance(df, pd.DataFrame):
            return {"Error": "No se pudo procesar el archivo"}
        return {
            "Nombre": name,
            "Filas": df.shape[0],
            "Columnas Clave": list(df.columns[:5])
        }

def procesar_oferta_con_malla(df_oferta, df_malla):
    """
    Cruza la oferta con la malla para determinar tipo de curso y ciclo.
    """
    # 1. Estandarización de claves para el cruce (Join)
    # Convertimos a string y quitamos espacios para evitar fallos por formato " 24UC..."
    df_oferta['key_curso'] = df_oferta['Codigo De Curso'].astype(str).str.strip().str.upper()
    df_malla['key_curso'] = df_malla['COD ASIGNATURA'].astype(str).str.strip().str.upper()
    
    # 2. Preparamos la malla para el cruce
    # Seleccionamos solo columnas necesarias para no ensuciar la oferta
    # Nota: Es posible que un curso esté repetido en malla (varios planes), 
    # por ahora quitamos duplicados de código para traer la info base.
    # EN EL FUTURO: Podríamos necesitar cruzar también por 'Plan' si los atributos cambian.
    cols_malla = ['key_curso', 'TIPO 4', 'PROGRAMA', 'CICLO']
    malla_unica = df_malla[cols_malla].drop_duplicates(subset=['key_curso'], keep='first')
    
    # 3. Realizamos el cruce (Left Join: Mantenemos toda la oferta, traemos info de malla)
    df_merge = pd.merge(
        df_oferta, 
        malla_unica, 
        on='key_curso', 
        how='left'
    )
    
    # 4. Lógica de Negocio: Clasificación de Cursos
    def clasificar_curso(row):
        # Si no cruzó con malla, no podemos saber (retornamos alerta)
        if pd.isna(row['TIPO 4']):
            return "NO ENCONTRADO EN MALLA"
        
        tipo_4 = str(row['TIPO 4']).upper()
        programa_malla = str(row['PROGRAMA']).upper()
        
        # Lógica solicitada por el usuario
        if tipo_4.startswith("GENERAL"):
            return "GENERAL"
        elif tipo_4 == programa_malla:
            return "ESPECIALIDAD"
        else:
            return "OTRO / TRANSVERSAL"

    df_merge['TIPO_CALCULADO'] = df_merge.apply(clasificar_curso, axis=1)
    
    # Limpieza final de columnas auxiliares
    df_merge.drop(columns=['key_curso'], inplace=True)
    
    return df_merge

def programar_horarios(data_context):
    """
    Motor principal.
    """
    print("Iniciando integración de datos...")
    
    df_oferta = data_context.get('oferta')
    df_malla = data_context.get('malla')
    
    if df_oferta is None or df_malla is None:
        return {"error": "Faltan archivos oferta o malla"}

    # --- PASO 1: ENRIQUECER OFERTA CON DATOS DE MALLA ---
    df_procesado = procesar_oferta_con_malla(df_oferta, df_malla)
    
    # Seleccionamos columnas relevantes para mostrar en el resumen
    cols_mostrar = [
        'Carrera', 'Codigo De Curso', 'Nombre De Curso', 
        'CICLO', 'TIPO_CALCULADO', 'TIPO 4', 'Plan'
    ]
    
    # Filtramos para mostrar solo las que existen (por si acaso cambian nombres)
    cols_finales = [c for c in cols_mostrar if c in df_procesado.columns]
    
    return {
        "status": "Procesado",
        "message": "Cruce Oferta vs Malla completado.",
        "data_preview": df_procesado[cols_finales].head(10).to_dict(orient='records'),
        "full_data_stats": df_procesado['TIPO_CALCULADO'].value_counts().to_dict()
    }