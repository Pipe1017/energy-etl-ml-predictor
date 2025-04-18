# -*- coding: utf-8 -*-
# Archivo: dags/db_demanda_predictions.py
"""DAG para predicción semanal de demanda con LSTM."""

import logging
import os
from datetime import timedelta

import pandas as pd
import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Intenta importar funciones locales; define placeholders si falla.
try:
    from scripts.prediction_utils import (create_prediction_output,
                                            generate_predictions,
                                            load_model_and_scalers,
                                            prepare_prediction_input)
    from scripts.db_operations_prediction import insert_predictions
except ImportError as e:
    logging.error(f"Error importando scripts locales: {e}. Revisa PYTHONPATH.")
    # Placeholders para que Airflow parsee el DAG
    def load_model_and_scalers(*args, **kwargs): raise NotImplementedError("Script no importado")
    def prepare_prediction_input(*args, **kwargs): raise NotImplementedError("Script no importado")
    def generate_predictions(*args, **kwargs): raise NotImplementedError("Script no importado")
    def create_prediction_output(*args, **kwargs): raise NotImplementedError("Script no importado")
    def insert_predictions(*args, **kwargs): raise NotImplementedError("Script no importado")


# --- Constantes ---
POSTGRES_CONN_ID = "app_postgres"
MINIO_CONN_ID = "minio_storage"
S3_BUCKET = "modelo-demanda-lstm"
MODEL_KEY = "lstm_demand_model.keras"
FEATURE_SCALER_KEY = "feature_scaler.joblib"
TARGET_SCALER_KEY = "target_scaler.joblib"
MODEL_VERSION = "lstm_v1"
WINDOW_SIZE = 336  # Horas históricas requeridas (14 días)
PREDICTION_HORIZON = 168 # Horas a predecir (7 días)
LOCAL_ARTIFACT_PATH = "/tmp/pred_artifacts" # Dir temporal en worker

