/**
 * Dashboard App - AgroPampa S.A.
 * 
 * Este script inicializa los 4 elementos obligatorios del Ítem 6 usando Chart.js
 * En una implementación real, haría fetch() a la API REST de Supabase.
 * Aquí mockeamos los resultados de las queries SQL que armamos en la Base de Datos.
 */

// Configuración global de Chart.js para Dark Mode
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = 'Inter';
Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.05)';

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. Evolución del Rendimiento (Línea)
    // ==========================================
    const ctxEvolucion = document.getElementById('evolucionChart').getContext('2d');
    
    // Gradiente para el gráfico de líneas
    const gradientSoja = ctxEvolucion.createLinearGradient(0, 0, 0, 400);
    gradientSoja.addColorStop(0, 'rgba(16, 185, 129, 0.5)'); // Verde
    gradientSoja.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    new Chart(ctxEvolucion, {
        type: 'line',
        data: {
            labels: ['2022/23 (Normal)', '2023/24 (Sequía)', '2024/25 (Recup.)'],
            datasets: [
                {
                    label: 'Soja (kg/ha)',
                    data: [3350, 2750, 3420],
                    borderColor: '#10b981',
                    backgroundColor: gradientSoja,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Trigo (kg/ha)',
                    data: [4100, 3200, 4250],
                    borderColor: '#f59e0b', // Amarillo
                    borderWidth: 3,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: false, min: 2000 } }
        }
    });


    // ==========================================
    // 2. Producción por Propietario (Barras)
    // ==========================================
    const ctxPropietarios = document.getElementById('propietariosChart').getContext('2d');
    new Chart(ctxPropietarios, {
        type: 'bar',
        data: {
            labels: ['Perez S.A.', 'Gomez Hnos', 'Agro Inversiones', 'Crespo', 'Don Juan'],
            datasets: [{
                label: 'Producción Total (TN)',
                data: [12500, 9800, 15400, 6200, 4350],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)', // Azul
                    'rgba(139, 92, 246, 0.8)', // Púrpura
                    'rgba(16, 185, 129, 0.8)', // Verde
                    'rgba(245, 158, 11, 0.8)', // Naranja
                    'rgba(239, 68, 68, 0.8)'   // Rojo
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });


    // ==========================================
    // 3. Mapa de Calor / Dispersión (Minería NTILE)
    // ==========================================
    const ctxRiesgo = document.getElementById('riesgoChart').getContext('2d');
    
    // Generar datos de dispersión basados en la query de Segmentación
    // Eje X: Riesgo (Coeficiente de Variación)
    // Eje Y: Rendimiento Promedio
    const generarScatter = (count, minX, maxX, minY, maxY) => {
        return Array.from({length: count}, () => ({
            x: Math.random() * (maxX - minX) + minX,
            y: Math.random() * (maxY - minY) + minY,
            r: Math.random() * 5 + 5
        }));
    };

    new Chart(ctxRiesgo, {
        type: 'bubble', // Bubble actua muy bien para matrices de riesgo
        data: {
            datasets: [
                {
                    label: 'Grupo 1: Alto Rendimiento',
                    data: generarScatter(8, 0.05, 0.12, 3600, 4200),
                    backgroundColor: 'rgba(16, 185, 129, 0.6)',
                    borderColor: 'rgba(16, 185, 129, 1)'
                },
                {
                    label: 'Grupo 2: Medio',
                    data: generarScatter(10, 0.10, 0.18, 2800, 3500),
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgba(59, 130, 246, 1)'
                },
                {
                    label: 'Grupo 3: Riesgoso',
                    data: generarScatter(7, 0.18, 0.30, 1800, 2700),
                    backgroundColor: 'rgba(239, 68, 68, 0.6)',
                    borderColor: 'rgba(239, 68, 68, 1)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    title: { display: true, text: 'Riesgo (Coeficiente de Variación)', color: '#94a3b8' }
                },
                y: { 
                    title: { display: true, text: 'Rendimiento Promedio Histórico (kg/ha)', color: '#94a3b8' }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (context) => `Rinde: ${context.raw.y.toFixed(0)} kg/ha | CV: ${context.raw.x.toFixed(2)}`
                    }
                }
            }
        }
    });

    // Elemento 4: La "Proyección OLS" está en las KPI Cards (arriba)
});
