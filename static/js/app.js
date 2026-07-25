document.addEventListener("DOMContentLoaded", () => {
    initCharts();

    // 1. Sidebar Tab Switcher Fix
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            
            navItems.forEach(nav => nav.classList.remove("active"));
            tabContents.forEach(tab => tab.classList.remove("active"));

            item.classList.add("active");
            const tabId = item.getAttribute("data-tab");
            const activeTab = document.getElementById(`${tabId}-tab`);
            if (activeTab) activeTab.classList.add("active");

            const titleMap = {
                'overview': 'System Overview',
                'cpu': 'CPU Performance & Load',
                'memory': 'Memory Usage',
                'disk': 'Disk Storage Allocation',
                'network': 'Network Traffic',
                'processes': 'System Processes',
                'cleanup': 'Crash Prevention & Cleanup Recommendations'
            };
            pageTitle.innerText = titleMap[tabId] || 'System Dashboard';
        });
    });

    // 2. Refresh Metrics Telemetry
    async function updateMetrics() {
        try {
            const response = await fetch('/api/metrics');
            if (!response.ok) return;

            const data = await response.json();
            const timeStr = new Date().toLocaleTimeString();

            // Overview Values
            document.getElementById('ov-cpu').innerText = data.cpu.percent.toFixed(1);
            document.getElementById('ov-mem').innerText = data.memory.percent.toFixed(1);
            document.getElementById('ov-disk').innerText = data.disk.percent.toFixed(1);
            document.getElementById('ov-net-rx').innerText = data.network.rx_mb;
            document.getElementById('ov-proc-count').innerText = data.process_count;
            
            // Center Banner Crash Risk
            const riskVal = data.crash_risk_score;
            document.getElementById('ov-risk').innerText = riskVal.toFixed(1);
            const crashLbl = document.getElementById('crash-status-lbl');
            if (crashLbl) {
                if (riskVal > 70) {
                    crashLbl.innerText = "CRITICAL: System heavily loaded. Crash imminent!";
                    crashLbl.style.color = "#ef4444";
                } else if (riskVal > 35) {
                    crashLbl.innerText = "WARNING: Moderate system strain detected.";
                    crashLbl.style.color = "#f59e0b";
                } else {
                    crashLbl.innerText = "System operating within safe parameters.";
                    crashLbl.style.color = "#10b981";
                }
            }

            // CPU Tab
            document.getElementById('cpu-val').innerText = data.cpu.percent.toFixed(1);
            document.getElementById('cpu-cores').innerText = data.cpu.cores;

            // Memory Tab
            document.getElementById('mem-used').innerText = data.memory.used_gb;
            document.getElementById('mem-total').innerText = data.memory.total_gb;
            document.getElementById('swap-val').innerText = data.memory.swap_percent.toFixed(1);

            // Disk Tab
            document.getElementById('disk-used').innerText = data.disk.used_gb;
            document.getElementById('disk-total').innerText = data.disk.total_gb;

            // Network Tab
            document.getElementById('net-rx').innerText = data.network.rx_mb;
            document.getElementById('net-tx').innerText = data.network.tx_mb;

            // Header Status Badge
            const badge = document.getElementById('status-badge');
            if (riskVal > 70) {
                badge.className = "status-badge badge-critical-crash";
                badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> HIGH CRASH RISK';
            } else if (riskVal > 35) {
                badge.className = "status-badge badge-warning";
                badge.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Moderate Risk';
            } else {
                badge.className = "status-badge badge-normal";
                badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> System Healthy';
            }

            // Update Overview Line Chart
            pushChartData(overviewChart, timeStr, [
                data.crash_risk_score,
                data.cpu.percent,
                data.memory.percent,
                data.disk.percent,
                data.network.rx_mb,
                data.network.tx_mb
            ]);

            // Update Specific Tab Line Charts
            pushChartData(cpuChart, timeStr, [data.cpu.percent]);
            pushChartData(networkChart, timeStr, [data.network.rx_mb, data.network.tx_mb]);

            // Update Donut Charts
            if (memoryDoughnutChart) {
                memoryDoughnutChart.data.datasets[0].data = [data.memory.used_gb, data.memory.free_gb];
                memoryDoughnutChart.update();
            }

            if (diskChart) {
                diskChart.data.datasets[0].data = [data.disk.used_gb, data.disk.free_gb];
                diskChart.update();
            }

            // Render Browser Tab Cleanup Recommendations
            const tabBox = document.getElementById('browser-tab-suggestions');
            if (tabBox && data.browser_tab_suggestions) {
                tabBox.innerHTML = '';
                if (data.browser_tab_suggestions.length === 0) {
                    tabBox.innerHTML = '<p class="loading-txt">No memory-heavy web browser tabs detected.</p>';
                } else {
                    data.browser_tab_suggestions.forEach(item => {
                        const div = document.createElement('div');
                        div.className = `suggestion-item ${item.level}`;
                        div.innerHTML = `
                            <div class="suggest-info">
                                <h4><i class="fa-brands ${item.icon || 'fa-chrome'}"></i> ${item.title}</h4>
                                <p>${item.description}</p>
                                <small>Impact: <strong>${item.impact}</strong> | PID: <code>${item.pid}</code></small>
                            </div>
                        `;
                        tabBox.appendChild(div);
                    });
                }
            }

            // Render Storage Cleanup Suggestions
            const cleanupList = document.getElementById('cleanup-suggestions');
            if (cleanupList && data.cleanup_suggestions) {
                cleanupList.innerHTML = '';
                data.cleanup_suggestions.forEach(item => {
                    const div = document.createElement('div');
                    div.className = `suggestion-item ${item.level}`;
                    div.innerHTML = `
                        <div class="suggest-info">
                            <h4><i class="fa-solid ${item.icon}"></i> ${item.title}</h4>
                            <p>${item.description}</p>
                            ${item.path ? `<small>Path: <code>${item.path}</code></small>` : ''}
                        </div>
                    `;
                    cleanupList.appendChild(div);
                });
            }

            // Render Processes Table
            const tbody = document.getElementById('process-table-body');
            if (tbody && data.processes) {
                tbody.innerHTML = '';
                data.processes.forEach(proc => {
                    const tr = document.createElement('tr');
                    const statusClass = proc.status === 'running' ? 'proc-running' : 'proc-sleeping';
                    tr.innerHTML = `
                        <td>${proc.pid}</td>
                        <td><strong>${proc.name}</strong></td>
                        <td><span class="status-tag ${statusClass}">${proc.status}</span></td>
                        <td>${proc.cpu_percent.toFixed(1)}%</td>
                        <td>${proc.memory_percent.toFixed(1)}%</td>
                        <td>${proc.memory_mb.toFixed(1)} MB</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

        } catch (err) {
            console.error("Failed fetching live telemetry:", err);
        }
    }

    updateMetrics();
    setInterval(updateMetrics, 2000);
});