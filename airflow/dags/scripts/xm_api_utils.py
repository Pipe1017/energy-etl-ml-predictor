# -*- coding: utf-8 -*-
# Archivo: scripts/xm_api_utils.py

import datetime as dt
import pandas as pd
import numpy as np
from pydataxm import pydataxm
from workalendar.america import Colombia
import logging

# Configuración básica de logging (si no está configurado globalmente)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_medellin_season_numeric(month: int) -> int:
    """Determina la estación climática numérica."""
    if month in [12, 1, 2, 3]: return 1
    elif month in [4, 5, 6]: return 2
    elif month in [7, 8]: return 3
    else: return 4

def extraer_demanda(fecha_inicio: dt.date, fecha_fin: dt.date) -> pd.DataFrame | None:
    """Extrae datos de demanda para un rango de fechas."""
    logging.info(f"API Call: Extrayendo demanda para {fecha_inicio} a {fecha_fin}")
    try:
        objetoAPI = pydataxm.ReadDB()
        df_demanda = objetoAPI.request_data("DemaReal", "Sistema", fecha_inicio, fecha_fin)

        if df_demanda is None or df_demanda.empty:
            logging.warning(f"API Call: No se obtuvieron datos para {fecha_inicio} a {fecha_fin}")
            return None
        logging.info(f"API Call: Datos crudos obtenidos ({df_demanda.shape[0]} filas).")

        # --- Procesamiento Básico dentro de la extracción ---
        df_melted = pd.melt(
            df_demanda, id_vars=['Date'],
            value_vars=[col for col in df_demanda.columns if col.startswith('Values_Hour')],
            var_name='Hora_str', value_name='kWh'
        )
        df_melted['kWh'] = pd.to_numeric(df_melted['kWh'], errors='coerce')
        df_melted.dropna(subset=['kWh'], inplace=True)
        if df_melted.empty: return None

        df_melted['Hora_num_1_24'] = df_melted['Hora_str'].str.extract(r'(\d+)').astype(int)
        df_melted['Datetime'] = pd.to_datetime(df_melted['Date']) + pd.to_timedelta(df_melted['Hora_num_1_24'] - 1, unit='h')

        cal = Colombia()
        df_melted['Dia_habil'] = df_melted['Datetime'].apply(lambda x: 1 if (x.weekday() < 5 and cal.is_working_day(x.date())) else 0)

        df_modelo = df_melted[['Datetime', 'kWh', 'Dia_habil']].copy()
        df_modelo['Mes'] = df_modelo['Datetime'].dt.month
        df_modelo['Hour'] = df_modelo['Datetime'].dt.hour
        df_modelo['Season'] = df_modelo['Mes'].apply(get_medellin_season_numeric)
        df_modelo['kWh'] = df_modelo['kWh'].round(0).astype(np.int64)
        df_modelo = df_modelo[['Datetime', 'Mes', 'Hour', 'Season', 'Dia_habil', 'kWh']]
        df_modelo = df_modelo.sort_values('Datetime').set_index('Datetime')
        logging.info(f"API Call: Procesamiento inicial completado ({df_modelo.shape[0]} filas).")
        return df_modelo
    except Exception as e:
        logging.error(f"API Call: Error durante extracción/procesamiento: {e}", exc_info=True)
        return None