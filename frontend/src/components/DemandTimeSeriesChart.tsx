// src/components/DemandTimeSeriesChart.tsx

import { useState, useEffect, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale, // Escala para ejes de tiempo
    ChartOptions,
    ChartData
} from 'chart.js';
import 'chartjs-adapter-date-fns'; // Adaptador para que Chart.js entienda fechas con date-fns
import { es } from 'date-fns/locale'; // Importar idioma español para formato de fechas
import { CombinedDemandPoint, HistoricalDemandPoint, PredictedDemandPoint } from '../types'; // Importar tipos de datos definidos

// --- Registrar Componentes de Chart.js ---
// Es necesario registrar las escalas, elementos y plugins que se van a usar en el gráfico
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale
);

// --- Funciones Auxiliares (para dar formato a las etiquetas) ---

/** Formatea un timestamp (milisegundos) a una etiqueta legible (ej: "15:30 abr 18") */
const formatTimestampLabel = (timestamp: number): string => {
    try {
        const date = new Date(timestamp);
        // Combina hora y fecha corta en formato local de Colombia
        return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false }) + ' ' + date.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
    } catch (e) {
        return 'Fecha inválida';
    }
};

/** Formatea los números del eje Y para que sean más cortos (ej: 1000 -> 1k, 1000000 -> 1M) */
const formatYAxisTick = (value: number | string): string => {
    const numValue = Number(value);
    if (isNaN(numValue)) return ''; // No mostrar si no es número
    if (numValue >= 1e6) return `${(numValue / 1e6).toFixed(1)} M`; // Millones
    if (numValue >= 1e3) return `${(numValue / 1e3).toFixed(0)} k`; // Miles (kilo)
    return numValue.toString(); // Otros números
};

/** Helper para formatear una fecha a YYYY-MM-DD */
const formatDateToYYYYMMDD = (date: Date): string => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Los meses son base 0
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
};


