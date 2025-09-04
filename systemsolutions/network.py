"""
Network utilities and operations.
"""

import socket
import subprocess
import ipaddress
import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from datetime import datetime
from .utils import ErrorHandler, logger

@dataclass
class NetworkInterface:
    """Network interface information."""
    name: str
    is_up: bool
    mtu: int
    mac_address: str
    ipv4_addresses: List[str]
    ipv6_addresses: List[str]
    netmask: str
    broadcast: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'is_up': self.is_up,
            'mtu': self.mtu,
            'mac_address': self.mac_address,
            'ipv4_addresses': self.ipv4_addresses,
            'ipv6_addresses': self.ipv6_addresses,
            'netmask': self.netmask,
            'broadcast': self.broadcast
        }

@dataclass
class NetworkConnection:
    """Network connection information."""
    fd: int
    family: int
    type: int
    local_addr: Tuple[str, int]
    remote_addr: Optional[Tuple[str, int]]
    status: str
    pid: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'fd': self.fd,
            'family': self.family,
            'type': self.type,
            'local_addr': self.local_addr,
            'remote_addr': self.remote_addr,
            'status': self.status,
            'pid': self.pid
        }

class NetworkManager:
    """Manages network operations and information."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    # ========== Network Information ==========
    
    def get_hostname(self) -> str:
        """Get the hostname of the system."""
        try:
            return socket.gethostname()
        except Exception as e:
            self.error_handler.log_error(f"Error getting hostname: {e}")
            return ""
    
    def get_fqdn(self) -> str:
        """Get the fully qualified domain name."""
        try:
            return socket.getfqdn()
        except Exception as e:
            self.error_handler.log_error(f"Error getting FQDN: {e}")
            return ""
    
    def get_ip_address(self, hostname: str = None) -> str:
        """Get the IP address for a hostname (default: localhost)."""
        try:
            hostname = hostname or socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception as e:
            self.error_handler.log_error(f"Error getting IP address for {hostname}: {e}")
            return ""
    
    def get_mac_address(self, interface: str = None) -> str:
        """Get the MAC address of a network interface."""
        try:
            if hasattr(socket, 'AF_LINK'):
                # macOS/Linux
                import fcntl
                import struct
                
                if not interface:
                    # Get default interface
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.connect(("8.8.8.8", 80))
                        interface = s.getsockname()[0]
                
                with open(f"/sys/class/net/{interface}/address") as f:
                    return f.read().strip()
            else:
                # Windows
                import ctypes
                import ctypes.wintypes
                
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                info = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM)
                ip = info[0][4][0]
                
                # Use the Windows API to get the MAC address
                class MIB_IPNETROW(ctypes.Structure):
                    _fields_ = [
                        ("dwIndex", ctypes.wintypes.DWORD),
                        ("dwPhysAddrLen", ctypes.wintypes.DWORD),
                        ("bPhysAddr", ctypes.c_ubyte * 8),
                        ("dwAddr", ctypes.wintypes.DWORD),
                        ("dwType", ctypes.wintypes.DWORD)
                    ]
                
                GetIpNetTable = ctypes.windll.iphlpapi.GetIpNetTable
                GetIpNetTable.argtypes = [ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong), bool]
                GetIpNetTable.restype = ctypes.c_uint
                
                GetAdaptersInfo = ctypes.windll.iphlpapi.GetAdaptersInfo
                GetAdaptersInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
                GetAdaptersInfo.restype = ctypes.c_uint
                
                # First call to get the buffer size
                buf_len = ctypes.c_ulong(0)
                GetAdaptersInfo(None, ctypes.byref(buf_len))
                
                # Allocate the buffer
                buf = ctypes.create_string_buffer(buf_len.value)
                
                # Second call to get the actual data
                if GetAdaptersInfo(ctypes.byref(buf), ctypes.byref(buf_len)) != 0:
                    raise OSError("Failed to get adapter info")
                
                # Parse the result
                class IP_ADAPTER_INFO(ctypes.Structure):
                    pass
                
                IP_ADAPTER_INFO._fields_ = [
                    ("next", ctypes.POINTER(IP_ADAPTER_INFO)),
                    ("ComboIndex", ctypes.c_ulong),
                    ("AdapterName", ctypes.c_char * 260),
                    ("Description", ctypes.c_char * 132),
                    ("AddressLength", ctypes.c_uint),
                    ("Address", ctypes.c_ubyte * 8),
                    ("Index", ctypes.c_ulong),
                    ("Type", ctypes.c_uint),
                    ("DhcpEnabled", ctypes.c_uint),
                    ("CurrentIpAddress", ctypes.c_void_p),
                    ("IpAddressList", ctypes.c_ulong * 4),  # Simplified
                    ("GatewayList", ctypes.c_ulong * 4),    # Simplified
                    ("DhcpServer", ctypes.c_ulong * 4),     # Simplified
                    ("HaveWins", ctypes.c_uint),
                    ("PrimaryWinsServer", ctypes.c_ulong * 4),  # Simplified
                    ("SecondaryWinsServer", ctypes.c_ulong * 4),  # Simplified
                    ("LeaseObtained", ctypes.c_ulong),
                    ("LeaseExpires", ctypes.c_ulong)
                ]
                
                adapter = ctypes.cast(ctypes.byref(buf), ctypes.POINTER(IP_ADAPTER_INFO)).contents
                
                while True:
                    # Check if this is the adapter we're looking for
                    if socket.inet_ntoa(adapter.IpAddressList[0].to_bytes(4, 'little')) == ip:
                        return ":".join(f"{b:02x}" for b in adapter.Address[:adapter.AddressLength])
                    
                    if not adapter.next:
                        break
                    adapter = adapter.next.contents
                
                return ""
                
        except Exception as e:
            self.error_handler.log_error(f"Error getting MAC address: {e}")
            return ""
    
    def get_network_interfaces(self) -> Dict[str, NetworkInterface]:
        """Get information about all network interfaces."""
        try:
            import psutil
            
            interfaces = {}
            
            # Get network interface information
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for name, addrs_list in addrs.items():
                is_up = name in stats and stats[name].isup
                mtu = stats[name].mtu if name in stats else 1500
                
                ipv4_addrs = []
                ipv6_addrs = []
                mac_address = ""
                netmask = ""
                broadcast = ""
                
                for addr in addrs_list:
                    if addr.family == socket.AF_INET:
                        ipv4_addrs.append(addr.address)
                        netmask = addr.netmask or ""
                        broadcast = addr.broadcast or ""
                    elif addr.family == socket.AF_INET6:
                        ipv6_addrs.append(addr.address)
                    elif addr.family == psutil.AF_LINK:
                        mac_address = addr.address
                
                interfaces[name] = NetworkInterface(
                    name=name,
                    is_up=is_up,
                    mtu=mtu,
                    mac_address=mac_address,
                    ipv4_addresses=ipv4_addrs,
                    ipv6_addresses=ipv6_addrs,
                    netmask=netmask,
                    broadcast=broadcast
                )
            
            return interfaces
        except Exception as e:
            self.error_handler.log_error(f"Error getting network interfaces: {e}")
            return {}
    
    def get_network_connections(self, kind: str = 'inet') -> List[NetworkConnection]:
        """Get network connections."""
        try:
            import psutil
            
            connections = []
            
            # Map kind to psutil connection kind
            kind_map = {
                'inet': 'inet',
                'inet4': 'inet4',
                'inet6': 'inet6',
                'tcp': 'tcp',
                'tcp4': 'tcp4',
                'tcp6': 'tcp6',
                'udp': 'udp',
                'udp4': 'udp4',
                'udp6': 'udp6',
                'unix': 'unix',
                'all': 'all'
            }
            
            kind = kind_map.get(kind.lower(), 'inet')
            
            for conn in psutil.net_connections(kind=kind):
                connections.append(NetworkConnection(
                    fd=conn.fd,
                    family=conn.family,
                    type=conn.type,
                    local_addr=conn.laddr,
                    remote_addr=conn.raddr if conn.raddr else None,
                    status=conn.status,
                    pid=conn.pid
                ))
            
            return connections
        except Exception as e:
            self.error_handler.log_error(f"Error getting network connections: {e}")
            return []
    
    # ========== Network Testing ==========
    
    def ping(self, host: str, count: int = 4, timeout: int = 2) -> Dict[str, Any]:
        """Ping a host and return the results."""
        try:
            # Prepare the command based on the platform
            if os.name == 'nt':
                # Windows
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
            else:
                # Unix/Linux/Mac
                cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
            
            # Run the ping command
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Parse the output
            sent = 0
            received = 0
            times = []
            
            if os.name == 'nt':
                # Windows output parsing
                for line in output.split('\n'):
                    if 'bytes=' in line and 'time=' in line:
                        sent += 1
                        if 'time=' in line and 'timeout' not in line:
                            received += 1
                            time_ms = int(line.split('time=')[1].split('ms')[0].strip())
                            times.append(time_ms)
            else:
                # Unix/Linux/Mac output parsing
                for line in output.split('\n'):
                    if 'bytes from' in line:
                        sent += 1
                        if 'time=' in line:
                            received += 1
                            time_ms = float(line.split('time=')[1].split(' ')[0])
                            times.append(time_ms)
            
            # Calculate statistics
            lost = sent - received
            loss_percent = (lost / sent * 100) if sent > 0 else 0
            
            if times:
                min_time = min(times)
                max_time = max(times)
                avg_time = sum(times) / len(times)
            else:
                min_time = max_time = avg_time = 0
            
            return {
                'host': host,
                'sent': sent,
                'received': received,
                'lost': lost,
                'loss_percent': loss_percent,
                'min_time': min_time,
                'max_time': max_time,
                'avg_time': avg_time,
                'times': times,
                'success': received > 0
            }
        except subprocess.CalledProcessError as e:
            self.error_handler.log_error(f"Ping failed: {e}")
            return {
                'host': host,
                'sent': 0,
                'received': 0,
                'lost': 0,
                'loss_percent': 100,
                'min_time': 0,
                'max_time': 0,
                'avg_time': 0,
                'times': [],
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.error_handler.log_error(f"Error pinging {host}: {e}")
            return {
                'host': host,
                'error': str(e),
                'success': False
            }
    
    def traceroute(self, host: str, max_hops: int = 30, timeout: int = 1) -> List[Dict[str, Any]]:
        """Perform a traceroute to a host."""
        try:
            import subprocess
            import re
            
            # Prepare the command based on the platform
            if os.name == 'nt':
                # Windows
                cmd = ['tracert', '-h', str(max_hops), '-w', str(timeout * 1000), host]
            else:
                # Unix/Linux/Mac
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), host]
            
            # Run the traceroute command
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Parse the output
            hops = []
            
            if os.name == 'nt':
                # Windows output parsing
                for line in output.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Match lines like: 1     1 ms    <1 ms    <1 ms  192.168.1.1
                    match = re.match(r'^\s*(\d+)\s+([\d\*]+)\s*ms\s+([\d\*]+)\s*ms\s+([\d\*]+)\s*ms\s+(.+)$', line)
                    if match:
                        hop_num = int(match.group(1))
                        times = []
                        for t in match.groups()[1:4]:
                            if t == '*':
                                times.append(None)
                            else:
                                times.append(float(t))
                        
                        host = match.group(5).strip()
                        if host.startswith('Request timed out.'):
                            host = '* * *'
                        
                        hops.append({
                            'hop': hop_num,
                            'host': host,
                            'times': times,
                            'avg_time': sum(t for t in times if t is not None) / len([t for t in times if t is not None]) if any(t is not None for t in times) else None
                        })
            else:
                # Unix/Linux/Mac output parsing
                for line in output.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('traceroute'):
                        continue
                    
                    # Match lines like: 1  192.168.1.1 (192.168.1.1)  1.234 ms  1.123 ms  1.456 ms
                    match = re.match(r'^\s*(\d+)\s+([^\s]+)\s+\(([^)]+)\)\s+([\d.]+)\s*ms(?:\s+([\d.]+)\s*ms)?(?:\s+([\d.]+)\s*ms)?', line)
                    if not match:
                        # Try matching lines without hostname: 1  * * *
                        match = re.match(r'^\s*(\d+)\s+\*\s*\*\s*\*', line)
                        if match:
                            hop_num = int(match.group(1))
                            hops.append({
                                'hop': hop_num,
                                'host': '* * *',
                                'times': [None, None, None],
                                'avg_time': None
                            })
                        continue
                    
                    hop_num = int(match.group(1))
                    hostname = match.group(2)
                    ip = match.group(3)
                    times = []
                    
                    for t in match.groups()[3:]:
                        if t is not None and t.replace('.', '').isdigit():
                            times.append(float(t))
                    
                    host = f"{hostname} ({ip})" if hostname != ip else ip
                    
                    hops.append({
                        'hop': hop_num,
                        'host': host,
                        'times': times + [None] * (3 - len(times)),
                        'avg_time': sum(times) / len(times) if times else None
                    })
            
            return hops
        except subprocess.CalledProcessError as e:
            self.error_handler.log_error(f"Traceroute failed: {e}")
            return [{'error': str(e), 'success': False}]
        except Exception as e:
            self.error_handler.log_error(f"Error performing traceroute to {host}: {e}")
            return [{'error': str(e), 'success': False}]
    
    # ========== Network Requests ==========
    
    def http_request(self, url: str, method: str = 'GET', 
                    headers: Dict[str, str] = None, 
                    data: Any = None, 
                    json_data: Any = None, 
                    timeout: int = 10) -> Dict[str, Any]:
        """Perform an HTTP request."""
        try:
            import urllib.request
            import urllib.parse
            import json
            
            # Prepare the request
            if headers is None:
                headers = {}
            
            # Add default headers if not provided
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'SystemSolutions/1.0'
            
            # Prepare the request data
            body = None
            if data is not None:
                if isinstance(data, dict):
                    data = urllib.parse.urlencode(data).encode('utf-8')
                elif isinstance(data, str):
                    data = data.encode('utf-8')
                
                body = data
                if 'Content-Type' not in headers:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            # Handle JSON data
            if json_data is not None:
                body = json.dumps(json_data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            
            # Create the request
            req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
            
            # Send the request and get the response
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                
                # Try to parse as JSON if the content type is JSON
                content_type = response.getheader('Content-Type', '')
                json_response = None
                if 'application/json' in content_type:
                    try:
                        json_response = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                
                return {
                    'status_code': response.status,
                    'headers': dict(response.getheaders()),
                    'content': content,
                    'json': json_response,
                    'url': response.geturl(),
                    'success': 200 <= response.status < 400
                }
        except urllib.error.HTTPError as e:
            return {
                'status_code': e.code,
                'headers': dict(e.headers) if hasattr(e, 'headers') else {},
                'content': e.read().decode('utf-8') if hasattr(e, 'read') else str(e),
                'url': url,
                'success': False,
                'error': str(e)
            }
        except urllib.error.URLError as e:
            return {
                'status_code': None,
                'headers': {},
                'content': str(e),
                'url': url,
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.error_handler.log_error(f"Error making HTTP request to {url}: {e}")
            return {
                'status_code': None,
                'headers': {},
                'content': str(e),
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, url: str, destination: str, chunk_size: int = 8192) -> Dict[str, Any]:
        """Download a file from a URL."""
        try:
            import urllib.request
            import shutil
            
            # Create the destination directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(destination)), exist_ok=True)
            
            # Download the file
            with urllib.request.urlopen(url) as response, open(destination, 'wb') as out_file:
                shutil.copyfileobj(response, out_file, chunk_size)
            
            return {
                'success': True,
                'destination': destination,
                'size': os.path.getsize(destination)
            }
        except Exception as e:
            self.error_handler.log_error(f"Error downloading file from {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'destination': destination
            }
