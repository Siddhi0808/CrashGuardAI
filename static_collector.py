import socket
import platform
import psutil
import shutil
from db import get_connection


def get_or_create_host():
    hostname = socket.gethostname()
    machine_type = platform.machine()
    os_name = platform.system()
    os_version = platform.version()
    kernel_version = platform.release()
    architecture = platform.architecture()[0]
    cpu_model = platform.processor()

    total_ram_bytes = psutil.virtual_memory().total
    total_disk_bytes = shutil.disk_usage("/").total
    physical_cores = psutil.cpu_count(logical=False)
    logical_cores = psutil.cpu_count(logical=True)

    print("hostname:", hostname, len(hostname))
    print("machine_type:", machine_type, len(machine_type))
    print("os_name:", os_name, len(os_name))
    print("os_version:", os_version, len(os_version))
    print("kernel_version:", kernel_version, len(kernel_version))
    print("architecture:", architecture, len(architecture))
    print("cpu_model:", cpu_model, len(cpu_model))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT host_id FROM hosts WHERE hostname = %s", (hostname,))
    row = cur.fetchone()

    if row:
        host_id = row[0]
    else:
        cur.execute("""
            INSERT INTO hosts (
                hostname, machine_type, os_name, os_version, kernel_version,
                architecture, cpu_model, total_ram_bytes, total_disk_bytes,
                physical_cores, logical_cores
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING host_id
        """, (
            hostname,
            machine_type,
            os_name,
            os_version,
            kernel_version,
            architecture,
            cpu_model,
            total_ram_bytes,
            total_disk_bytes,
            physical_cores,
            logical_cores
        ))
        host_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return host_id


def insert_cpu_details(host_id):
    try:
        freq = psutil.cpu_freq()
        freq_current = freq.current if freq else None
        freq_min = freq.min if freq else None
        freq_max = freq.max if freq else None
    except Exception:
        freq_current = None
        freq_min = None
        freq_max = None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO cpu_details (
            host_id, cpu_model, physical_cores, logical_cores,
            freq_current_mhz, freq_min_mhz, freq_max_mhz
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        host_id,
        platform.processor(),
        psutil.cpu_count(logical=False),
        psutil.cpu_count(logical=True),
        freq_current,
        freq_min,
        freq_max
    ))

    conn.commit()
    cur.close()
    conn.close()


def insert_disk_devices(host_id):
    partitions = psutil.disk_partitions()

    conn = get_connection()
    cur = conn.cursor()

    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            cur.execute("""
                INSERT INTO disk_devices (
                    host_id, device_name, mountpoint, filesystem_type, total_bytes
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                host_id,
                part.device,
                part.mountpoint,
                part.fstype,
                usage.total
            ))
        except Exception:
            continue

    conn.commit()
    cur.close()
    conn.close()


def insert_network_interfaces(host_id):
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    conn = get_connection()
    cur = conn.cursor()

    for iface, addr_list in addrs.items():
        mac_address = None

        for addr in addr_list:
            if str(addr.family) == "-1" or str(addr.family) == "AddressFamily.AF_LINK":
                mac_address = addr.address

        iface_stat = stats.get(iface)
        speed = iface_stat.speed if iface_stat else None
        status = "up" if iface_stat and iface_stat.isup else "down"

        cur.execute("""
            INSERT INTO network_interfaces (
                host_id, interface_name, mac_address, speed_mbps, status
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            host_id,
            iface,
            mac_address,
            speed,
            status
        ))

    conn.commit()
    cur.close()
    conn.close()


def collect_static_info():
    host_id = get_or_create_host()
    insert_cpu_details(host_id)
    insert_disk_devices(host_id)
    insert_network_interfaces(host_id)
    print("Static info collected for host_id =", host_id)
    return host_id


if __name__ == "__main__":
    collect_static_info()