// --- Componente Principal del Gráfico ---
function DemandTimeSeriesChart() {
    // --- Estado del Componente ---
    const [demandData, setDemandData] = useState<CombinedDemandPoint[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // --- Fechas por Defecto ---
    const defaultStartDate = '2025-01-01'; // Inicio fijo
    const defaultEndDate = formatDateToYYYYMMDD(new Date()); // Fin: "hoy"

    // --- Estados para los inputs de fecha (Inicializados con los defaults) ---
    const [startDateInput, setStartDateInput] = useState<string>(defaultStartDate);
    const [endDateInput, setEndDateInput] = useState<string>(defaultEndDate);

    // --- Estado para las fechas APLICADAS al filtro (Inicializado con los defaults) ---
    const [filterDates, setFilterDates] = useState<{ start: string | null; end: string | null }>({
        start: defaultStartDate,
        end: defaultEndDate
    });

    const apiUrl = import.meta.env.VITE_API_URL || '';

    // --- Manejador para el clic del botón Filtrar ---
    const handleFilterClick = () => {
        if (startDateInput && endDateInput && new Date(endDateInput) < new Date(startDateInput)) {
            setError("La fecha de fin no puede ser anterior a la fecha de inicio.");
            return;
        }
        setError(null);
        setFilterDates({
            start: startDateInput || null,
            end: endDateInput || null
        });
    };

    // --- Efecto para Cargar Datos ---
    useEffect(() => {
        const loadDemandData = async () => {
            setLoading(true);
            setError(null);

            try {
                // --- Construir URL Histórica Dinámicamente (SIN LÍMITE) ---
                const historicalParams = new URLSearchParams({ skip: '0' });
                if (filterDates.start) historicalParams.set('start_date', filterDates.start);
                if (filterDates.end) historicalParams.set('end_date', filterDates.end);
                const historicalUrl = `${apiUrl}/api/v1/demand/historical?${historicalParams.toString()}`;

                const predictionsUrl = `${apiUrl}/api/v1/demand/predictions?skip=0&limit=500`;

                console.log("Solicitando datos:", historicalUrl, predictionsUrl);
                const [historicalResponse, predictionsResponse] = await Promise.all([
                    fetch(historicalUrl),
                    fetch(predictionsUrl)
                ]);

                if (!historicalResponse.ok) throw new Error(`Error HTTP Históricos: ${historicalResponse.status}`);
                if (!predictionsResponse.ok) throw new Error(`Error HTTP Predicciones: ${predictionsResponse.status}`);

                const historicalDataObj = await historicalResponse.json();
                const predictionsRaw: PredictedDemandPoint[] = await predictionsResponse.json();

                if (!historicalDataObj || !Array.isArray(historicalDataObj.results)) { throw new Error('Respuesta histórica inesperada.'); }
                const historicalRaw: HistoricalDemandPoint[] = historicalDataObj.results;

                if (!Array.isArray(predictionsRaw)) { throw new Error('Respuesta de predicciones inesperada.'); }

                console.log(`Recibidos ${historicalRaw.length} históricos, ${predictionsRaw.length} predicciones.`);

                // --- Procesamiento y Combinación ---
                const combinedDataMap = new Map<number, CombinedDemandPoint>();
                historicalRaw.forEach(item => {
                     if (item.datetime && item.kwh !== null && item.kwh !== undefined) {
                         const timestamp = new Date(item.datetime).getTime();
                         if (!isNaN(timestamp)) {
                             combinedDataMap.set(timestamp, { x: timestamp, y_hist: item.kwh, y_pred: null });
                         }
                     }
                });
                predictionsRaw.forEach(item => {
                     if (item.prediction_for_datetime && item.predicted_kwh !== null && item.predicted_kwh !== undefined) {
                         const timestamp = new Date(item.prediction_for_datetime).getTime();
                         if (!isNaN(timestamp)) {
                             const existing = combinedDataMap.get(timestamp);
                             if (existing) {
                                 existing.y_pred = item.predicted_kwh;
                             } else {
                                combinedDataMap.set(timestamp, { x: timestamp, y_hist: null, y_pred: item.predicted_kwh });
                             }
                         }
                     }
                });
                const finalChartData = Array.from(combinedDataMap.values()).sort((a, b) => a.x - b.x);
                console.log(`Datos combinados y ordenados: ${finalChartData.length} puntos.`);
                setDemandData(finalChartData);

            } catch (err) {
                console.error("Error cargando datos de demanda:", err);
                setError(err instanceof Error ? err.message : 'Error desconocido al cargar datos.');
            } finally {
                setLoading(false);
            }
        };

        loadDemandData();
    }, [apiUrl, filterDates]);

    // --- Opciones de Configuración del Gráfico ---
     const chartOptions = useMemo((): ChartOptions<'line'> => ({
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
            legend: { position: 'top' as const },
            title: { display: true, text: 'Demanda Energética: Histórica vs. Predicha' },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) label += ': ';
                        if (context.parsed.y !== null && !isNaN(context.parsed.y)) {
                             label += context.parsed.y.toLocaleString('es-CO', { maximumFractionDigits: 0 });
                         }
                        return label;
                    },
                     title: function(tooltipItems) {
                         if (tooltipItems.length > 0) {
                             return formatTimestampLabel(tooltipItems[0].parsed.x);
                         }
                         return '';
                     }
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                adapters: { date: { locale: es } },
                time: {
                    unit: 'day',
                    tooltipFormat: 'PPpp',
                    displayFormats: {
                        hour: 'HH:mm', day: 'MMM d', week: 'MMM d yy', month: 'MMM yy',
                    }
                },
                title: { display: true, text: 'Fecha y Hora' },
            },
            y: {
                title: { display: true, text: 'Demanda (kWh)' },
                min: 0,
                ticks: { callback: formatYAxisTick }
            },
        },
        // Considerar opciones de rendimiento si hay muchos puntos
        // animation: false,
        // parsing: false,
    }), []); // Dependencias vacías, se calcula una vez


    // --- Preparación de Datos para el Gráfico ---
    const chartData = useMemo((): ChartData<'line'> => {
        return {
            datasets: [
                { // Dataset Histórico
                    label: 'Demanda Histórica (kWh)',
                    data: demandData.map(p => ({ x: p.x, y: p.y_hist === null ? NaN : p.y_hist })),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.1,
                    pointRadius: 0,
                    borderWidth: 2,
                    spanGaps: true,
                }, // <- Coma importante entre datasets
                { // Dataset Predicho
                    label: 'Demanda Predicha (kWh)',
                    data: demandData.map(p => ({ x: p.x, y: p.y_pred === null ? NaN : p.y_pred })), // <- La línea problemática
                    // --- COMA CORREGIDA AQUÍ --- vvvvvv
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.1,
                    pointRadius: 0,
                    borderWidth: 2,
                    spanGaps: true,
                } // <- Sin coma aquí porque es el último dataset
            ],
        };
    }, [demandData]); // Se recalcula si demandData cambia


    // --- Renderizado del Componente ---
    return (
        <div className="chart-container card">

            {/* Sección de Filtros de Fecha */}
            <div className="date-filters" style={{ marginBottom: '20px', padding: '10px', border: '1px solid #eee', borderRadius: '5px' }}>
                <h4>Filtrar Rango de Fechas</h4>
                <label htmlFor="start-date" style={{ marginRight: '5px' }}>Inicio:</label>
                <input
                    type="date"
                    id="start-date"
                    value={startDateInput}
                    onChange={(e) => setStartDateInput(e.target.value)}
                    style={{ marginRight: '15px' }}
                />
                <label htmlFor="end-date" style={{ marginRight: '5px' }}>Fin:</label>
                <input
                    type="date"
                    id="end-date"
                    value={endDateInput}
                    onChange={(e) => setEndDateInput(e.target.value)}
                    style={{ marginRight: '15px' }}
                />
                <button onClick={handleFilterClick} disabled={loading}>
                    {loading ? 'Cargando...' : 'Filtrar'}
                </button>
            </div>

            {/* Mensajes de Carga/Error */}
            {loading && <p>Cargando datos del gráfico...</p>}
            {error && (<p style={{ color: 'red', marginTop: '10px' }}>Error: {error}</p>)}

            {/* Contenedor del gráfico */}
            <div style={{ marginTop: '10px', height: '450px', position: 'relative' }}>
                {!loading && !error && demandData.length > 0 && (
                    <Line options={chartOptions} data={chartData} />
                )}
                {!loading && !error && demandData.length === 0 && (
                     <p style={{ textAlign: 'center', fontStyle: 'italic', paddingTop: '50px' }}>
                         No se encontraron datos de demanda para el rango seleccionado.
                     </p>
                 )}
            </div>
        </div>
    );
}

export default DemandTimeSeriesChart;

// --- Definiciones de Tipos (ejemplo para src/types.ts - sin cambios) ---
/*
export interface HistoricalDemandPoint {
    datetime: string;
    kwh: number | null;
    mes: number | null;
    hour: number | null;
    season: number | null;
    dia_habil: number | null;
}

export interface PredictedDemandPoint {
    prediction_run_ts: string;
    prediction_for_datetime: string;
    predicted_kwh: number | null;
    model_version: string | null;
}

export interface CombinedDemandPoint {
    x: number; // Timestamp ms
    y_hist: number | null;
    y_pred: number | null;
}
*/