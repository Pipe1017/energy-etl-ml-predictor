# -*- coding: utf-8 -*-
# Archivo: scripts/db_operations_prediction.py
"""Utilidades concisas para insertar predicciones en PostgreSQL."""

import logging
from datetime import datetime
from typing import List, Dict

import pendulum
from airflow.exceptions import AirflowException
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Table, MetaData

# Tabla destino en la base de datos
TARGET_TABLE = "demanda_prediccion"

def insert_predictions(
    predictions_list: List[Dict], 
    prediction_run_ts_iso: str, 
    postgres_conn_id: str
) -> None:
    """
    Inserta predicciones usando UPSERT para manejar duplicados.
    Actualiza registros existentes con nuevos valores.
    """
    if not predictions_list:
        logging.info("DB Ops: No hay predicciones para insertar.")
        return

    logging.info(f"DB Ops: Procesando {len(predictions_list)} predicciones...")

    try:
        hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        engine = hook.get_sqlalchemy_engine()
        metadata = MetaData()
        
        # Reflect table from database
        metadata.reflect(bind=engine, only=[TARGET_TABLE])
        table = Table(TARGET_TABLE, metadata)
        
        run_ts = pendulum.parse(prediction_run_ts_iso)

    except Exception as e:
        logging.error(f"DB Ops: Error inicializando recursos: {e}", exc_info=True)
        raise AirflowException(f"Fallo inicialización DB Ops: {e}")

    processed_rows = []
    for pred in predictions_list:
        try:
            dt = pendulum.parse(pred['prediction_for_datetime'])
            processed_rows.append({
                "prediction_run_ts": run_ts,
                "prediction_for_datetime": dt,
                "predicted_kwh": pred['predicted_kwh'],
                "model_version": pred['model_version']
            })
        except Exception as e:
            logging.warning(f"Error procesando fila: {pred} - {e}")

    if not processed_rows:
        logging.warning("DB Ops: No quedaron filas válidas para insertar.")
        return

    try:
        # UPSERT usando SQLAlchemy
        stmt = insert(table).values(processed_rows)
        
        update_stmt = stmt.on_conflict_do_update(
            constraint='demanda_prediccion_pkey',
            set_={
                "predicted_kwh": stmt.excluded.predicted_kwh,
                "model_version": stmt.excluded.model_version,
                "prediction_run_ts": stmt.excluded.prediction_run_ts
            }
        )

        with engine.connect() as conn:
            with conn.begin():  # <-- Contexto de transacción
                conn.execute(update_stmt)
            
        logging.info(f"DB Ops: UPSERT completado. {len(processed_rows)} registros procesados.")

    except Exception as e:
        logging.error(f"DB Ops: Error en operación UPSERT: {e}", exc_info=True)
        raise AirflowException(f"Fallo en UPSERT: {e}")