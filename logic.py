import pandas as pd

class DataLoader:
    """Clase encargada de la carga y limpieza inicial de datos."""
    
    @staticmethod
    def clean_col_names(df):
        """Elimina espacios en blanco al inicio/final de los nombres de columnas."""
        if df is not None:
            df.columns = df.columns.str.strip()
        return df

    @staticmethod
    def load_file(uploaded_file):
        """Carga inteligente de CSV/Excel."""
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
        """Genera resumen estadístico para el frontend."""
        if not isinstance(df, pd.DataFrame):
            return {"Error": str(df) if df else "No cargado"}
        
        return {
            "Nombre": name,
            "Filas": df.shape[0],
            "Columnas": df.shape[1],
            "Cols_Preview": list(df.columns[:5]),
            "Nulos": df.isnull().sum().sum()
        }

def detectar_restricciones_malla(df_oferta, df_malla):
    """
    Analiza qué cursos de la oferta afectan a qué carreras y ciclos.
    Maneja la lógica de '1 curso -> Múltiples Carreras' (Generales).
    """
    
    # 1. Normalizar claves
    df_oferta['key_curso'] = df_oferta['Codigo De Curso'].astype(str).str.strip().str.upper()
    df_malla['key_curso'] = df_malla['COD ASIGNATURA'].astype(str).str.strip().str.upper()
    
    # 2. Construir Diccionario de Impacto desde la Malla
    # Agrupamos la malla por código de curso para ver en cuántos programas aparece
    # Resultado esperado: { 'COD123': [{'Programa': 'Ingeniería', 'Ciclo': 1}, {'Programa': 'Derecho', 'Ciclo': 2}] }
    
    malla_relevant = df_malla[['key_curso', 'PROGRAMA', 'CICLO', 'TIPO 4']].drop_duplicates()
    
    impacto_curso = {}
    
    # Iteramos sobre los cursos únicos de la malla
    for curso, grupo in malla_relevant.groupby('key_curso'):
        tipo_curso = grupo['TIPO 4'].iloc[0] # Asumimos que el tipo (General/Esp) es constante para el código
        
        lista_afectados = []
        for _, row in grupo.iterrows():
            lista_afectados.append({
                'Programa': row['PROGRAMA'],
                'Ciclo': row['CICLO']
            })
            
        impacto_curso[curso] = {
            'Tipo_Malla': tipo_curso,
            'Afecta_A': lista_afectados,
            'Es_General': 'GENERAL' in str(tipo_curso).upper() or 'TRANSVERSAL' in str(tipo_curso).upper()
        }
        
    # 3. Aplicar esto a la Oferta
    resultados = []
    
    for _, row in df_oferta.iterrows():
        cod = row['key_curso']
        nombre = row.get('Nombre De Curso', 'Sin Nombre')
        carrera_oferta = row.get('Carrera', 'Desconocida')
        
        info_malla = impacto_curso.get(cod)
        
        if not info_malla:
            # Caso: Curso nuevo o electivo no encontrado en malla base
            resultados.append({
                'Codigo': cod,
                'Nombre': nombre,
                'Tipo_Detectado': 'NO ENCONTRADO EN MALLA',
                'Restriccion_Principal': f"Solo carrera oferta: {carrera_oferta}",
                'Detalle_Impacto': []
            })
        else:
            es_general = info_malla['Es_General']
            afecta = info_malla['Afecta_A']
            
            # Lógica Crucial:
            # Si es ESPECIALIDAD: Solo nos importa que no cruce con SU carrera y SU ciclo.
            # Si es GENERAL: No debe cruzar con NINGUNA de las carreras/ciclos donde se dicta.
            
            if es_general:
                desc = f"GENERAL: Impacta a {len(afecta)} programas"
            else:
                # Si es especialidad, filtramos para quedarnos con la carrera que dice la oferta
                # (A veces un código se recicla, pero en especialidad suele ser único)
                desc = f"ESPECIALIDAD: {afecta[0]['Programa']} - Ciclo {afecta[0]['Ciclo']}"
            
            resultados.append({
                'Codigo': cod,
                'Nombre': nombre,
                'Tipo_Detectado': 'GENERAL/TRANSVERSAL' if es_general else 'ESPECIALIDAD',
                'Restriccion_Visual': desc,
                'Data_Raw': afecta # Esto servirá para el algoritmo matemático luego
            })
            
    return pd.DataFrame(resultados)