 let categoryChartInstance = null;
    let trendChartInstance = null;

    (function() {
        const dataElement = document.getElementById('latestData');
        if (dataElement) {
            try {
                const latestResult = JSON.parse(dataElement.textContent);
                if (latestResult && latestResult.breakdown) {
                    updateDashboard(latestResult);
                }
            } catch (e) {
                console.warn('Could not parse latest data:', e);
            }
        }
    })();
    
    function updateDashboard(result){
        if (!result || !result.breakdown) return;
        
        const breakdown = result.breakdown;
        const total = result.total_kg_co2e || 0;
        const totalTonnes = total / 1000;
        setText('.total-value', totalTonnes.toFixed(2) + ' t');
        
        const transport = (breakdown.Transport || 0) / 1000;
        const electricity = (breakdown.Electricity || 0) / 1000;
        const enhancedFuel = (breakdown.EnhancedFuel || 0) / 1000;
        const diet = (breakdown.Diet || 0) / 1000;
        const buildings = (breakdown.Buildings || 0) / 1000;
        const trees = (breakdown.Trees || 0) / 1000;
        
        setText('.transport-value', transport.toFixed(2) + ' t');
        setText('.housing-value', buildings.toFixed(2) + ' t');
        setText('.energy-value', (electricity + enhancedFuel).toFixed(2) + ' t');
        setText('.offset-value', Math.abs(trees).toFixed(2) + ' t');
    }
    
    function setText(selector, value) {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            el.textContent = value;
        }
    }
    
    async function loadHistory() {
        try {
            const response = await fetch('/history');
            if (!response.ok) throw new Error('Failed to load history');
            
            const data = await response.json();
            if (!data.history || !Array.isArray(data.history)) return;
            
            const table = document.getElementById('dashboard-history-body');
            if (!table) return;
            
            table.innerHTML = '';
            
            let chartData = {
                labels: [],
                transport: [],
                housing: [],
                energy: [],
                total: []
            };
            
            const entries = data.history.slice(0, 6);
            entries.forEach((entry) => {
                if (!entry.search) return;
                const breakdown = entry.search.breakdown || {};
                const total = entry.search.total_kg_co2e || 0;
                const transport = (breakdown.Transport || 0) / 1000;
                const buildings = (breakdown.Buildings || 0) / 1000;
                const energy = ((breakdown.Electricity || 0) + (breakdown.EnhancedFuel || 0)) / 1000;
                const totalTonnes = total / 1000;
                
                const date = entry.time ? new Date(entry.time).toLocaleDateString() : 'N/A';
                chartData.labels.push(date);
                chartData.transport.push(transport);
                chartData.housing.push(buildings);
                chartData.energy.push(energy);
                chartData.total.push(totalTonnes);
                
                const row = document.createElement('tr');
                let status = 'Low';
                if (totalTonnes > 3.5) status = 'High';
                else if (totalTonnes > 2.5) status = 'Medium';
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>${transport.toFixed(2)} t</td>
                    <td>${buildings.toFixed(2)} t</td>
                    <td>${energy.toFixed(2)} t</td>
                    <td>${totalTonnes.toFixed(2)} t</td>
                    <td><span class="badge-status ${status.toLowerCase()}">${status}</span></td>
                `;
                table.appendChild(row);
            });
            
            if (entries.length === 0) {
                table.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#7e96b5;">No entries yet. Submit the form to add one.</td></tr>';
            }
            
            updateCharts(chartData);
        } catch (error) {
            console.error('Error loading history:', error);
            const table = document.getElementById('dashboard-history-body');
            if (table) {
                table.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#7e96b5;">Could not load history.</td></tr>';
            }
        }
    }
    
    function updateCharts(data) {
        const ctx1 = document.getElementById('categoryChart').getContext('2d');
        const ctx2 = document.getElementById('trendChart').getContext('2d');
        
        if (categoryChartInstance) {
            categoryChartInstance.destroy();
        }
        if (trendChartInstance) {
            trendChartInstance.destroy();
        }
        
        const avgTransport = data.transport.length ? (data.transport.reduce((a, b) => a + b) / data.transport.length) : 0;
        const avgHousing = data.housing.length ? (data.housing.reduce((a, b) => a + b) / data.housing.length) : 0;
        const avgEnergy = data.energy.length ? (data.energy.reduce((a, b) => a + b) / data.energy.length) : 0;
        
        categoryChartInstance = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Transport', 'Housing', 'Energy'],
                datasets: [{
                    data: [avgTransport, avgHousing, avgEnergy],
                    backgroundColor: ['#f5a623', '#4aa3ff', '#b388ff'],
                    borderColor: ['#0b0e14', '#0b0e14', '#0b0e14'],
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '64%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#c8d6e8',
                            font: { size: 12, weight: '500' },
                            padding: 16,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    }
                }
            }
        });
        
        trendChartInstance = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: data.labels.slice(0, 6),
                datasets: [{
                    label: 'tCO₂e',
                    data: data.total.slice(0, 6),
                    borderColor: '#00d474',
                    backgroundColor: 'rgba(0, 212, 116, 0.08)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#00d474',
                    pointBorderColor: '#0b0e14',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#c8d6e8', font: { size: 12 } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(2) + ' tCO₂e';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#7e96b5' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        ticks: { color: '#7e96b5' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                }
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        loadHistory();

        const calcView = document.getElementById('calc-view');
        const historyView = document.getElementById('history-view');
        const toggleBtn = document.getElementById('view-toggle-btn');
        const backBtn = document.getElementById('back-to-dashboard-btn');

        function showHistoryView() {
            calcView.style.display = 'none';
            historyView.style.display = 'block';
            toggleBtn.dataset.mode = 'history';
            toggleBtn.textContent = '📊 View Dashboard';
            if (window.location.hash !== '#history-view') {
                history.replaceState(null, '', '#history-view');
            }
        }

        function showCalcView() {
            historyView.style.display = 'none';
            calcView.style.display = '';
            toggleBtn.dataset.mode = 'calc';
            toggleBtn.textContent = '📋 View History';
            if (window.location.hash) {
                history.replaceState(null, '', window.location.pathname);
            }
        }

        toggleBtn.addEventListener('click', function() {
            if (toggleBtn.dataset.mode === 'history') {
                showCalcView();
            } else {
                showHistoryView();
            }
        });

        backBtn.addEventListener('click', showCalcView);

        if (window.location.hash === '#history-view') {
            showHistoryView();
        }
    });