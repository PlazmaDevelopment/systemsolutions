"""
System information and monitoring utilities.
"""

import os
import sys
import platform
import psutil
import socket
import uuid
import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from .utils import ErrorHandler, logger

class SystemInfo:
    """Provides comprehensive system information."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    @property
    def platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version(),
        }
    
    @property
    def cpu_info(self) -> Dict[str, Union[str, int, float]]:
        """Get CPU information."""
        try:
            return {
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(),
                'max_frequency': psutil.cpu_freq().max if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else None,
                'min_frequency': psutil.cpu_freq().min if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else None,
                'current_frequency': psutil.cpu_freq().current if hasattr(psutil, 'cpu_freq') and psutil.cpu_freq() else None,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_stats': dict(psutil.cpu_stats()._asdict()) if hasattr(psutil, 'cpu_stats') else {},
                'cpu_times': dict(psutil.cpu_times()._asdict()) if hasattr(psutil, 'cpu_times') else {},
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting CPU info: {e}")
            return {}
    
    @property
    def memory_info(self) -> Dict[str, Union[int, float]]:
        """Get memory information."""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            return {
                'total_ram': virtual_mem.total,
                'available_ram': virtual_mem.available,
                'used_ram': virtual_mem.used,
                'ram_percent': virtual_mem.percent,
                'total_swap': swap_mem.total,
                'used_swap': swap_mem.used,
                'free_swap': swap_mem.free,
                'swap_percent': swap_mem.percent,
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting memory info: {e}")
            return {}
    
    @property
    def disk_info(self) -> List[Dict[str, Union[str, int, float]]]:
        """Get disk/partition information."""
        try:
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'opts': partition.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                    })
                except Exception as e:
                    self.error_handler.log_error(f"Error getting disk info for {partition.mountpoint}: {e}")
            return disks
        except Exception as e:
            self.error_handler.log_error(f"Error getting disk info: {e}")
            return []
    
    @property
    def network_info(self) -> Dict[str, Union[str, List[Dict]]]:
        """Get network information."""
        try:
            net_io = psutil.net_io_counters()
            net_addrs = psutil.net_if_addrs()
            
            interfaces = []
            for interface, addrs in net_addrs.items():
                interface_info = {'interface': interface, 'addresses': []}
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask if hasattr(addr, 'netmask') else None,
                        'broadcast': addr.broadcast if hasattr(addr, 'broadcast') else None,
                    })
                interfaces.append(interface_info)
            
            return {
                'hostname': socket.gethostname(),
                'fqdn': socket.getfqdn(),
                'ip_address': socket.gethostbyname(socket.gethostname()),
                'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                      for elements in range(5, -1, -1)]),
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'interfaces': interfaces,
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting network info: {e}")
            return {}
    
    @property
    def boot_time(self) -> str:
        """Get system boot time."""
        try:
            return datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.error_handler.log_error(f"Error getting boot time: {e}")
            return ""
    
    def get_all_info(self) -> Dict:
        """Get all system information in a single dictionary."""
        return {
            'platform': self.platform_info,
            'cpu': self.cpu_info,
            'memory': self.memory_info,
            'disks': self.disk_info,
            'network': self.network_info,
            'boot_time': self.boot_time,
            'timestamp': datetime.datetime.now().isoformat(),
        }


class SystemMonitor:
    """Monitors system resources and performance."""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.error_handler = ErrorHandler()
        self._stop_event = False
    
    def monitor_cpu(self, duration: int = 10, callback=None) -> List[Dict]:
        """Monitor CPU usage over time."""
        import time
        
        results = []
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration and not self._stop_event:
                cpu_percent = psutil.cpu_percent(interval=self.interval, percpu=True)
                timestamp = datetime.datetime.now().isoformat()
                
                result = {
                    'timestamp': timestamp,
                    'cpu_percent': cpu_percent,
                    'avg_cpu': sum(cpu_percent) / len(cpu_percent)
                }
                
                results.append(result)
                if callback:
                    callback(result)
                
                if self._stop_event:
                    break
                    
        except Exception as e:
            self.error_handler.log_error(f"Error monitoring CPU: {e}")
        
        return results
    
    def monitor_memory(self, duration: int = 10, callback=None) -> List[Dict]:
        """Monitor memory usage over time."""
        import time
        
        results = []
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < duration and not self._stop_event:
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                timestamp = datetime.datetime.now().isoformat()
                
                result = {
                    'timestamp': timestamp,
                    'ram': {
                        'total': mem.total,
                        'available': mem.available,
                        'used': mem.used,
                        'percent': mem.percent
                    },
                    'swap': {
                        'total': swap.total,
                        'used': swap.used,
                        'free': swap.free,
                        'percent': swap.percent
                    }
                }
                
                results.append(result)
                if callback:
                    callback(result)
                
                time.sleep(self.interval)
                if self._stop_event:
                    break
                    
        except Exception as e:
            self.error_handler.log_error(f"Error monitoring memory: {e}")
        
        return results
    
    def stop_monitoring(self):
        """Stop any active monitoring."""
        self._stop_event = True
    
    def get_processes(self, attrs: list = None) -> List[Dict]:
        """Get information about running processes."""
        try:
            processes = []
            default_attrs = ['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent']
            attrs = attrs or default_attrs
            
            for proc in psutil.process_iter(attrs=attrs):
                try:
                    process_info = proc.info
                    process_info['memory_info'] = proc.memory_info()._asdict() if hasattr(proc, 'memory_info') else {}
                    processes.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return processes
        except Exception as e:
            self.error_handler.log_error(f"Error getting process list: {e}")
            return []
