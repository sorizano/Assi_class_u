import pandas as pd
import numpy as np

class DataLoader:
    """Clase encargada de la carga y limpieza inicial de datos."""
    
    @staticmethod
    def clean_col_names(df):
        if df is not None:
            df.columns = df.columns.str.strip()
        return df

    @staticmethod
    def load_file(uploaded_file):
        if uploaded_file is None: return None
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                # Lógica para CSV con distintos encodings
                try: df = pd.read_csv(uploaded_file)
                except: 
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1', sep=';')
            return DataLoader.clean_col_names(df)
        except Exception as e:
            return pd.DataFrame() # Retorna vacío en error para no romper

    @staticmethod
    def get_summary(df, name):
        if df is None or df.empty: return {"Error": "No cargado o vacío"}
        return {
            "Nombre": name,
            "Filas": df.shape[0],
            "Cols_Preview": list(df.columns[:4]),
            "Nulos": df.isnull().sum().sum()
        }

def procesar_oferta(df_oferta):
    """
    1. Limpia tipos de datos numéricos.
    2. Calcula HORAS_TOTALES según el 'Tipo De Sección'.
    """
    # Evitar modificar el original directamente
    df = df_oferta.copy()
    
    # 1. Asegurar que Ht y Hp sean números (convertir errores a 0)
    cols_num = ['Ht', 'Hp']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    # 2. Lógica de Negocio: Cálculo de Horas
    def aplicar_regla_horas(row):
        tipo = str(row.get('Tipo De Sección', '')).strip().upper()
        ht = row['Ht']
        hp = row['Hp']
        
        if 'NORMAL' in tipo:
            return ht + hp
        elif 'TEORÍA' in tipo or 'TEORIA' in tipo:
            return ht
        elif 'PRÁCTICA' in tipo or 'PRACTICA' in tipo:
            return hp
        else:
            # Si está vacío o es otro tipo, por defecto sumamos (o puedes poner 0)
            return ht + hp

    df['HORAS_TOTALES'] = df.apply(aplicar_regla_horas, axis=1)
    
    # Creamos un ID único temporal para trackear el curso en el sistema
    # (Usamos código + sección si existe, sino solo código para referencia)
    if 'Codigo De Curso' in df.columns:
         df['key_curso'] = df['Codigo De Curso'].astype(str).str.strip().str.upper()
    
    return df

def detectar_restricciones_malla(df_oferta, df_malla):
    """
    Cruza la oferta (ya procesada con horas) con la malla para ver restricciones.
    """
    # Procesamos primero la oferta para tener las horas listas
    df_oferta_proc = procesar_oferta(df_oferta)
    
    # Preparar malla
    df_malla['key_curso'] = df_malla['COD ASIGNATURA'].astype(str).str.strip().str.upper()
    
    # --- Lógica de Agrupación de Malla (La que hicimos antes) ---
    malla_relevant = df_malla[['key_curso', 'PROGRAMA', 'CICLO', 'TIPO 4']].drop_duplicates()
    impacto_curso = {}
    
    for curso, grupo in malla_relevant.groupby('key_curso'):
        tipo_curso = grupo['TIPO 4'].iloc[0]
        lista_afectados = grupo[['PROGRAMA', 'CICLO']].to_dict('records')
        
        impacto_curso[curso] = {
            'Tipo_Malla': tipo_curso,
            'Afecta_A': lista_afectados,
            'Es_General': 'GENERAL' in str(tipo_curso).upper()
        }
    
    # --- Cruzar con Oferta ---
    resultados = []
    for idx, row in df_oferta_proc.iterrows():
        cod = row.get('key_curso', 'S/C')
        # Datos visuales
        info_base = {
            'Codigo': cod,
            'Curso': row.get('Nombre De Curso', ''),
            'Seccion': row.get('Sección Aperturado O Bloqueado', ''), # Útil para identificar
            'Ht': row['Ht'],
            'Hp': row['Hp'],
            'Tipo_Seccion': row.get('Tipo De Sección', ''),
            'Horas_Totales': row['HORAS_TOTALES'] # <--- DATO CLAVE NUEVO
        }
        
        # Buscar en diccionario de malla
        info_malla = impacto_curso.get(cod)
        
        if info_malla:
            info_base['Tipo_Detectado'] = 'GENERAL' if info_malla['Es_General'] else 'ESPECIALIDAD'
            info_base['Restricciones'] = info_malla['Afecta_A']
            info_base['Info_Malla'] = f"{len(info_malla['Afecta_A'])} carreras" if info_malla['Es_General'] else f"Ciclo {info_malla['Afecta_A'][0]['CICLO']}"
        else:
            info_base['Tipo_Detectado'] = 'NO ENCONTRADO'
            info_base['Restricciones'] = []
            info_base['Info_Malla'] = '-'
            
        resultados.append(info_base)
        
    return pd.DataFrame(resultados)