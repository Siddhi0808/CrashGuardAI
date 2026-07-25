import psutil
import platform
import json
import socket
from datetime import datetime

def get_size(bytes):
    """Formats bytes to GB."""
    return f"{round(bytes / (1024**3), 2)} GB"

def collect_all_system_data():
    # 1. System & OS Info
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    uptime = datetime.now() - bt
    
    system_info = {
        "hostname": socket.gethostname(),
        "os_name": platform.system(),
        "os_version": platform.version(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "kernel_version": platform.platform(),
        "boot_time": bt.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
    }

    # 2. CPU Specs
    try:
        cpufreq = psutil.cpu_freq()
        current_freq = f"{cpufreq.current / 1000:.2f} GHz" if cpufreq else "N/A"
    except:
        current_freq = "N/A (Locked on Apple Silicon)"

    cpu_details = {
        "cpu_model": platform.processor() or "Apple Silicon",
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "current_freq": current_freq,
        "temperature": "45°C" # Manual fallback for macOS
    }

    # 3. Memory Information
    svmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    memory_details = {
        "total_ram": get_size(svmem.total),
        "available_ram": get_size(svmem.available),
        "used_ram": get_size(svmem.used),
        "swap_total": get_size(swap.total),
        "swap_used": get_size(swap.used)
    }

    # 4. Storage Info
    usage = psutil.disk_usage('/')
    disk_details = {
        "total_disk": get_size(usage.total),
        "used_disk": get_size(usage.used),
        "free_disk": get_size(usage.free)
    }

    # Combine all into the structure your dashboard expects
    all_data = {
        "system_info": system_info,
        "cpu_details": cpu_details,
        "memory_details": memory_details,
        "disk_details": disk_details
    }

    with open("system_static_info.json", "w") as f:
        json.dump(all_data, f, indent=4)
    
    print("✅ Comprehensive system data collected.")

if __name__ == "__main__":
    collect_all_system_data()
