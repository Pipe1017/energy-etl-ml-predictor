// frontend/src/App.tsx
import './App.css'; // Estilos generales

// --- Importaciones y Registro de Chart.js (Mantener) ---
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import 'chartjs-adapter-date-fns';
ChartJS.register( CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale );
// --- Fin Registro Chart.js ---

// --- Importar los Componentes de la App ---
import Welcome from './components/Welcome';                 // <-- NUEVO
import DemandTimeSeriesChart from './components/DemandTimeSeriesChart'; // El gráfico que ya tenías
import Configuration from './components/Configuration';     // <-- NUEVO

function App() {
  return (
    // Puedes usar un contenedor principal con una clase si quieres limitar el ancho
    <div className="app-container">

        {/* Sección de Bienvenida */}
        <header>
             <Welcome />
        </header>

        <hr className="divider"/> {/* Un separador visual opcional */}

        {/* Sección Principal con el Gráfico */}
        <main className="chart-section">
            {/* El componente del gráfico ya tiene su propio título interno */}
            <DemandTimeSeriesChart />
        </main>

        <hr className="divider"/> {/* Otro separador opcional */}

        {/* Sección de Configuración (Placeholder) */}
        <section className="config-section">
            <Configuration />
        </section>

         {/* Footer simple */}
         <footer className="app-footer">
            <p>&copy; {new Date().getFullYear()} Analítica Energética Colombia. Todos los derechos reservados.</p>
         </footer>
    </div>
  );
}

export default App;