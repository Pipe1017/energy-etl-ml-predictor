# -*- coding: utf-8 -*-
# Archivo: scripts/db_operations_prediction.py
"""Utilidades concisas para insertar predicciones en PostgreSQL."""

import logging
from datetime import datetime # Necesario para isinstance

import pendulum # Para parsear ISO ts robustamente
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Tabla destino en la base de datos
TARGET_TABLE = "demanda_prediccion"

def insert_predictions(predictions_list: list[dict], prediction_run_ts_iso: str, postgres_conn_id: str):
    """
    Inserta predicciones en la tabla `demanda_prediccion`.
    Parsea correctamente los timestamps string ISO 8601 de XCom.
    """
    if not predictions_list:
        logging.info("DB Ops: No hay predicciones para insertar.")
        return

    logging.info(f"DB Ops: Insertando {len(predictions_list)} predicciones en '{TARGET_TABLE}'...")
    try:
        hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        # Parsea el timestamp de ejecución del DAG (viene de {{ ts }})
        # El resultado es un objeto pendulum.DateTime
        run_ts = pendulum.parse(prediction_run_ts_iso)
        # NO es necesaria la conversión explícita a datetime estándar
        # run_ts_std = run_ts.to_pydatetime() # <-- Eliminado
    except Exception as e:
        logging.error(f"DB Ops: Error inicializando Hook o parseando run_ts: {e}", exc_info=True)
        raise AirflowException(f"Fallo inicialización DB Ops: {e}")

    # Prepara datos para insert_rows: lista de tuplas (run_ts, pred_for_ts, kwh, version)
    rows_to_insert = []
    fields = ['prediction_run_ts', 'prediction_for_datetime', 'predicted_kwh', 'model_version']

    # --- Bucle Simplificado y Corregido ---
    for pred_dict in predictions_list:
        pred_for_dt_input = pred_dict.get('prediction_for_datetime')
        processed_dt = None  # Variable para guardar el objeto datetime/pendulum

        if isinstance(pred_for_dt_input, str):
            # CASO ESPERADO: El input es un string ISO 8601 desde XCom
            try:
                # Parsear el string a objeto Pendulum. NO se necesita .to_pydatetime()
                processed_dt = pendulum.parse(pred_for_dt_input)
            except Exception as e:
                logging.warning(
                    f"DB Ops: Skip record, fallo al parsear string de fecha: '{pred_for_dt_input}'. Error: {e}"
                )
                continue  # Saltar al siguiente registro si falla el parseo
        elif isinstance(pred_for_dt_input, (pendulum.DateTime, datetime)):
            # Caso defensivo: si por alguna razón ya es un objeto datetime/pendulum
            processed_dt = pred_for_dt_input
        else:
            # Caso inesperado: el tipo no es manejable
            logging.warning(
                f"DB Ops: Skip record, tipo inesperado para prediction_for_datetime: "
                f"{type(pred_for_dt_input)}. Valor: {pred_for_dt_input}"
            )
            continue # Saltar tipos inesperados

        # Crear la tupla si el datetime fue procesado correctamente
        if processed_dt:
            row = (
                run_ts,                 # Usar el objeto Pendulum directamente
                processed_dt,           # Usar el objeto Pendulum/datetime procesado directamente
                pred_dict.get('predicted_kwh'),
                pred_dict.get('model_version')
            )
            rows_to_insert.append(row)
        else:
             logging.warning(f"DB Ops: No se pudo procesar la fecha (processed_dt es None), no se añadirá fila.")
    # --- FIN DEL BUCLE ---

    logging.info(f"DB Ops: Fin del bucle. {len(rows_to_insert)} filas listas para insertar.")

    if not rows_to_insert:
         logging.warning("DB Ops: No quedaron filas válidas para insertar.")
         return

    # Inserta las filas en batch
    try:
        logging.info(f"DB Ops: Intentando insertar {len(rows_to_insert)} filas...")
        hook.insert_rows(
            table=TARGET_TABLE, rows=rows_to_insert, target_fields=fields,
            commit_every=1000 # Ajusta tamaño del batch según necesidad
        )
        logging.info(f"DB Ops: Inserción completada.")
    except Exception as e:
        # Si falla aquí, podría ser un problema de tipo de dato con psycopg2 a pesar de la subclase
        # o un problema con la BD (constraint, conexión, etc.)
        logging.error(f"DB Ops: Error en hook.insert_rows tabla '{TARGET_TABLE}': {e}", exc_info=True)
        raise AirflowException(f"Fallo inserción de predicciones: {e}")