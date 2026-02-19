import argparse
import json
import random
import socket
import sys
import time
import logging
from dataclasses import dataclass
from datetime import datetime
import os
import threading
import urllib.request
import urllib.error
import subprocess

import psutil
import requests


# Set up basic logging for the agent itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
agent_logger = logging.getLogger(__name__)


@dataclass
class Intervals:
    cpu_s: float
    ram_s: float
    disk_usage_s: float
    disk_io_s: float
    load_s: float
    net_s: float
    uptime_s: float
    db_s: float


def _now() -> float:
    return time.time()


def _sleep_until(deadline: float):
    while True:
        remaining = deadline - _now()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.5))


def _loadavg():
    try:
        la = psutil.getloadavg()
        return {"1": float(la[0]), "5": float(la[1]), "15": float(la[2])}
    except (AttributeError, OSError):
        return {}


def _disk_partitions():
    parts = []
    for p in psutil.disk_partitions(all=False):
        if not p.mountpoint:
            continue
        parts.append(p)
    return parts


def _disk_usage_samples():
    samples = []
    for p in _disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
        except OSError:
            continue
        samples.append(
            {
                "mount": p.mountpoint,
                "fstype": p.fstype or "",
                "total_bytes": int(u.total),
                "used_bytes": int(u.used),
                "percent": float(u.percent),
            }
        )
    return samples


def _disk_io():
    try:
        io = psutil.disk_io_counters()
    except Exception:
        return {}
    if io is None:
        return {}

    out = {
        "read_bytes": int(getattr(io, "read_bytes", 0) or 0),
        "write_bytes": int(getattr(io, "write_bytes", 0) or 0),
    }

    if hasattr(io, "read_time"):
        out["read_time_ms"] = int(getattr(io, "read_time", 0) or 0)
    if hasattr(io, "write_time"):
        out["write_time_ms"] = int(getattr(io, "write_time", 0) or 0)

    return out


def _net_io():
    try:
        io = psutil.net_io_counters()
    except Exception:
        return {}
    if io is None:
        return {}

    def _get(name: str):
        return int(getattr(io, name, 0) or 0)

    return {
        "bytes_sent": _get("bytes_sent"),
        "bytes_recv": _get("bytes_recv"),
        "packets_sent": _get("packets_sent"),
        "packets_recv": _get("packets_recv"),
        "errin": _get("errin"),
        "errout": _get("errout"),
        "dropin": _get("dropin"),
        "dropout": _get("dropout"),
    }


def _boot_time_epoch() -> float | None:
    try:
        return float(psutil.boot_time())
    except Exception:
        return None


def _uptime_payload() -> dict:
    boot = _boot_time_epoch()
    if boot is None:
        return {}
    return {
        "boot_time": boot,
        "uptime_seconds": int(max(0.0, _now() - boot)),
    }


def _ram_payload() -> dict:
    vm = psutil.virtual_memory()
    return {
        "total_bytes": int(vm.total),
        "used_bytes": int(vm.total - vm.available),
        "percent": float(vm.percent),
    }


def _cpu_payload() -> dict:
    return {"percent": float(psutil.cpu_percent(interval=None))}


def _post(session: requests.Session, url: str, token: str, payload: dict, timeout_s: float):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "serverwatch-agent/1.0",
    }
    agent_logger.info(f"Sending data to {url} with token (prefix): {token[:8] if token else 'None'}")
    resp = session.post(url, data=json.dumps(payload), headers=headers, timeout=timeout_s)
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _tcp_check(host: str, port: int, timeout_s: float) -> tuple[bool, float | None]:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            pass
        ms = (time.perf_counter() - start) * 1000.0
        return True, ms
    except OSError:
        return False, None


def _mysql_process_up() -> bool | None:
    try:
        for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
            name = (p.info.get("name") or "").lower()
            if name in {"mysqld", "mariadbd"}:
                return True
            exe = (p.info.get("exe") or "").lower()
            if exe.endswith("/mysqld") or exe.endswith("/mariadbd"):
                return True
            cmd = " ".join((p.info.get("cmdline") or [])).lower()
            if "mysqld" in cmd or "mariadbd" in cmd:
                return True
        return False
    except Exception:
        return None


