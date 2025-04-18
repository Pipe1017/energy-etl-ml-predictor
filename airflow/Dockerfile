# airflow/Dockerfile

ARG AIRFLOW_IMAGE_NAME="apache/airflow:2.8.1"
FROM ${AIRFLOW_IMAGE_NAME}


# 1) Definimos la clave secreta para el webserver (reemplaza por algo aleatorio en producción)
ENV AIRFLOW__WEBSERVER__SECRET_KEY="6bRd_rJpCDPrMpC-nM4qIF0h_8U6VU5GHdcACm60Qhw"


# 2) (Opcional) Desactivar ejemplos por defecto de Airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES="false"


# 3) Copiar e instalar dependencias de Python para DAGs (requirements.txt)
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

