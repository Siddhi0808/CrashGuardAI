import os
import psutil
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    # 1. Gather Telemetry
    cpu_pct = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    # 2. Crash Risk Prediction Formula
    risk_score = min(100.0, round(
        (cpu_pct * 0.35) + 
        (vm.percent * 0.40) + 
        (swap.percent * 0.15) + 
        (disk.percent * 0.10), 1
    ))

    # 3. Active & Sleeping Processes Inspection
    all_processes = []
    browser_tabs_suggestions = []
    
    known_browsers = {
        'chrome': ('Google Chrome', 'fa-chrome'),
        'safari': ('Safari Browser', 'fa-safari'),
        'firefox': ('Firefox Browser', 'fa-firefox'),
        'msedge': ('Microsoft Edge', 'fa-edge'),
        'brave': ('Brave Browser', 'fa-compass'),
        'arc': ('Arc Browser', 'fa-compass')
    }

    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            pinfo = proc.info
            name = pinfo['name'] or ''
            status = pinfo['status'] or 'unknown'
            mem_mb = round((pinfo['memory_info'].rss if pinfo['memory_info'] else 0) / (1024 ** 2), 1)
            mem_pct = pinfo['memory_percent'] or 0.0
            cpu_p = pinfo['cpu_percent'] or 0.0

            all_processes.append({
                'pid': pinfo['pid'],
                'name': name,
                'status': status,  # Captures 'sleeping', 'running', 'idle', etc.
                'cpu_percent': cpu_p,
                'memory_percent': mem_pct,
                'memory_mb': mem_mb
            })

            # Check if process is a browser tab consuming high memory
            name_lower = name.lower()
            for b_key, (b_name, icon_class) in known_browsers.items():
                if b_key in name_lower and (mem_mb > 150 or mem_pct > 3.0):
                    browser_tabs_suggestions.append({
                        'title': f'Close Heavy {b_name} Process/Tab',
                        'description': f'Process "{name}" ({status}) is taking {mem_mb} MB RAM ({mem_pct:.1f}%). Closing it frees system memory.',
                        'impact': f'{mem_mb} MB RAM',
                        'pid': pinfo['pid'],
                        'icon': icon_class,
                        'level': 'critical' if mem_mb > 400 else 'warning'
                    })
                    break

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    sorted_procs = sorted(all_processes, key=lambda x: x['memory_percent'], reverse=True)[:15]

    # 4. Storage & System Cleanup Suggestions
    cleanup_suggestions = []
    if vm.percent > 80:
        cleanup_suggestions.append({
            'title': f'High Memory Pressure ({vm.percent}% RAM Used)',
            'description': 'RAM resources are critically strained. Close sleeping background apps to avoid Out-Of-Memory system panics.',
            'icon': 'fa-memory',
            'level': 'critical'
        })

    if disk.percent > 85:
        cleanup_suggestions.append({
            'title': f'Low Storage Disk Space ({disk.percent}% Full)',
            'description': 'Storage is low, which prevents the OS from creating virtual swap files.',
            'icon': 'fa-hard-drive',
            'level': 'critical'
        })

    cache_dirs = [
        ("~/Library/Caches", "User App Caches", "Remove temporary application cache files."),
        ("/tmp", "System Temp Folder", "Clear temporary process cache directory."),
        ("~/.Trash", "System Trash Bin", "Empty trash bin to recover storage space.")
    ]

    for path_raw, title, desc in cache_dirs:
        expanded_path = os.path.expanduser(path_raw)
        if os.path.exists(expanded_path):
            cleanup_suggestions.append({
                'title': title,
                'description': desc,
                'path': path_raw,
                'icon': 'fa-folder-minus',
                'level': 'warning' if 'Trash' in title else 'info'
            })

    return jsonify({
        'cpu': {
            'percent': cpu_pct,
            'cores': psutil.cpu_count(logical=True)
        },
        'memory': {
            'percent': vm.percent,
            'used_gb': round(vm.used / (1024 ** 3), 2),
            'free_gb': round(vm.available / (1024 ** 3), 2),
            'total_gb': round(vm.total / (1024 ** 3), 2),
            'swap_percent': swap.percent
        },
        'disk': {
            'percent': disk.percent,
            'used_gb': round(disk.used / (1024 ** 3), 2),
            'free_gb': round(disk.free / (1024 ** 3), 2),
            'total_gb': round(disk.total / (1024 ** 3), 2)
        },
        'network': {
            'rx_mb': round(net.bytes_recv / (1024 ** 2), 2),
            'tx_mb': round(net.bytes_sent / (1024 ** 2), 2)
        },
        'crash_risk_score': risk_score,
        'process_count': len(all_processes),
        'processes': sorted_procs,
        'browser_tab_suggestions': browser_tabs_suggestions[:6],
        'cleanup_suggestions': cleanup_suggestions
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)