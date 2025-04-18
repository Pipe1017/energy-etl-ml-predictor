// frontend/src/components/DemandTimeSeriesChart.tsx
// ==============================================
// VERSIÓN COMPLETA (18 Abr 2025) - Incluye fechas futuras por defecto.

import { useState, useEffect, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale, ChartOptions, ChartData
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { es } from 'date-fns/locale';
// Importar addDays para calcular la fecha futura
import { addDays } from 'date-fns';
import { CombinedDemandPoint, HistoricalDemandPoint, PredictedDemandPoint } from '../types';

// --- Registrar Componentes de Chart.js ---
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale);

// --- Funciones Auxiliares ---
const formatTimestampLabel = (timestamp: number): string => {
    try {
        // Verificar si el timestamp es un número válido antes de crear la fecha
        if (isNaN(timestamp)) {
             console.warn("formatTimestampLabel recibió un timestamp inválido:", timestamp);
             return 'Fecha inválida';
        }
        const date = new Date(timestamp);
         // Verificar si la fecha creada es válida
         if (isNaN(date.getTime())) {
             console.warn("formatTimestampLabel creó una fecha inválida desde el timestamp:", timestamp);
             return 'Fecha inválida';
         }
        // Usando hora militar (00-23) y formato día/mes corto estándar en Colombia con locale 'es-CO'
        return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false }) + ' ' + date.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
    } catch (e) {
        console.error("Error formateando timestamp:", timestamp, e);
        return 'Fecha inválida';
    }
};

const formatYAxisTick = (value: number | string): string => {
    const numValue = Number(value);
    if (isNaN(numValue)) return '';
    if (numValue >= 1e6) return `${(numValue / 1e6).toFixed(1)} M`; // Millones
    if (numValue >= 1e3) return `${(numValue / 1e3).toFixed(0)} k`; // Miles (k)
    return numValue.toString(); // Valor normal
};