# --- Argumentos Default DAG ---
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# --- Definición del DAG ---
@dag(
    dag_id="prediccion_demanda_semanal_conciso",
    schedule="0 3 * * 0", # Domingos 3:00 AM (Zona Horaria Airflow)
    start_date=pendulum.datetime(2024, 4, 1, tz="America/Bogota"),
    catchup=False,
    default_args=default_args,
    tags=["energia", "prediccion", "semanal", "lstm"],
    doc_md="""### DAG Predicción Semanal de Demanda (Conciso)
    1. Descarga artefactos (modelo/scalers) de MinIO.
    2. Obtiene datos históricos de PostgreSQL.
    3. Genera predicciones para la próxima semana.
    4. Guarda predicciones en PostgreSQL.
    """,
)
def prediccion_demanda_semanal_dag_conciso():
    """Define el DAG y sus tareas."""

    @task
    def setup_local_dir() -> str:
        """Crea y limpia el directorio temporal local."""
        os.makedirs(LOCAL_ARTIFACT_PATH, exist_ok=True)
        logging.info(f"Directorio local asegurado: {LOCAL_ARTIFACT_PATH}")
        # Limpiar directorio (opcional pero recomendado)
        for item in os.listdir(LOCAL_ARTIFACT_PATH):
            item_path = os.path.join(LOCAL_ARTIFACT_PATH, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
            except Exception as e:
                logging.warning(f"No se pudo borrar {item_path}: {e}")
        logging.info(f"Directorio local limpiado: {LOCAL_ARTIFACT_PATH}")
        return LOCAL_ARTIFACT_PATH

    @task
    def download_artifacts_from_s3(local_dir_path: str) -> dict[str, str]:
        """Descarga modelo y scalers desde S3/MinIO usando get_key().download_file()."""
        s3_hook = S3Hook(aws_conn_id=MINIO_CONN_ID)
        files = {"model": MODEL_KEY, "feature_scaler": FEATURE_SCALER_KEY, "target_scaler": TARGET_SCALER_KEY}
        paths: dict[str, str] = {}
        for name, key in files.items():
            # Construye la ruta COMPLETA del archivo destino local
            local_file_path = os.path.join(local_dir_path, os.path.basename(key))
            try:
                logging.info(f"Descargando {key} a {local_file_path}")

                # --- Solución: Usar get_key().download_file() ---
                # 1. Obtener el objeto S3 (representación del archivo en S3)
                s3_object = s3_hook.get_key(key=key, bucket_name=S3_BUCKET)
                # 2. Llamar al método download_file DEL OBJETO S3, especificando la ruta local completa
                s3_object.download_file(local_file_path)
                # --- Fin Solución ---

                if not os.path.isfile(local_file_path): # Verifica descarga
                    raise FileNotFoundError(f"{local_file_path} no encontrado post-descarga.")
                paths[name] = local_file_path
                logging.info(f"Descargado y verificado: {local_file_path}")
            except Exception as e:
                # Captura errores de get_key, download_file o la verificación
                logging.error(f"Error descargando {name} ({key}): {e}", exc_info=True)
                raise AirflowException(f"Fallo descarga artefacto '{name}'.")

        if len(paths) != len(files):
            # Esto no debería ocurrir si cada descarga fallida lanza excepción, pero es una doble verificación
            raise AirflowException("No se descargaron todos los artefactos.")

        logging.info(f"Todos los artefactos descargados exitosamente: {paths}")
        return paths

    @task
    def get_historical_data(hours_to_fetch: int) -> pd.DataFrame:
        """Obtiene últimas `hours_to_fetch` horas de datos desde PostgreSQL."""
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        sql = f"""
            SELECT
                datetime,
                kwh       AS "kWh",  -- Alias con comillas para forzar mayúscula/minúscula
                mes       AS "Mes",
                hour      AS "Hour",
                season    AS "Season",
                dia_habil AS "Dia_habil"
            FROM demanda_historico
            ORDER BY datetime DESC
            LIMIT {hours_to_fetch};
        """
        logging.info(f"Obteniendo {hours_to_fetch}h de datos históricos...")
        df = pg_hook.get_pandas_df(sql)
        logging.warning(f"DEBUG (WARNING): Columnas recibidas de BD: {df.columns.tolist()}")
        logging.info(f"DEBUG (INFO): DataFrame obtenido: {df}")
        if df.empty:
            raise ValueError("No se obtuvieron datos históricos.")
        if len(df) < hours_to_fetch:
            raise ValueError(f"Datos históricos insuficientes ({len(df)}/{hours_to_fetch}).")
        df = df.sort_values("datetime").reset_index(drop=True) # Orden ASC para modelo
        logging.info(f"Datos históricos preparados ({len(df)} filas). Último ts: {df['datetime'].iloc[-1]}")
        return df

    @task
    def make_and_format_predictions(df_hist: pd.DataFrame, paths: dict) -> list[dict]:
        """Carga modelo, prepara datos, predice y formatea salida."""
        if df_hist is None or df_hist.empty: # Validación defensiva
            raise ValueError("No hay datos históricos válidos para predicción.")
        try:
            logging.info(f"Prediciendo con {len(df_hist)} registros. Artefactos: {paths}")
            # 1. Cargar artefactos locales
            model, feat_scaler, targ_scaler = load_model_and_scalers(
                model_path=paths["model"],
                feature_scaler_path=paths["feature_scaler"],
                target_scaler_path=paths["target_scaler"],
            )
            # 2. Preparar entrada (NOTA: Solo necesita feat_scaler)
            input_data = prepare_prediction_input(df_hist, feat_scaler)
            # 3. Generar y re-escalar predicciones
            preds = generate_predictions(model, input_data, targ_scaler)
            # 4. Formatear salida
            last_ts = df_hist["datetime"].iloc[-1]
            records = create_prediction_output(preds, last_ts, MODEL_VERSION)
            logging.info(f"Predicciones generadas: {len(records)} puntos.")
            return records
        except KeyError as ke:
             logging.error(f"Falta clave de artefacto: {ke}. Paths: {paths}", exc_info=True)
             raise AirflowException(f"Fallo acceso a ruta de artefacto: {ke}")
        except Exception as e:
             logging.error(f"Error durante predicción: {e}", exc_info=True)
             raise AirflowException(f"Fallo en make_and_format_predictions: {e}")

    @task
    def save_predictions_to_db(records: list[dict], run_ts_iso: str):
        """Guarda predicciones en la base de datos."""
        if not records:
            logging.info("No hay predicciones para guardar.")
            return
        if not run_ts_iso: # Debe recibir el ts de ejecución
             raise ValueError("Timestamp de ejecución 'run_ts_iso' es requerido.")
        logging.info(f"Guardando {len(records)} predicciones para corrida: {run_ts_iso}")
        insert_predictions(
            predictions_list=records,
            prediction_run_ts_iso=run_ts_iso, # Usar ts pasado
            postgres_conn_id=POSTGRES_CONN_ID,
        )

    # --- Flujo del DAG ---
    local_path = setup_local_dir()
    artifact_paths = download_artifacts_from_s3(local_path)
    df = get_historical_data(WINDOW_SIZE)
    predictions = make_and_format_predictions(df, artifact_paths)
    # Pasa el timestamp lógico de la ejecución ('{{ ts }}')
    save_predictions_to_db(predictions, run_ts_iso="{{ ts }}")

# Registrar el DAG
prediccion_demanda_semanal_dag_conciso()