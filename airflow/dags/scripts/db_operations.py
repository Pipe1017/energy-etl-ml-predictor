# -*- coding: utf-8 -*-
# Archivo: scripts/db_operations.py

# --- INICIO CORRECCIÓN: Añadir importaciones faltantes ---
import logging # Para registrar mensajes
import pendulum # Para parsear fechas/horas desde strings
# --- FIN CORRECCIÓN ---

# Otras importaciones necesarias que ya deberían estar
from datetime import datetime
import numpy as np
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowNotFoundException, AirflowException

def insertar_registros_demanda(records: list[dict], postgres_conn_id: str):
    """
    Inserta una lista de registros de demanda en la tabla 'demanda_historico'.
    Incluye columnas: datetime, kwh, mes, hour, season, dia_habil.
    Utiliza INSERT ... ON CONFLICT (datetime) DO NOTHING.

    Args:
        records (list[dict]): Lista de diccionarios con las claves requeridas.
        postgres_conn_id (str): El ID de la conexión PostgreSQL.
    """
    if not records:
        logging.info("DB Ops: No hay registros para insertar.")
        return

    target_table = "demanda_historico"
    expected_keys = ['datetime', 'kwh', 'mes', 'hour', 'season', 'dia_habil']
    # Chequeo básico de claves (opcional pero útil)
    # if records and not all(key in records[0] for key in expected_keys):
    #      logging.warning(f"DB Ops: Los registros no parecen tener todas las claves esperadas ({expected_keys}). Primer registro: {records[0].keys()}")
         # raise ValueError("Formato de registro inesperado.")

    logging.info(f"DB Ops: Iniciando inserción de {len(records)} registros en tabla '{target_table}'...")

    try:
        hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    except AirflowNotFoundException:
         # Usar logging aquí ahora que está importado
         logging.error(f"DB Ops: Conexión de Airflow '{postgres_conn_id}' no encontrada.")
         raise ValueError(f"Conexión '{postgres_conn_id}' no encontrada.")

    insert_sql = f"""
        INSERT INTO {target_table} (datetime, kwh, mes, hour, season, dia_habil)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (datetime) DO NOTHING;
    """
    total_processed = 0
    error_count = 0

    # Iterar para insertar fila por fila
    for i, rec in enumerate(records): # Usar enumerate si necesitas el índice i
        total_processed += 1
        try:
            # Obtener nuevos valores
            ts_val = rec.get('datetime')
            kwh_val = rec.get('kwh')
            mes_val = rec.get('mes')
            hour_val = rec.get('hour')
            season_val = rec.get('season')
            dia_habil_val = rec.get('dia_habil')

            # Validaciones y Conversiones
            if ts_val is None or kwh_val is None or mes_val is None or hour_val is None or season_val is None or dia_habil_val is None:
                 logging.warning(f"DB Ops: Registro {total_processed} incompleto, saltando: {rec}")
                 error_count += 1; continue

            # Usar pendulum (ahora importado)
            if isinstance(ts_val, str):
                ts_val = pendulum.parse(ts_val)
            elif isinstance(ts_val, pd.Timestamp):
                 ts_val = ts_val.to_pydatetime()
            elif not isinstance(ts_val, datetime):
                 logging.error(f"DB Ops: Tipo inesperado para 'datetime' en reg {total_processed}: {type(ts_val)}")
                 error_count += 1; continue

            # KWH (permitir float si es NUMERIC en BD)
            if not isinstance(kwh_val, (int, float, np.number)):
                 try: kwh_val = float(kwh_val)
                 except (ValueError, TypeError) as conv_e:
                      logging.error(f"DB Ops: Error convirtiendo 'kwh' a float en reg {total_processed}: {kwh_val}. Error: {conv_e}")
                      error_count += 1; continue

            # Otros enteros
            try:
                 mes_val = int(mes_val)
                 hour_val = int(hour_val)
                 season_val = int(season_val)
                 dia_habil_val = int(dia_habil_val)
            except (ValueError, TypeError):
                 logging.error(f"DB Ops: Error convirtiendo valores adicionales a int en reg {total_processed}: {rec}")
                 error_count += 1; continue

            # Log de parámetros (como lo añadimos antes)
            # if i < 5 or i == len(records) - 1: # Loggear algunos ejemplos
            #    params_tuple = (ts_val, kwh_val, mes_val, hour_val, season_val, dia_habil_val)
            #    logging.info(f"DB Ops: Parámetros para hook.run (Registro {total_processed}): {params_tuple}")


            # Ejecutar la inserción
            hook.run(insert_sql, parameters=(ts_val, kwh_val, mes_val, hour_val, season_val, dia_habil_val))

        except Exception as e:
            # Usar logging (ahora importado)
            logging.info(f"DB Ops: Proceso de inserción en '{target_table}' completado. Registros procesados: {total_processed}, Errores/Saltados: {error_count}")
            error_count += 1

    logging.info(f"DB Ops: Proceso de inserción en '{target_table}' completado. Registros procesados: {total_processed}, Errores/Saltados: {error_count}")

    if error_count > 0:
        raise AirflowException(f"{error_count} de {total_processed} registros fallaron durante la inserción en '{target_table}'. Revisar logs.")