// frontend/src/App.tsx
// =====================
// CORREGIDO: Eliminada la importación 'React,' que causaba el error TS6133
import { useState, lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import 'chartjs-adapter-date-fns';
// Importamos el CSS corregido
import './App.css';

// Components
import Sidebar from './components/Sidebar';
// Importa los componentes de forma diferida (lazy)
const DemandTimeSeriesChart = lazy(() => import('./components/DemandTimeSeriesChart'));
const PlaceholderPage = lazy(() => import('./components/PlaceholderPage'));
const HomePage = lazy(() => import('./components/HomePage')); // Importa la nueva HomePage

// Register Chart.js (Esto está bien)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale);

// Componente de carga simple mientras los componentes lazy cargan
const LoadingFallback = () => (
  <div style={{ padding: '50px', textAlign: 'center', color: '#e0e0e0' }}>Cargando...</div>
);

function App() {
  // Estado para controlar si el sidebar está abierto o cerrado
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    // Contenedor principal con tema oscuro
    <div className="dark-theme app-container">
      {/* El Sidebar recibe el estado y la función para cambiarlo */}
      <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      {/* Contenido principal */}
      {/* La clase 'sidebar-open' se aplica/quita dinámicamente */}
      <main className={`main-content ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Suspense envuelve las rutas para manejar la carga diferida */}
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* --- Rutas de la aplicación --- */}

            {/* Ruta principal */}
            <Route path="/" element={<HomePage />} />

            {/* Rutas base para secciones principales (muestra un placeholder general) */}
            <Route path="/descriptive-analysis" element={<PlaceholderPage title="Análisis Descriptivo" description="Selecciona una subcategoría como Energía, Demanda, etc." />} />
            <Route path="/predictive-analysis" element={<PlaceholderPage title="Análisis Predictivo" description="Selecciona una subcategoría como Energía, Demanda, etc." />} />

            {/* Rutas de Análisis Descriptivo */}
            <Route path="/descriptive-analysis/energy" element={<PlaceholderPage title="Análisis Descriptivo: Energía" description="Visualización de datos históricos de energía." />} />
            <Route path="/descriptive-analysis/demand" element={<PlaceholderPage title="Análisis Descriptivo: Demanda" description="Visualización de datos históricos de demanda." />} />
            <Route path="/descriptive-analysis/reservoirs" element={<PlaceholderPage title="Análisis Descriptivo: Embalses" description="Visualización de datos históricos de embalses." />} />
            <Route path="/descriptive-analysis/rivers" element={<PlaceholderPage title="Análisis Descriptivo: Ríos" description="Visualización de datos históricos de ríos." />} />

            {/* Rutas de Análisis Predictivo */}
            <Route path="/predictive-analysis/energy" element={<PlaceholderPage title="Predicción: Energía" description="Predicciones futuras sobre la generación de energía." />} />
            {/* Ruta con el gráfico real */}
            <Route path="/predictive-analysis/demand" element={<DemandTimeSeriesChart />} />
            <Route path="/predictive-analysis/reservoirs" element={<PlaceholderPage title="Predicción: Embalses" description="Predicciones futuras sobre los niveles de los embalses." />} />
            <Route path="/predictive-analysis/rivers" element={<PlaceholderPage title="Predicción: Ríos" description="Predicciones futuras sobre los caudales de los ríos." />} />

            {/* Considera añadir una ruta para páginas no encontradas */}
            {/* <Route path="*" element={<NotFoundPage />} /> */}
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default App;