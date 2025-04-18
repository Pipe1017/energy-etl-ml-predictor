# -*- coding: utf-8 -*-
"""Utilidades concisas para predicción de demanda."""

import logging
from datetime import timedelta

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

# Constantes (consistentes con el DAG)
WINDOW_SIZE_HOURS = 336
N_FEATURES = 5
REQUIRED_COLS_ORDERED = [
    'Mes', 'Hour', 'Season', 'Dia_habil', 'kWh'
]
PREDICTION_HORIZON_HOURS = 168


def load_model_and_scalers(
    model_path: str,
    feature_scaler_path: str,
    target_scaler_path: str
) -> tuple[tf.keras.Model, object, object]:
    """Carga modelo Keras y scalers Joblib."""
    try:
        model = keras.models.load_model(model_path)
        feature_scaler = joblib.load(feature_scaler_path)
        target_scaler = joblib.load(target_scaler_path)
        logging.info("Modelo y scalers cargados.")
        return model, feature_scaler, target_scaler
    except Exception as e:
        logging.error(f"Error cargando artefactos: {e}", exc_info=True)
        raise



def prepare_prediction_input(
    df_hist: pd.DataFrame,
    feature_scaler
) -> np.ndarray:
    """Prepara datos históricos para entrada LSTM (escala, ordena, ajusta forma)."""
    if df_hist is None or df_hist.empty:
        raise ValueError("Input df vacío.")
    if len(df_hist) < WINDOW_SIZE_HOURS:
        raise ValueError("Datos insuficientes.")

    df_window = df_hist.iloc[-WINDOW_SIZE_HOURS:].copy()
    # Asegura orden de columnas
    try:
        df_window = df_window[REQUIRED_COLS_ORDERED]
    except KeyError as e:
        raise ValueError(f"Falta columna requerida {e} en datos históricos.")

    # Escala features
    try:
        scaled_features = feature_scaler.transform(df_window)
    except Exception as e:
        logging.error(f"Error escalando features: {e}", exc_info=True)
        raise

    # Remodela para LSTM: (batch_size=1, timesteps, features)
    input_data = scaled_features.reshape(1, WINDOW_SIZE_HOURS, N_FEATURES)
    logging.info(f"Datos de entrada preparados con forma: {input_data.shape}")
    return input_data



def generate_predictions(
    model,
    input_data: np.ndarray,
    target_scaler
) -> np.ndarray:
    """Genera predicciones y las re-escala a unidad original (kWh)."""
    try:
        preds_scaled = model.predict(input_data)
        logging.info(f"Predicciones escaladas generadas (forma: {preds_scaled.shape})")

        # Ajusta forma para inverse_transform
        if preds_scaled.ndim == 3 and preds_scaled.shape[0] == 1:
            preds_scaled_2d = preds_scaled.reshape(-1, 1)
        elif preds_scaled.ndim == 2 and preds_scaled.shape[0] == 1:
            preds_scaled_2d = preds_scaled.T
        elif preds_scaled.ndim == 2 and preds_scaled.shape[1] == 1:
            preds_scaled_2d = preds_scaled
        else:
            raise ValueError(f"Forma inesperada de predicción: {preds_scaled.shape}")

        preds_inverse = target_scaler.inverse_transform(preds_scaled_2d)
        preds_final = preds_inverse.flatten()
        logging.info(f"Predicciones re-escaladas a kWh. Total: {len(preds_final)}")
        return preds_final
    except Exception as e:
        logging.error(f"Error generando/re-escalando predicciones: {e}", exc_info=True)
        raise



def create_prediction_output(
    preds: np.ndarray,
    last_hist_ts: pd.Timestamp,
    model_ver: str
) -> list[dict]:
    """Crea lista de diccionarios para guardar en BD."""
    if not isinstance(last_hist_ts, pd.Timestamp):
        try:
            last_hist_ts = pd.Timestamp(last_hist_ts)
        except Exception:
            raise TypeError("last_hist_ts debe ser Timestamp.")

    future_ts = pd.date_range(
        start=last_hist_ts + timedelta(hours=1),
        periods=len(preds),
        freq='H'
    )
    
    # Eliminar primeras 6 predicciones y sus timestamps
    preds = preds[6:]
    future_ts = future_ts[6:]
    
    if len(future_ts) != len(preds):
        raise ValueError("Mismatch preds/timestamps.")

    output_records = []
    for ts, pred_kwh in zip(future_ts, preds):
        output_records.append({
            "prediction_for_datetime": ts.isoformat(),
            "predicted_kwh": float(pred_kwh),
            "model_version": model_ver
        })

    logging.info(
        f"Generados {len(output_records)} registros de predicción "
        f"(con ts como string ISO)."
    )
    return output_records
