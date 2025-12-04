import pandas as pd
import io

class DataLoader:
    """Clase encargada de la carga y limpieza inicial de datos."""
    
    @staticmethod
    def load_file(uploaded_file):
        """Intenta cargar un archivo ya sea CSV o Excel."""
        if uploaded_file is None:
            return None
        
        try:
            # Intentar leer como Excel primero si la extensión lo sugiere
            if uploaded_file.name.endswith('.xlsx'):
                return pd.read_excel(uploaded_file)
            else:
                # Si es CSV, probar diferentes codificaciones comunes en español
                try:
                    return pd.read_csv(uploaded_file)
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding='latin-1', sep=',')
                except pd.errors.ParserError:
                    # Intento final con punto y coma (común en Excel Latam)
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding='latin-1', sep=';')
                    
        except Exception as e:
            return f"Error al cargar: {str(e)}"

    @staticmethod
    def get_summary(df, name):
        """Genera un resumen estadístico básico del DataFrame."""
        if not isinstance(df, pd.DataFrame):
            return {"Error": "No se pudo procesar el archivo"}
            
        summary = {
            "Nombre": name,
            "Filas": df.shape[0],
            "Columnas": df.shape[1],
            "Columnas Clave Detectadas": list(df.columns[:5]), # Muestra las primeras 5 para validar
            "Datos Nulos": df.isnull().sum().sum()
        }
        return summary

def programar_horarios(data_context):
    """
    FUNCIÓN PRINCIPAL DEL ALGORITMO.
    Aquí irá toda la lógica de asignación de horarios.
    
    Args:
        data_context (dict): Diccionario con todos los DataFrames cargados:
                             {'oferta', 'requerimientos', 'aulas', 'disponibilidad', 'malla'}
    
    Returns:
        dict: Resultado de la programación (actualmente vacío).
    """
    
    # ---------------------------------------------------------
    # AQUÍ IMPLEMENTARÁS TU LÓGICA DE OPTIMIZACIÓN / HEURÍSTICA
    # ---------------------------------------------------------
    
    # Por ahora, solo retornamos un mensaje de éxito simulado
    print("Iniciando motor de programación...")
    print(f"Procesando {len(data_context)} archivos base.")
    
    return {
        "status": "Pendiente",
        "message": "La lógica de programación aún no ha sido implementada.",
        "input_stats": {k: v.shape for k, v in data_context.items() if isinstance(v, pd.DataFrame)}
    }