def _mysql_avg_query_ms(cur) -> float | None:
    try:
        cur.execute(
            "SELECT SUM_SUM_TIMER_WAIT, SUM_COUNT_STAR "
            "FROM performance_schema.events_statements_summary_global_by_event_name "
            "WHERE EVENT_NAME LIKE 'statement/sql/%'"
        )
        rows = cur.fetchall() or []
    except Exception:
        return None

    total_wait = 0.0
    total_count = 0
    for r in rows:
        try:
            total_wait += float(r[0] or 0)
            total_count += int(r[1] or 0)
        except Exception:
            continue
    if total_count <= 0:
        return None
    return (total_wait / total_count) / 1e9


def _mysql_histogram_percentiles(cur) -> tuple[float | None, float | None]:
    try:
        cur.execute(
            "SELECT BUCKET_NUMBER, BUCKET_TIMER_HIGH, COUNT_BUCKET "
            "FROM performance_schema.events_statements_histogram_global ORDER BY BUCKET_NUMBER"
        )
        rows = cur.fetchall() or []
    except Exception:
        return None, None

    total = 0
    for r in rows:
        try:
            total += int(r[2] or 0)
        except Exception:
            continue
    if total <= 0:
        return None, None

    target95 = total * 0.95
    target99 = total * 0.99
    c = 0
    p95 = None
    p99 = None
    for r in rows:
        try:
            high_ps = float(r[1] or 0)
            cnt = int(r[2] or 0)
        except Exception:
            continue
        c += cnt
        if p95 is None and c >= target95:
            p95 = high_ps / 1e9
        if p99 is None and c >= target99:
            p99 = high_ps / 1e9
        if p95 is not None and p99 is not None:
            break
    return p95, p99


def _mysql_slow_count_1m(cur) -> int | None:
    try:
        cur.execute(
            "SELECT COUNT(*) FROM mysql.slow_log WHERE start_time > (NOW() - INTERVAL 1 MINUTE)"
        )
        row = cur.fetchone()
        if not row:
            return None
        return int(row[0] or 0)
    except Exception:
        return None


def _mysql_metrics(
    *, host: str, port: int, db_name: str, user: str, password: str, timeout_s: float, last_counters: dict | None, last_ts: float | None,
):
    try:
        import pymysql
    except Exception as e:
        agent_logger.error(f"pymysql not installed (pip install -r requirements.txt): {e}")
        return ({}, {}, {})

    process_up = _mysql_process_up()
    port_ok, port_ms = _tcp_check(host, int(port), timeout_s=timeout_s)

    connect_ok = False
    ping_ms = None

    counters: dict[str, int] = {}
    current_connections = None
    max_connections = None
    conn_usage_pct = None

    avg_query_ms = None
    p95_query_ms = None
    p99_query_ms = None
    slow_1m = None

    start = time.perf_counter()
    conn = None
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=db_name,
            connect_timeout=timeout_s,
            read_timeout=timeout_s,
            write_timeout=timeout_s,
            autocommit=True,
        )
        connect_ok = True

        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
            ping_ms = (time.perf_counter() - start) * 1000.0

            cur.execute("SHOW GLOBAL STATUS")
            for k, v in (cur.fetchall() or []):
                key = str(k)
                if key == "Threads_connected":
                    try:
                        current_connections = int(v)
                    except Exception:
                        current_connections = None
                    continue
                if key in {
                    "Queries",
                    "Questions",
                    "Com_select",
                    "Com_insert",
                    "Com_update",
                    "Com_delete",
                    "Com_commit",
                    "Com_rollback",
                }:
                    try:
                        counters[key] = int(v)
                    except Exception:
                        pass

            cur.execute("SHOW VARIABLES WHERE Variable_name='max_connections'")
            row = cur.fetchone()
            if row and len(row) >= 2:
                try:
                    max_connections = int(row[1])
                except Exception:
                    max_connections = None

            if current_connections is not None and max_connections:
                conn_usage_pct = (float(current_connections) / float(max_connections)) * 100.0

            avg_query_ms = _mysql_avg_query_ms(cur)
            p95_query_ms, p99_query_ms = _mysql_histogram_percentiles(cur)
            slow_1m = _mysql_slow_count_1m(cur)
    except Exception as e:
        agent_logger.error(f"MySQL connection or query error: {e}")
        connect_ok = False
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    qps = None
    read_qps = None
    write_qps = None
    tps = None
    now_ts = _now()

    if last_counters and last_ts is not None:
        dt = max(0.001, now_ts - float(last_ts))
        try:
            dq = int(counters.get("Queries", 0)) - int(last_counters.get("Queries", 0))
            dsel = int(counters.get("Com_select", 0)) - int(last_counters.get("Com_select", 0))
            dins = int(counters.get("Com_insert", 0)) - int(last_counters.get("Com_insert", 0))
            dupd = int(counters.get("Com_update", 0)) - int(last_counters.get("Com_update", 0))
            ddel = int(counters.get("Com_delete", 0)) - int(last_counters.get("Com_delete", 0))
            dcom = int(counters.get("Com_commit", 0)) - int(last_counters.get("Com_commit", 0))
            drol = int(counters.get("Com_rollback", 0)) - int(last_counters.get("Com_rollback", 0))
            if dq >= 0:
                qps = dq / dt
            if dsel >= 0:
                read_qps = dsel / dt
            dwrite = dins + dupd + ddel
            if dwrite >= 0:
                write_qps = dwrite / dt
            dtps = dcom + drol
            if dtps >= 0:
                tps = dtps / dt
        except Exception:
            pass

    return (
        {
            "engine": "mysql",
            "process_up": process_up,
            "port_ok": port_ok,
            "connect_ok": connect_ok,
            "ping_ms": ping_ms,
            "current_connections": current_connections,
            "max_connections": max_connections,
            "connection_usage_percent": conn_usage_pct,
            "qps": qps,
            "read_qps": read_qps,
            "write_qps": write_qps,
            "tps": tps,
            "avg_query_ms": avg_query_ms,
            "p95_query_ms": p95_query_ms,
            "p99_query_ms": p99_query_ms,
            "slow_queries_1m": slow_1m,
            "counters": counters,
        },
        counters,
        now_ts,
    )

