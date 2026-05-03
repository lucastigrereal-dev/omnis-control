import psutil
import shutil

DISK_CRITICAL_THRESHOLD = 10
DISK_WARNING_THRESHOLD = 20


def check() -> dict:
    all_disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            info = {
                "mount": part.mountpoint,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent_free": round(100 - usage.percent, 1),
                "percent_used": usage.percent,
            }
            all_disks.append(info)
        except PermissionError:
            continue

    critical_disks = [d for d in all_disks if d["percent_free"] < DISK_CRITICAL_THRESHOLD]
    warning_disks = [
        d for d in all_disks
        if DISK_CRITICAL_THRESHOLD <= d["percent_free"] < DISK_WARNING_THRESHOLD
    ]

    severity = "ok"
    if critical_disks:
        severity = "critical"
    elif warning_disks:
        severity = "warning"

    return {
        "severity": severity,
        "disks": all_disks,
        "critical": [d["mount"] for d in critical_disks],
        "warning": [d["mount"] for d in warning_disks],
        "summary": (
            f"Discos críticos: {[d['mount'] for d in critical_disks]}, "
            f"Discos em alerta: {[d['mount'] for d in warning_disks]}"
            if critical_disks or warning_disks
            else "Ok"
        ),
    }
