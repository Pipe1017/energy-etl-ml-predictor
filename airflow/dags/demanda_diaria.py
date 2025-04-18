# -*- coding: utf-8 -*-
# Archivo: dags/xm_demanda_dag_desacoplado.py

from __future__ import annotations

import pendulum
from datetime import timedelta
import logging

# Importaciones de Airflow
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException

# Importaciones de librerías usadas DIRECTAMENTE en las tareas (si las hay)
# En este caso, las tareas son principalmente llamadas a funciones externas
# import pandas as pd # pd ya no se usa directamente aquí

# Importa las funciones desacopladas desde los scripts
try:
    from scripts.xm_api_utils import extraer_demanda
    from scripts.data_processing import transformar_dataframe_demanda
    from scripts.db_operations import insertar_registros_demanda
except ImportError as e:
    logging.error(f"Error importando funciones de scripts: {e}. Verifica PYTHONPATH y la ubicación de 'scripts'.")
    # Define funciones placeholder para que el DAG cargue pero falle en ejecución
    def extraer_demanda(*args, **kwargs): raise NotImplementedError("extraer_demanda no importado")
    def transformar_dataframe_demanda(*args, **kwargs): raise NotImplementedError("transformar_dataframe_demanda no importado")
    def insertar_registros_demanda(*args, **kwargs): raise NotImplementedError("insertar_registros_demanda no importado")


# Configuración de argumentos por defecto para el DAG
default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

# --- Definición del DAG Desacoplado ---
@dag(
    dag_id='xm_actualizar_demanda_desacoplado_v1', # Nuevo ID
    schedule='0 2 * * *', # Diariamente a las 2:00 AM
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Bogota"),
    catchup=False,
    default_args=default_args,
    tags=['energia', 'xm', 'demanda', 'desacoplado'],
    doc_md="""
    ### DAG Desacoplado para Actualizar Datos de Demanda de Energía XM

    Versión refactorizada que separa la lógica de extracción, transformación y carga
    en funciones dentro de la carpeta `scripts`.

    1.  **Extrae** datos de los últimos 10 días.
    2.  **Transforma** los datos al formato requerido.
    3.  **Carga** los datos en la tabla `historico` usando `ON CONFLICT DO NOTHING`.
    """,
)
def xm_demanda_dag_desacoplado():
    """Define el DAG desacoplado."""

    @task(task_id="extraer_datos_api_xm")
    # Especificar qué tipo devuelve ayuda a Airflow y a la legibilidad.
    # Nota: La serialización de DataFrames puede depender de la config de Airflow.
    # Considerar devolver JSON si hay problemas: df.to_json(orient='split', date_format='iso')
    def extraer_datos() -> pd.DataFrame | None:
        """
        Calcula el rango de fechas (últimos 10 días hasta ayer) y llama a la
        función de extracción de la API. Devuelve un DataFrame de Pandas.
        """
        now = pendulum.now("America/Bogota")
        fecha_ayer = now.date() - timedelta(days=0)
        fecha_inicio_rango = fecha_ayer - timedelta(days=15)

        logging.info(f"Task [extraer_datos]: Extrayendo para {fecha_inicio_rango} a {fecha_ayer}")
        df_raw = extraer_demanda(fecha_inicio_rango, fecha_ayer)

        # Validar el resultado antes de pasarlo a la siguiente tarea
        if df_raw is None:
             logging.warning("Task [extraer_datos]: La extracción no devolvió datos (None).")
             # Podríamos querer que la tarea falle o simplemente continuar con None/vacío
             # raise AirflowException("Fallo en la extracción de datos, no se obtuvieron datos.")
        elif df_raw.empty:
             logging.warning("Task [extraer_datos]: La extracción devolvió un DataFrame vacío.")

        return df_raw # Devolver el DataFrame (Airflow intentará serializarlo/deserializarlo)

    @task(task_id="transformar_datos_demanda")
    def transformar_datos(df_raw: pd.DataFrame | None) -> list[dict]:
        """
        Recibe el DataFrame de la tarea anterior y llama a la función
        de transformación externa. Devuelve una lista de diccionarios.
        """
        logging.info("Task [transformar_datos]: Iniciando transformación...")
        # Nota: Airflow deserializará df_raw aquí si fue serializado.
        # Si se usó JSON: df_raw = pd.read_json(df_raw_json, orient='split')
        records = transformar_dataframe_demanda(df_raw)
        if not records and df_raw is not None and not df_raw.empty:
             logging.warning("Task [transformar_datos]: La transformación devolvió una lista vacía aunque había datos de entrada.")
             # Podría indicar un problema en la función de transformación
        logging.info(f"Task [transformar_datos]: Transformación resultó en {len(records)} registros.")
        return records

    @task(task_id="cargar_datos_postgres")
    def cargar_datos(records_to_load: list[dict]):
        """
        Recibe la lista de diccionarios y llama a la función externa
        para insertarlos en la base de datos.
        """
        logging.info("Task [cargar_datos]: Iniciando carga en BD...")
        if not records_to_load:
             logging.info("Task [cargar_datos]: No hay registros para cargar, tarea completada.")
             return # Termina la tarea si no hay nada que cargar

        # Llama a la función de inserción, pasando los datos y el connection ID
        insertar_registros_demanda(records_to_load, 'app_postgres') # Usa la conexión definida en Airflow
        logging.info("Task [cargar_datos]: Llamada a función de carga completada.")


    # --- Definición del Flujo/Pipeline del DAG ---
    datos_crudos_df = extraer_datos()
    registros_listos_dict = transformar_datos(datos_crudos_df)
    cargar_datos(registros_listos_dict)

# Llama a la función decorada para que Airflow registre el DAG
xm_demanda_dag_desacoplado()