let overviewChart, cpuChart, memoryDoughnutChart, diskChart, networkChart;

function initCharts() {
    const defaultScales = {
        y: { beginAtZero: true, ticks: { color: '#94a3b8' } },
        x: { ticks: { color: '#94a3b8' } }
    };

    // 1. Overview Chart
    const ctxOv = document.getElementById('overviewChart');
    if (ctxOv) {
        overviewChart = new Chart(ctxOv, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Crash Risk (%)', data: [], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.2)', borderWidth: 2, tension: 0.3, fill: true },
                    { label: 'CPU Usage (%)', data: [], borderColor: '#3b82f6', tension: 0.3 },
                    { label: 'RAM Usage (%)', data: [], borderColor: '#10b981', tension: 0.3 },
                    { label: 'Disk Used (%)', data: [], borderColor: '#f59e0b', tension: 0.3 },
                    { label: 'Network Rx (MB)', data: [], borderColor: '#a855f7', tension: 0.3 },
                    { label: 'Network Tx (MB)', data: [], borderColor: '#38bdf8', tension: 0.3 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: defaultScales, plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });
    }

    // 2. CPU Chart
    const ctxCpu = document.getElementById('cpuChart');
    if (ctxCpu) {
        cpuChart = new Chart(ctxCpu, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{ label: 'CPU Load (%)', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.3 }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { ...defaultScales, y: { beginAtZero: true, max: 100 } }, plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });
    }

    // 3. Memory Donut Chart
    const ctxMem = document.getElementById('memoryDoughnutChart');
    if (ctxMem) {
        memoryDoughnutChart = new Chart(ctxMem, {
            type: 'doughnut',
            data: {
                labels: ['Used RAM (GB)', 'Free RAM (GB)'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#10b981', '#334155'],
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });
    }

    // 4. Disk Donut Chart
    const ctxDisk = document.getElementById('diskChart');
    if (ctxDisk) {
        diskChart = new Chart(ctxDisk, {
            type: 'doughnut',
            data: {
                labels: ['Used Storage (GB)', 'Free Storage (GB)'],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#ef4444', '#334155'],
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });
    }

    // 5. Network Chart
    const ctxNet = document.getElementById('networkChart');
    if (ctxNet) {
        networkChart = new Chart(ctxNet, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Received - Rx (MB)', data: [], borderColor: '#a855f7', backgroundColor: 'rgba(168, 85, 247, 0.1)', tension: 0.3 },
                    { label: 'Transmitted - Tx (MB)', data: [], borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', tension: 0.3 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: defaultScales, plugins: { legend: { labels: { color: '#f8fafc' } } } }
        });
    }
}

function pushChartData(chart, label, values) {
    if (!chart) return;
    if (chart.data.labels.length >= 12) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(ds => ds.data.shift());
    }
    chart.data.labels.push(label);
    values.forEach((val, idx) => {
        if (chart.data.datasets[idx]) {
            chart.data.datasets[idx].data.push(val);
        }
    });
    chart.update();
}