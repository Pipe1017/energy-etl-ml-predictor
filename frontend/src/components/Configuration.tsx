// src/components/Configuration.tsx

import './Configuration.css'; // Opcional

function Configuration() {
  return (
    <div className="configuration-section card">
      <h3>Configuración de Visualización</h3>
      <p style={{ fontStyle: 'italic', color: '#666' }}>
        Próximamente: Opciones para seleccionar rangos de fecha,
        comparar modelos, o ajustar parámetros de visualización.
      </p>
      {/* Aquí podrías añadir inputs desactivados o ejemplos */}
       {/*
      <div className="config-option">
        <label htmlFor="date-range">Rango de Fechas: </label>
        <input type="text" id="date-range" placeholder="Últimos 7 días" disabled />
      </div>
       */}
    </div>
  );
}

export default Configuration;