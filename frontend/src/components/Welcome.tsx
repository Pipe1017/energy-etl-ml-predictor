// src/components/Welcome.tsx

import './Welcome.css'; // Archivo CSS opcional para estilos específicos

function Welcome() {
  const currentDate = new Date();
  const formattedDate = currentDate.toLocaleDateString('es-CO', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  const formattedTime = currentDate.toLocaleTimeString('es-CO', {
      hour: '2-digit', minute: '2-digit', hour12: true
  });


  return (
    <div className="welcome-section card"> {/* Usa la clase card si la tienes definida */}
      <h2>Bienvenido al Portal de Analítica Energética</h2>
      <p className="subtitle">Datos y Predicciones de Demanda para Medellín, Colombia</p>
      <hr />
      <p>
        Aquí puedes visualizar la demanda histórica de energía registrada y compararla
        con las predicciones generadas por nuestro modelo LSTM.
      </p>
      <p className="date-info">
          Fecha y Hora Actual (Medellín): {formattedDate} - {formattedTime}
      </p>
    </div>
  );
}

export default Welcome;