const formatDateToYYYYMMDD = (date: Date): string => {
    try {
        // Verificar si la fecha es válida
        if (!(date instanceof Date) || isNaN(date.getTime())) {
             console.warn("formatDateToYYYYMMDD recibió una fecha inválida:", date);
             // Retornar fecha mínima o manejar error
             return "1970-01-01";
        }
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Meses son 0-indexados
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`; // Formato AAAA-MM-DD
    } catch (e) {
        console.error("Error formateando fecha a YYYY-MM-DD:", date, e);
        return "1970-01-01"; // Retornar fecha mínima en caso de error
    }
};

// --- Componente Principal del Gráfico ---
function DemandTimeSeriesChart() {
    // --- Estado del Componente ---
    const [demandData, setDemandData] = useState<CombinedDemandPoint[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // --- Calcular Fechas por Defecto ---
    const today = useMemo(() => new Date(), []); // Obtener fecha actual una sola vez

    // Función auxiliar para calcular fecha pasada (ej. para inicio por defecto)
    const calculatePastDate = (baseDate: Date, monthsToSubtract: number): string => {
         const pastDate = new Date(baseDate);
         pastDate.setMonth(baseDate.getMonth() - monthsToSubtract);
         // Ajustar si el día del mes original no existe en el mes resultante
         if (pastDate.getDate() !== baseDate.getDate()) {
           pastDate.setDate(0); // Ir al último día del mes anterior
         }
         return formatDateToYYYYMMDD(pastDate);
    };

    // Calcular hoy y fecha futura por defecto (+14 días) usando useMemo
    const defaultStartDate = useMemo(() => calculatePastDate(today, 3), [today]); // Inicio: 3 meses antes de hoy
    const defaultFutureEndDate = useMemo(() => {
        const futureDate = addDays(today, 14); // Fin: 14 días después de hoy
        return formatDateToYYYYMMDD(futureDate);
    }, [today]);

    // --- Estados para los inputs de fecha (inicializados con los nuevos defaults) ---
    const [startDateInput, setStartDateInput] = useState<string>(defaultStartDate);
    const [endDateInput, setEndDateInput] = useState<string>(defaultFutureEndDate);

    // --- Estado para las fechas APLICADAS al filtro (inicializado con los nuevos defaults) ---
    const [filterDates, setFilterDates] = useState<{ start: string; end: string }>({
        start: defaultStartDate,
        end: defaultFutureEndDate
    });

    // --- Manejador para el clic del botón Filtrar ---
    const handleFilterClick = () => {
        // Validación básica de fechas
        if (!startDateInput || !endDateInput) { setError("Por favor, selecciona ambas fechas."); return; }
        try {
            const start = new Date(startDateInput);
            const end = new Date(endDateInput);
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                 setError("Fechas seleccionadas inválidas."); return;
            }
            if (end < start) { setError("La fecha de fin no puede ser anterior a la fecha de inicio."); return; }
        } catch (e) { setError("Error al procesar las fechas."); return; }

        setError(null); // Limpiar error si la validación pasa
        // Actualizar el estado del filtro para disparar useEffect
        setFilterDates({ start: startDateInput, end: endDateInput });
    };

    // --- Efecto para Cargar Datos ---
    useEffect(() => {
        const loadDemandData = async () => {
            // Validar fechas del filtro antes de proceder
            if (!filterDates.start || !filterDates.end) {
                setError("Fechas de filtro inválidas."); setLoading(false); setDemandData([]); return;
            }
            // Verificar si las fechas son válidas antes de usarlas
            try {
                if (isNaN(new Date(filterDates.start).getTime()) || isNaN(new Date(filterDates.end).getTime())) {
                     setError("Fechas de filtro inválidas."); setLoading(false); setDemandData([]); return;
                }
            } catch {
                 setError("Fechas de filtro inválidas."); setLoading(false); setDemandData([]); return;
            }

            setLoading(true); setError(null);
            console.log(`Iniciando carga con filtro: ${filterDates.start} a ${filterDates.end}`);

            try {
                // Construir Parámetros y URLs Relativas
                const historicalParams = new URLSearchParams({
                    skip: '0', start_date: filterDates.start, end_date: filterDates.end
                });
                const historicalUrl = `/api/v1/demand/historical?${historicalParams.toString()}`;
                // NOTA: La URL de predicciones sigue sin filtrar por fecha. Si tu API lo permite, considera añadir params.
                const predictionsUrl = `/api/v1/demand/predictions?skip=0&limit=500`;

                console.log("Solicitando datos históricos:", historicalUrl);
                console.log("Solicitando datos de predicción:", predictionsUrl);

                // Fetch y Procesamiento
                const [historicalResponse, predictionsResponse] = await Promise.all([
                    fetch(historicalUrl), fetch(predictionsUrl)
                ]);

                // Validación de Respuestas
                if (!historicalResponse.ok) {
                    const errorText = await historicalResponse.text();
                    throw new Error(`Error HTTP Históricos (${historicalResponse.status}): ${errorText || historicalResponse.statusText}`);
                }
                if (!predictionsResponse.ok) {
                    const errorText = await predictionsResponse.text();
                    throw new Error(`Error HTTP Predicciones (${predictionsResponse.status}): ${errorText || predictionsResponse.statusText}`);
                }

                // Procesamiento de Datos
                const historicalDataObj = await historicalResponse.json();
                const predictionsRaw: PredictedDemandPoint[] = await predictionsResponse.json();

                // Validación de formato
                if (!historicalDataObj || typeof historicalDataObj !== 'object' || !Array.isArray(historicalDataObj.results)) {
                     console.error("Respuesta histórica inesperada:", historicalDataObj);
                     throw new Error('La respuesta de datos históricos no tiene el formato esperado.');
                 }
                const historicalRaw: HistoricalDemandPoint[] = historicalDataObj.results;
                if (!Array.isArray(predictionsRaw)) {
                     console.error("Respuesta de predicciones inesperada:", predictionsRaw);
                     throw new Error('La respuesta de datos de predicciones no es un array.');
                 }
                console.log(`Recibidos ${historicalRaw.length} registros históricos, ${predictionsRaw.length} predicciones.`);

                // Combinación y Mapeo
                const combinedDataMap = new Map<number, CombinedDemandPoint>();
                historicalRaw.forEach(item => {
                    if (item.datetime && item.kwh !== null && item.kwh !== undefined) {
                        const timestamp = new Date(item.datetime).getTime();
                        if (!isNaN(timestamp)) {
                            if (!combinedDataMap.has(timestamp)) { combinedDataMap.set(timestamp, { x: timestamp, y_hist: item.kwh, y_pred: null }); }
                        } else { console.warn("Fecha histórica inválida:", item.datetime); }
                    }
                });
                predictionsRaw.forEach(item => {
                    if (item.prediction_for_datetime && item.predicted_kwh !== null && item.predicted_kwh !== undefined) {
                        const timestamp = new Date(item.prediction_for_datetime).getTime();
                        if (!isNaN(timestamp)) {
                            const existing = combinedDataMap.get(timestamp);
                            if (existing) { existing.y_pred = item.predicted_kwh; }
                            else { combinedDataMap.set(timestamp, { x: timestamp, y_hist: null, y_pred: item.predicted_kwh }); }
                        } else { console.warn("Fecha de predicción inválida:", item.prediction_for_datetime); }
                    }
                });

                const finalChartData = Array.from(combinedDataMap.values()).sort((a, b) => a.x - b.x);
                console.log(`Datos combinados y ordenados: ${finalChartData.length} puntos.`);
                setDemandData(finalChartData);

            } catch (err) {
                console.error("Error detallado cargando datos de demanda:", err);
                const message = err instanceof Error ? err.message : 'Ocurrió un error desconocido al cargar los datos.';
                setError(`Error al cargar datos: ${message}`);
                setDemandData([]); // Limpiar datos si hay error
            } finally {
                setLoading(false);
            }
        };
        loadDemandData();
    }, [filterDates]); // Dependencia: Ejecutar solo cuando cambian las fechas del filtro aplicado

    // --- Opciones de Configuración del Gráfico ---
    const chartOptions = useMemo((): ChartOptions<'line'> => {
        let minTimestamp: number | undefined = undefined;
        let maxTimestamp: number | undefined = undefined;
        try {
            // Calcular timestamps UTC para consistencia
            if (filterDates.start) { minTimestamp = new Date(filterDates.start + 'T00:00:00Z').getTime(); }
            if (filterDates.end) {
                const endDate = new Date(filterDates.end + 'T00:00:00Z');
                // Incluir todo el día final (hasta 23:59:59.999)
                maxTimestamp = endDate.getTime() + (24 * 60 * 60 * 1000 - 1);
            }
            // Validar que los timestamps sean números válidos
            if (isNaN(minTimestamp as number)) minTimestamp = undefined;
            if (isNaN(maxTimestamp as number)) maxTimestamp = undefined;
        } catch (e) { console.error("Error calculando min/max timestamp:", e); minTimestamp = maxTimestamp = undefined; }

        // Log para depuración de los límites del eje X
        console.log(`Ajustando escala X: min=${minTimestamp ? new Date(minTimestamp).toISOString() : 'auto'}, max=${maxTimestamp ? new Date(maxTimestamp).toISOString() : 'auto'}`);

        return {
            responsive: true,
            maintainAspectRatio: false, // Permite controlar altura con CSS/contenedor
            interaction: {
                mode: 'index', // Muestra tooltips para todos los datasets en el mismo índice X
                intersect: false // El tooltip aparece al pasar cerca, no necesita tocar el punto exacto
            },
            plugins: {
                legend: {
                    position: 'top' as const // Posición de la leyenda
                },
                title: {
                    display: true, // Mostrar título del gráfico
                    text: 'Demanda Energética: Histórica vs. Predicha' // Título
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        // Formato del label (contenido) del tooltip
                        label: function(context) {
                            let label = context.dataset.label || ''; // Nombre del dataset (ej: 'Demanda Histórica (kWh)')
                            if (label) label += ': ';
                            // Usar valor parseado si existe y es número
                            if (context.parsed && context.parsed.y !== null && !isNaN(context.parsed.y)) {
                                // Formato numérico local (Colombia) sin decimales y añadir unidad
                                label += context.parsed.y.toLocaleString('es-CO', { maximumFractionDigits: 0 }) + ' kWh';
                            } else {
                                label += 'N/A'; // Mostrar N/A si no hay dato
                            }
                            return label;
                        },
                        // Formato del título del tooltip (usualmente la fecha/hora)
                        title: function(tooltipItems) {
                            // Tomar el primer item del tooltip (todos deberían tener el mismo valor X)
                            if (tooltipItems.length > 0 && tooltipItems[0].parsed) {
                                // Usar la función auxiliar para formatear el timestamp
                                return formatTimestampLabel(tooltipItems[0].parsed.x);
                            }
                            return ''; // Retornar vacío si no hay items
                        }
                    }
                }
            },
            scales: {
                x: { // Configuración del eje X (Tiempo)
                    type: 'time', // Indicar que es una escala de tiempo
                    adapters: {
                        date: { locale: es } // Usar adaptador de date-fns con locale español
                    },
                    time: {
                        unit: 'day', // Unidad base para mostrar ticks (puede ser 'hour', 'week', etc.)
                        // Formato detallado para usar en el tooltip (si se configura)
                        tooltipFormat: 'PPpp', // ej: 18 abr 2025 14:30:00
                        // Formatos para mostrar en las etiquetas del eje según el nivel de zoom/unidad
                        displayFormats: {
                            hour: 'HH:mm',      // ej: 15:00
                            day: 'MMM d',       // ej: abr 18
                            week: 'MMM d yy',   // ej: abr 18 25
                            month: 'MMM yy',    // ej: abr 25
                            year: 'yyyy'        // ej: 2025
                        }
                    },
                    title: { display: true, text: 'Fecha y Hora' }, // Título del eje X
                    // Aplicar los límites calculados basados en el filtro
                    min: minTimestamp,
                    max: maxTimestamp,
                    ticks: {
                        autoSkip: true,       // Permitir que Chart.js omita etiquetas si se solapan
                        maxTicksLimit: 15     // Limitar el número máximo de etiquetas visibles
                    }
                },
                y: { // Configuración del eje Y (Demanda)
                    title: { display: true, text: 'Demanda (kWh)' }, // Título del eje Y
                    min: 0, // Forzar que el eje empiece en 0
                    ticks: {
                        // Usar la función auxiliar para formatear los números (añadir k, M)
                        callback: formatYAxisTick
                    },
                    beginAtZero: true // Redundante con min: 0, pero asegura la intención
                },
            },
        };
    }, [filterDates]); // Recalcular opciones solo si cambian las fechas del filtro


    // --- Preparación de Datos para el Gráfico ---
    const chartData = useMemo((): ChartData<'line'> => {
        console.log(`Preparando chartData con ${demandData.length} puntos.`);
        return {
            // No necesitamos 'labels' explícitos porque usamos escala 'time' y datos {x, y}
            datasets: [
                { // Dataset para datos históricos
                    label: 'Demanda Histórica (kWh)',
                    // Mapear datos combinados al formato {x: timestamp, y: valor_historico}
                    // Usar NaN donde no hay dato histórico para que spanGaps funcione
                    data: demandData.map(p => ({ x: p.x, y: p.y_hist ?? NaN })),
                    borderColor: 'rgb(54, 162, 235)', // Azul
                    backgroundColor: 'rgba(54, 162, 235, 0.1)', // Relleno azul claro
                    tension: 0.1,      // Suavizado leve de la línea
                    pointRadius: 0,    // Ocultar puntos (mejor para muchas series)
                    pointHitRadius: 10, // Área de detección para tooltip
                    borderWidth: 2,    // Grosor de la línea
                    spanGaps: true,    // Conectar puntos aunque haya NaN entre ellos
                },
                { // Dataset para datos predichos
                    label: 'Demanda Predicha (kWh)',
                    // Mapear datos combinados al formato {x: timestamp, y: valor_predicho}
                    data: demandData.map(p => ({ x: p.x, y: p.y_pred ?? NaN })),
                    borderColor: 'rgb(255, 99, 132)', // Rojo/Rosa
                    backgroundColor: 'rgba(255, 99, 132, 0.1)', // Relleno rosa claro
                    borderDash: [5, 5], // Línea punteada para diferenciarla
                    tension: 0.1,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    borderWidth: 2,
                    spanGaps: true,
                }
            ],
        };
    }, [demandData]); // Recalcular datos del gráfico solo si cambia demandData


    // --- Renderizado del Componente ---
    return (
        // Contenedor principal con clases CSS (definidas en App.css)
        <div className="chart-container card">

            {/* Sección de Filtros de Fecha */}
            <div className="date-filters">
                <h4>Filtrar Rango:</h4>
                <div>
                    <label htmlFor="start-date">Inicio:</label>
                    <input
                        type="date" id="start-date" value={startDateInput}
                        onChange={(e) => setStartDateInput(e.target.value)}
                        // No permitir seleccionar inicio después del fin actual
                        max={endDateInput || defaultFutureEndDate}
                        aria-label="Fecha de inicio del filtro"
                    />
                </div>
                <div>
                    <label htmlFor="end-date">Fin:</label>
                    <input
                        type="date" id="end-date" value={endDateInput}
                        onChange={(e) => setEndDateInput(e.target.value)}
                        // No permitir seleccionar fin antes del inicio actual
                        min={startDateInput || defaultStartDate}
                        // Eliminado el max para permitir seleccionar cualquier fecha futura
                        aria-label="Fecha de fin del filtro"
                    />
                </div>
                {/* Botón para aplicar el filtro, deshabilitado mientras carga */}
                <button onClick={handleFilterClick} disabled={loading}>
                    {loading ? 'Cargando...' : 'Aplicar Filtro'}
                </button>
            </div>

             {/* Mensaje de Error (si existe y no está cargando) */}
             {error && !loading && (
                <p className="error-message" style={{ color: 'red', border: '1px solid red', padding: '10px', backgroundColor: '#ffebee', borderRadius: '4px', marginTop: '10px' }}>
                    <strong>Error:</strong> {error}
                </p>
             )}

            {/* Contenedor del gráfico y mensajes de estado */}
            <div className="chart-wrapper" style={{ height: '450px', position: 'relative', marginTop: '15px' }}>
                {/* Mostrar mensaje de carga */}
                {loading && (
                     <div className="loading-message" style={{ textAlign: 'center', paddingTop: '50px', fontStyle: 'italic' }}>
                         Cargando datos del gráfico...
                     </div>
                 )}
                 {/* Mostrar gráfico si NO carga, NO hay error y HAY datos */}
                {!loading && !error && demandData.length > 0 && (
                    <Line options={chartOptions} data={chartData} aria-label="Gráfico de demanda energética histórica y predicha" />
                 )}
                 {/* Mostrar mensaje si NO carga, NO hay error y NO hay datos */}
                {!loading && !error && demandData.length === 0 && (
                     <p className="no-data-message" style={{ textAlign: 'center', paddingTop: '50px', fontStyle: 'italic' }}>
                         No se encontraron datos de demanda para el rango de fechas seleccionado.
                     </p>
                 )}
            </div>
        </div>
    );
}

export default DemandTimeSeriesChart;