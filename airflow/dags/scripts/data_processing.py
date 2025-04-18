# -*- coding: utf-8 -*-
# Archivo: scripts/data_processing.py

import pandas as pd
import logging
import numpy as np # Importar numpy para chequeo de tipos

def transformar_dataframe_demanda(df: pd.DataFrame | None) -> list[dict]:
    """
    Toma el DataFrame procesado por extraer_demanda y lo prepara
    para la inserción en la base de datos, devolviendo una lista de diccionarios.
    Incluye columnas adicionales: mes, hour, season, dia_habil.
    Convierte las fechas a strings ISO 8601 para serialización JSON.

    Args:
        df (pd.DataFrame | None): El DataFrame con 'Datetime' como índice y
                                   columnas: 'kWh', 'Mes', 'Hour', 'Season', 'Dia_habil'.

    Returns:
        list[dict]: Lista de diccionarios con claves 'datetime', 'kwh', 'mes',
                    'hour', 'season', 'dia_habil'. Lista vacía si hay errores.
    """
    if df is None or df.empty:
        logging.info("Transformación: DataFrame de entrada vacío o None.")
        return []

    try:
        logging.info(f"Transformación: Iniciando con DataFrame de {df.shape[0]} filas. Columnas originales: {df.columns.tolist()}")
        # 1. Mover 'Datetime' del índice a una columna
        # Asegurarse que el índice se llama 'Datetime' como lo genera extraer_demanda
        if df.index.name == 'Datetime':
             df_processed = df.reset_index()
        else:
             logging.warning(f"Transformación: El índice no se llama 'Datetime' (se llama '{df.index.name}'). Intentando resetear de todas formas.")
             # Si el índice no tiene nombre, reset_index crea 'index'. Si tiene otro nombre, usa ese.
             # Esto podría ser una fuente de error si el índice no es el esperado.
             df_processed = df.reset_index()


        # 2. Renombrar columnas a formato esperado (minúsculas)
        column_rename_map = {
            'Datetime': 'datetime', # Viene del índice reseteado
            'kWh': 'kwh',
            'Mes': 'mes',
            'Hour': 'hour',
            'Season': 'season',
            'Dia_habil': 'dia_habil'
            # Añadir 'index': 'datetime' por si reset_index() no encontró 'Datetime'
             #'index': 'datetime' # Descomentar si sospechas que el índice no tenía nombre
        }
        # Renombrar solo las columnas que existen en df_processed
        actual_rename_map = {k: v for k, v in column_rename_map.items() if k in df_processed.columns}
        df_processed = df_processed.rename(columns=actual_rename_map)
        logging.info(f"Transformación: Columnas después de renombrar: {df_processed.columns.tolist()}")


        # 3. Definir y verificar columnas requeridas *después* de renombrar
        required_cols = ['datetime', 'kwh', 'mes', 'hour', 'season', 'dia_habil']
        missing_cols = [col for col in required_cols if col not in df_processed.columns]

        if missing_cols:
            # ¡Error Crítico! Si faltan columnas después de renombrar, algo falló antes.
            logging.error(f"Transformación: Faltan columnas requeridas después del renombrado: {missing_cols}. No se puede continuar.")
            return [] # Devolver lista vacía porque faltan datos esenciales.


        # 4. Seleccionar solo las columnas requeridas *antes* de cualquier conversión
        df_final = df_processed[required_cols].copy()


        # --- INICIO DEBUG LOGGING ---
        # Verificar tipos y valores nulos ANTES de la conversión final
        logging.info("Transformación: Info del DataFrame ANTES de conversión a dict:")
        df_final.info(verbose=True, show_counts=True) # Muestra tipos y conteo de no-nulos
        # Verificar si hay NaNs inesperados en columnas numéricas
        nan_check = df_final[['kwh', 'mes', 'hour', 'season', 'dia_habil']].isnull().sum()
        logging.info(f"Transformación: Conteo de NaNs por columna numérica: \n{nan_check}")
        # Mostrar las primeras filas para inspección visual
        logging.info("Transformación: Primeras 5 filas ANTES de conversión a dict:")
        try:
            logging.info("\n" + df_final.head().to_string()) # to_string para mejor formato en logs
        except Exception as log_e:
            logging.warning(f"No se pudieron loggear las primeras filas: {log_e}")
        # --- FIN DEBUG LOGGING ---


        # 5. Convertir la columna 'datetime' a string ISO 8601
        # Esto DEBE hacerse después de la selección y ANTES de to_dict
        logging.info("Transformación: Convirtiendo columna 'datetime' a string ISO 8601...")
        df_final['datetime'] = df_final['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S')



        # 6. Convertir a lista de diccionarios
        # Pandas puede convertir NaN a None durante esta operación
        records = df_final.to_dict(orient='records')
        logging.info(f"Transformación: Completada. {len(records)} registros generados.")

        # Opcional: Loggear el primer registro generado para ver su estructura final
        if records:
            logging.info(f"Transformación: Ejemplo del primer registro generado: {records[0]}")

        return records

    except Exception as e:
        logging.error(f"Transformación: Error procesando DataFrame: {e}", exc_info=True)
        return []