class ServerAgent:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = os.path.expanduser("~/.config/serverwatch-agent/config.json")
        self.config = self.load_config(config_file)
        self.setup_logging()
        agent_logger.info(f"Agent initialized with config: {{'server_url': self.config.get('server_url'), 'agent_token_prefix': self.config.get('agent_token')[:8] if self.config.get('agent_token') else 'None'}}")
        self.running = False
        self.server_id = self.get_server_id()
        self.last_metrics_time = 0
        self.last_heartbeat_time = 0
        
    def load_config(self, config_file):
        """Load agent configuration"""
        default_config = {
            "server_url": "http://192.168.253.23:8001", # Updated default to match current setup
            "agent_token": "",
            "metrics_interval": 30,
            "heartbeat_interval": 60,
            "log_level": "INFO",
            "retry_attempts": 3,
            "retry_delay": 5,
            "monitored_directories": [],
            "directory_timeout": 30
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                agent_logger.error(f"Error loading config from {config_file}: {e}")
        return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = os.path.expanduser('~/logs/serverwatch-agent.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config["log_level"]),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) # Also log to stdout
            ]
        )
        self.logger = logging.getLogger(__name__) # Use specific logger for instance
    
    def get_server_id(self):
        """Generate unique server ID"""
        try:
            hostname = socket.gethostname()
            # Try to get IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80)) # Public DNS to get external IP
                ip = s.getsockname()[0]
                s.close()
                return f"{hostname}-{ip.replace('.', '-')}"
            except Exception as e:
                self.logger.warning(f"Could not determine external IP for server ID: {e}. Using hostname only.")
                return hostname
        except Exception as e:
            self.logger.error(f"Error getting server ID: {e}")
            return "unknown-server"
    
    def _read_proc_file(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.debug(f"Could not read proc file {path}: {e}")
            return None

    def get_system_metrics(self):
        """Collect system metrics using standard library only"""
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "server_id": self.server_id,
                "cpu": {"percent": 0, "count": 1, "load_1m": 0, "load_5m": 0, "load_15m": 0},
                "memory": {"total": 0, "available": 0, "percent": 0, "used": 0, "free": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "percent": 0},
                "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                "system": {"uptime_seconds": 0, "process_count": 0, "hostname": socket.gethostname()}
            }

            # 1. Load Average
            try:
                load = os.getloadavg()
                metrics["cpu"]["load_1m"] = load[0]
                metrics["cpu"]["load_5m"] = load[1]
                metrics["cpu"]["load_15m"] = load[2]
            except Exception:
                # Fallback for systems without os.getloadavg (e.g., macOS older versions, busybox)
                load_data = self._read_proc_file('/proc/loadavg')
                if load_data:
                    try:
                        parts = load_data.split()
                        metrics["cpu"]["load_1m"] = float(parts[0])
                        metrics["cpu"]["load_5m"] = float(parts[1])
                        metrics["cpu"]["load_15m"] = float(parts[2])
                    except Exception as e:
                        self.logger.debug(f"Error parsing /proc/loadavg: {e}")

            # 2. CPU Count & Usage (Simplified approximation)
            cpu_info = self._read_proc_file('/proc/cpuinfo')
            if cpu_info:
                metrics["cpu"]["count"] = cpu_info.count('processor\t:') or 1
            
            # CPU Percent calculation requires two samples, we'll do a simple 1s sleep for the first one
            # or just use the load average as a proxy if we want to be very fast.
            # Here we'll read /proc/stat
            stat1 = self._read_proc_file('/proc/stat')
            if stat1:
                def get_cpu_times(stat_content):
                    line = stat_content.splitlines()[0]
                    parts = [float(x) for x in line.split()[1:]]
                    idle = parts[3]
                    total = sum(parts)
                    return idle, total
                
                i1, t1 = get_cpu_times(stat1)
                time.sleep(0.1) # Small sleep for sampling
                stat2 = self._read_proc_file('/proc/stat')
                if stat2:
                    i2, t2 = get_cpu_times(stat2)
                    dt = t2 - t1
                    di = i2 - i1
                    if dt > 0:
                        metrics["cpu"]["percent"] = max(0, min(100, 100 * (dt - di) / dt))

            # 3. Memory
            mem_info = self._read_proc_file('/proc/meminfo')
            if mem_info:
                mem = {}
                for line in mem_info.splitlines():
                    parts = line.split(':')
                    if len(parts) == 2:
                        name = parts[0].strip()
                        val = int(parts[1].split()[0]) * 1024 # KB to Bytes
                        mem[name] = val
                
                total = mem.get('MemTotal', 0)
                free = mem.get('MemFree', 0)
                buffers = mem.get('Buffers', 0)
                cached = mem.get('Cached', 0)
                available = mem.get('MemAvailable', free + buffers + cached)
                used = total - available
                
                metrics["memory"] = {
                    "total": total,
                    "available": available,
                    "percent": (used / total * 100) if total > 0 else 0,
                    "used": used,
                    "free": free
                }

            # 4. Disk (Root partition)
            try:
                st = os.statvfs('/')
                total = st.f_blocks * st.f_frsize
                free = st.f_bavail * st.f_frsize
                used = total - free
                metrics["disk"] = {
                    "total": total,
                    "used": used,
                    "free": free,
                    "percent": (used / total * 100) if total > 0 else 0
                }
            except Exception as e:
                self.logger.debug(f"Error collecting disk metrics: {e}")

            # 5. Uptime
            uptime_data = self._read_proc_file('/proc/uptime')
            if uptime_data:
                try:
                    metrics["system"]["uptime_seconds"] = float(uptime_data.split()[0])
                except Exception as e:
                    self.logger.debug(f"Error parsing uptime: {e}")

            # 6. Process Count
            try:
                pids = [p for p in os.listdir('/proc') if p.isdigit()]
                metrics["system"]["process_count"] = len(pids)
            except Exception as e:
                self.logger.debug(f"Error counting processes: {e}")

            # 7. Directory Metrics
            directory_metrics = []
            if self.config.get("monitored_directories"):
                for path in self.config["monitored_directories"]:
                    dir_metrics = self.get_directory_metrics(path, timeout=self.config.get("directory_timeout", 30))
                    directory_metrics.append(dir_metrics)
            metrics["directory_metrics"] = directory_metrics

            # 8. SSL Metrics
            ssl_certs = self.discover_ssl_certificates()
            metrics["ssl_metrics"] = self.get_ssl_metrics(ssl_certs)

            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None

    def discover_ssl_certificates(self):
        """Automatically discover SSL certificates in standard paths"""
        standard_paths = [
            "/etc/letsencrypt/live",
            "/etc/ssl/certs",
            "/usr/local/etc/letsencrypt/live"
        ]
        found_certs = []
        for base_path in standard_paths:
            if os.path.exists(base_path) and os.path.isdir(base_path):
                try:
                    for entry in os.listdir(base_path):
                        full_entry = os.path.join(base_path, entry)
                        if os.path.isdir(full_entry):
                            # Look for common cert names in subdirectories (Let's Encrypt style)
                            for cert_name in ["fullchain.pem", "cert.pem"]:
                                cert_path = os.path.join(full_entry, cert_name)
                                if os.path.exists(cert_path):
                                    found_certs.append(cert_path)
                                    break
                        elif entry.endswith(".pem") or entry.endswith(".crt"):
                            found_certs.append(full_entry)
                except Exception as e:
                    self.logger.debug(f"Error discovering certs in {base_path}: {e}")
        return found_certs

    def get_ssl_metrics(self, paths, timeout=10):
        """Get metrics for SSL certificates at given paths using openssl command"""
        results = []
        for path in paths:
            if not os.path.exists(path):
                self.logger.warning(f"SSL certificate path {path} does not exist.")
                continue
                
            cert_info = {
                "path": path,
                "common_name": None,
                "expiry_date": None,
                "days_remaining": None,
                "issuer": None,
                "status": "error",
                "error": None
            }
            
            try:
                # 1. Get expiry date
                cmd_expiry = f"openssl x509 -enddate -noout -in {path}"
                proc = subprocess.run(cmd_expiry, shell=True, capture_output=True, text=True, timeout=timeout)
                if proc.returncode == 0:
                    # Output: notAfter=Jan 27 23:59:59 2027 GMT
                    line = proc.stdout.strip()
                    if "notAfter=" in line:
                        date_str = line.split("notAfter=")[1]
                        cert_info["expiry_date"] = date_str
                        # Parse date to calculate days remaining
                        # Format: Jan 27 23:59:59 2027 GMT
                        try:
                            # Strip GMT if present for strptime
                            clean_date = date_str.replace("GMT", "").strip()
                            expiry_dt = datetime.strptime(clean_date, "%b %d %H:%M:%S %Y")
                            diff = expiry_dt - datetime.utcnow()
                            cert_info["days_remaining"] = diff.days
                        except Exception as e:
                            self.logger.warning(f"Error parsing expiry date for {path}: {e}")
                else:
                    cert_info["error"] = f"OpenSSL expiry command failed: {proc.stderr.strip()}"
                
                # 2. Get Subject and Issuer
                cmd_meta = f"openssl x509 -subject -issuer -noout -in {path}"
                proc = subprocess.run(cmd_meta, shell=True, capture_output=True, text=True, timeout=timeout)
                if proc.returncode == 0:
                    # Output: 
                    # subject=CN = example.com
                    # issuer=C = US, O = Let's Encrypt, CN = R3
                    lines = proc.stdout.strip().splitlines()
                    for line in lines:
                        if "subject=" in line:
                            if "CN =" in line:
                                cert_info["common_name"] = line.split("CN =")[1].split(",")[0].strip()
                        if "issuer=" in line:
                            if "O =" in line:
                                cert_info["issuer"] = line.split("O =")[1].split(",")[0].strip()
                            elif "CN =" in line:
                                cert_info["issuer"] = line.split("CN =")[1].split(",")[0].strip()
                else:
                    cert_info["error"] = f"OpenSSL meta command failed: {proc.stderr.strip()}"

                if not cert_info["error"]:
                    cert_info["status"] = "ok"
            except subprocess.TimeoutExpired:
                cert_info["error"] = f"OpenSSL command for {path} timed out"
            except Exception as e:
                cert_info["error"] = str(e)
                self.logger.error(f"Error getting SSL metrics for {path}: {e}")
                
            results.append(cert_info)
        return results

    def get_directory_metrics(self, path, timeout=30): # Increased default timeout
        """Get metrics for the most recently modified subdirectory within a given path"""
        result = {
            "path": path,
            "newest_folder_name": None,
            "newest_folder_size_mb": None,
            "newest_folder_last_modified": None,
            "status": "error",
            "error": "Unknown error"
        }

        if not os.path.exists(path):
            result["error"] = "Directory not found"
            return result

        if not os.path.isdir(path):
            result["error"] = "Not a directory"
            return result

        # Find the most recently modified subdirectory
        newest_subdir = None
        newest_mtime = 0
        
        try:
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    mtime = os.path.getmtime(full_path)
                    if mtime > newest_mtime:
                        newest_mtime = mtime
                        newest_subdir = full_path
        except Exception as e:
            result["error"] = f"Error finding newest subdirectory: {str(e)}"
            self.logger.error(f"Error in get_directory_metrics (listdir) for {path}: {e}")
            return result
        
        if not newest_subdir:
            result["error"] = "No subdirectories found"
            result["status"] = "ok" # No error, just no subdirs
            return result

        result["newest_folder_name"] = os.path.basename(newest_subdir)

        # Get size of the newest subdirectory
        try:
            cmd_size = f"du -sm {newest_subdir}"
            proc = subprocess.run(cmd_size, shell=True, capture_output=True, text=True, timeout=timeout)
            if proc.returncode == 0:
                size_str = proc.stdout.strip().split('\t')[0]
                result["newest_folder_size_mb"] = int(size_str)
            else:
                result["error"] = f"Size command failed for {os.path.basename(newest_subdir)}: {proc.stderr.strip()}"
                self.logger.error(f"Error in get_directory_metrics (du -sm) for {path}: {proc.stderr.strip()}")
                return result
        except subprocess.TimeoutExpired:
            result["error"] = f"Size command for {os.path.basename(newest_subdir)} timed out"
            self.logger.error(f"Timeout in get_directory_metrics (du -sm) for {path}")
            return result
        except Exception as e:
            result["error"] = f"Size error for {os.path.basename(newest_subdir)}: {str(e)}"
            self.logger.error(f"Error in get_directory_metrics (du -sm) for {path}: {e}")
            return result

        # Get last modified time of the newest subdirectory
        try:
            result["newest_folder_last_modified"] = datetime.fromtimestamp(newest_mtime).isoformat()
        except Exception:
            result["newest_folder_last_modified"] = None # Should not happen if newest_mtime is set

        result["status"] = "ok"
        result["error"] = None
        return result
    
    def send_with_retry(self, endpoint, data, max_retries=None):
        """Send data using urllib (no requests dependency)"""
        if max_retries is None:
            max_retries = self.config.get("retry_attempts", 3)
        
        url = f"{self.config['server_url']}{endpoint}"
        self.logger.info(f"send_with_retry: Final URL for request: {url}")
        body = json.dumps(data).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['agent_token']}"
        }
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=self.config.get("timeout", 10)) as response:
                    if response.status == 200:
                        return True, json.loads(response.read().decode())
                    else:
                        self.logger.warning(f"Request to {url} failed with status {response.status}: {response.read().decode().strip()}")
            except urllib.error.URLError as e:
                self.logger.error(f"Request error (attempt {attempt + 1}) to {url}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error (attempt {attempt + 1}) to {url}: {e}")
                
            if attempt < max_retries - 1:
                time.sleep(self.config.get("retry_delay", 5))
        
        return False, None
    
    def send_heartbeat(self):
        """Send heartbeat to server"""
        if time.time() - self.last_heartbeat_time < self.config["heartbeat_interval"]:
            return
            
        payload = {
            "server_id": self.server_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "online",
            "agent_version": "1.1.0-light"
        }
        
        self.logger.info(f"Attempting to send heartbeat to endpoint: /agent/heartbeat/")
        success, response = self.send_with_retry("/agent/heartbeat/", payload)
        
        if success:
            self.logger.debug("Heartbeat sent successfully")
            self.last_heartbeat_time = time.time()
        else:
            self.logger.error("Heartbeat failed after retries")
    
    def send_metrics(self, metrics):
        """Send metrics to server"""
        if not metrics:
            return
            
        self.logger.info(f"Attempting to send metrics to endpoint: /agent/metrics/")
        success, response = self.send_with_retry("/agent/metrics/", metrics)
        
        if success:
            self.logger.debug("Metrics sent successfully")
            self.last_metrics_time = time.time()
        else:
            self.logger.error("Metrics send failed after retries")
    
    def metrics_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                metrics = self.get_system_metrics()
                if metrics:
                    self.send_metrics(metrics)
                time.sleep(self.config["metrics_interval"])
            except Exception as e:
                self.logger.error(f"Metrics loop error: {e}")
                time.sleep(5)
    
    def heartbeat_loop(self):
        """Heartbeat loop"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(self.config["heartbeat_interval"])
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start agent"""
        self.logger.info(f"Starting ServerWatch Agent (Light) - Server ID: {self.server_id}")
        self.running = True
        
        # Send initial heartbeat
        self.send_heartbeat()
        
        # Start metrics collection thread
        metrics_thread = threading.Thread(target=self.metrics_loop, daemon=True)
        metrics_thread.start()
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down agent...")
            self.running = False
    
    def stop(self):
        """Stop agent"""
        self.running = False

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="serverwatch-agent")
    parser.add_argument("--config", help="Path to a JSON configuration file")
    parser.add_argument("--url", help="Base URL for the server, e.g. http://<django-host>:8001")
    parser.add_argument("--token", help="Bearer token (Server.agent_token)")
    parser.add_argument("--timeout", type=float, default=5.0)

    parser.add_argument("--cpu", type=float, default=3.0)
    parser.add_argument("--ram", type=float, default=10.0)
    parser.add_argument("--disk-usage", type=float, default=120.0)
    parser.add_argument("--disk-io", type=float, default=3.0)
    parser.add_argument("--load", type=float, default=5.0)
    parser.add_argument("--net", type=float, default=3.0)
    parser.add_argument("--uptime", type=float, default=60.0)

    parser.add_argument("--db", action="store_true", help="Enable DB health monitoring (MySQL/MariaDB)")
    parser.add_argument("--db-interval", type=float, default=5.0)
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-port", type=int, default=3306)
    parser.add_argument("--db-name", default="")
    parser.add_argument("--db-user", default="")
    parser.add_argument("--db-password", default="")

    parser.add_argument("--jitter", type=float, default=0.15, help="Adds +/- jitter to schedule to prevent thundering herd")

    args = parser.parse_args(argv)

    # Load configuration from file
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            agent_logger.error(f"Configuration file not found: {args.config}")
            return 1
        except json.JSONDecodeError:
            agent_logger.error(f"Invalid JSON in configuration file: {args.config}")
            return 1

    # Override config with command-line arguments if provided
    server_url = args.url or config.get("server_url")
    agent_token = args.token or config.get("agent_token")
    
    # Use intervals from config if not provided via command line (assuming args.cpu etc. are always present with default values)
    metrics_interval = config.get("metrics_interval", 30)
    heartbeat_interval = config.get("heartbeat_interval", 60)
    log_level = config.get("log_level", "INFO") # Not directly used here, but good to keep
    monitored_directories = config.get("monitored_directories", []) # Not directly used here, but good to keep
    directory_timeout = config.get("directory_timeout", 30) # Not directly used here, but good to keep

    if not server_url:
        agent_logger.error("Error: Server URL not provided via --url or config file.")
        return 1
    if not agent_token:
        agent_logger.error("Error: Agent token not provided via --token or config file.")
        return 1

    heartbeat_url = f"{server_url.rstrip('/')}/agent/heartbeat/"
    metrics_url = f"{server_url.rstrip('/')}/agent/metrics/"
    
    intervals = Intervals(
        cpu_s=_clamp(float(args.cpu), 2.0, 5.0),
        ram_s=_clamp(float(args.ram), 5.0, 15.0),
        disk_usage_s=_clamp(float(args.disk_usage), 30.0, 300.0),
        disk_io_s=_clamp(float(args.disk_io), 2.0, 5.0),
        load_s=_clamp(float(args.load), 5.0, 5.0),
        net_s=_clamp(float(args.net), 2.0, 5.0),
        uptime_s=max(60.0, float(args.uptime)),
        db_s=max(2.0, float(args.db_interval)),
    )

    jitter = max(0.0, float(args.jitter))

    psutil.cpu_percent(interval=None)

    session = requests.Session()

    due = {
        "cpu": _now(),
        "ram": _now(),
        "disk_usage": _now(),
        "disk_io": _now(),
        "load": _now(),
        "net": _now(),
        "uptime": _now(),
        "db": _now(),
        "heartbeat": _now(),
        "metrics": _now(),
    }

    backoff_s = 1.0

    last_db_counters: dict | None = None
    last_db_ts: float | None = None

    while True:
        t = _now()
        
        def _next(base: float) -> float:
            if jitter <= 0:
                return t + base
            return t + base * (1.0 + random.uniform(-jitter, jitter))

        # Handle Heartbeat
        if t >= due["heartbeat"]:
            heartbeat_payload = {
                "ts": t,
                "server_id": agent.server_id, # Use agent instance's server_id
                "status": "online", # Assuming agent is online if sending heartbeat
                "agent_version": "1.1.0-light"
            }
            try:
                _post(session, heartbeat_url, agent_token, heartbeat_payload, timeout_s=float(args.timeout))
                backoff_s = 1.0
            except Exception as e:
                agent_logger.error(f"Heartbeat error: {e}")
                backoff_s = min(60.0, backoff_s * 2.0)
            due["heartbeat"] = _next(heartbeat_interval)

        # Handle Metrics
        if t >= due["metrics"]:
            metrics_payload: dict = {"ts": t, "agent_token": agent_token, "server_id": agent.server_id} # Also include server_id
            
            # Collect and add metrics to metrics_payload
            if t >= due["cpu"]:
                metrics_payload["cpu"] = _cpu_payload()
                due["cpu"] = _next(intervals.cpu_s)
            else:
                metrics_payload["cpu"] = None # Ensure all fields are present

            if t >= due["ram"]:
                metrics_payload["memory"] = _ram_payload()
                due["ram"] = _next(intervals.ram_s)
            else:
                metrics_payload["memory"] = None

            if t >= due["load"]:
                metrics_payload["load"] = _loadavg()
                due["load"] = _next(intervals.load_s)
            else:
                metrics_payload["load"] = None

            if t >= due["uptime"]:
                metrics_payload["system"] = _uptime_payload() # Renamed to system for consistency
                due["uptime"] = _next(intervals.uptime_s)
            else:
                metrics_payload["system"] = None

            if t >= due["disk_io"]:
                metrics_payload["disk_io"] = _disk_io()
                due["disk_io"] = _next(intervals.disk_io_s)
            else:
                metrics_payload["disk_io"] = None

            if t >= due["net"]:
                metrics_payload["network"] = _net_io()
                due["net"] = _next(intervals.net_s)
            else:
                metrics_payload["network"] = None

            if t >= due["disk_usage"]:
                metrics_payload["disk"] = _disk_usage_samples()[0] if _disk_usage_samples() else {} # Assuming first disk for simplicity
                due["disk_usage"] = _next(intervals.disk_usage_s)
            else:
                metrics_payload["disk"] = None
            
            # DB metrics (if enabled)
            if args.db and t >= due["db"]:
                if args.db_name and args.db_user and args.db_password:
                    try:
                        db_payload, last_db_counters, last_db_ts = _mysql_metrics(
                            host=str(args.db_host),
                            port=int(args.db_port),
                            db_name=str(args.db_name),
                            user=str(args.db_user),
                            password=str(args.db_password),
                            timeout_s=float(args.timeout),
                            last_counters=last_db_counters,
                            last_ts=last_db_ts,
                        )
                        metrics_payload["db"] = db_payload
                    except Exception as e:
                        agent_logger.error(f"db: {e}")
                else:
                    port_ok, port_ms = _tcp_check(str(args.db_host), int(args.db_port), timeout_s=float(args.timeout))
                    metrics_payload["db"] = {
                        "engine": "mysql",
                        "process_up": _mysql_process_up(),
                        "port_ok": port_ok,
                        "port_ms": port_ms,
                        "connect_ok": None,
                    }
                due["db"] = _next(intervals.db_s)
            else:
                metrics_payload["db"] = None

            try:
                _post(session, metrics_url, agent_token, metrics_payload, timeout_s=float(args.timeout))
                backoff_s = 1.0
            except Exception as e:
                agent_logger.error(f"Metrics error: {e}")
                backoff_s = min(60.0, backoff_s * 2.0)
            due["metrics"] = _next(metrics_interval) # Update metrics due time after attempting to send

        next_deadline = min(due.values())
        sleep_until = min(next_deadline, _now() + backoff_s)
        _sleep_until(sleep_until)


if __name__ == "__main__":
    agent = ServerAgent(config_file=os.path.expanduser("~/.config/serverwatch-agent/config.json"))
    agent.start()