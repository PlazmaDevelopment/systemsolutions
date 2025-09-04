"""
Process management and monitoring utilities.
"""

import os
import psutil
import signal
import subprocess
import time
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, asdict
from .utils import ErrorHandler, logger

@dataclass
class ProcessInfo:
    """Process information container."""
    pid: int
    name: str
    status: str
    username: str
    create_time: float
    cpu_percent: float
    memory_percent: float
    memory_info: Dict[str, int]
    cmdline: List[str]
    exe: str
    cwd: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def terminate(self, timeout: int = 5) -> bool:
        """Terminate the process."""
        try:
            proc = psutil.Process(self.pid)
            proc.terminate()
            
            # Wait for process to terminate
            try:
                proc.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                # Force kill if process doesn't terminate
                proc.kill()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error terminating process {self.pid}: {e}")
            return False


class Process:
    """Wrapper for process operations."""
    
    def __init__(self, pid: Optional[int] = None, process: Optional[psutil.Process] = None):
        """Initialize with either a PID or a psutil.Process object."""
        self.error_handler = ErrorHandler()
        
        if process is not None:
            self._process = process
        elif pid is not None:
            try:
                self._process = psutil.Process(pid)
            except psutil.NoSuchProcess as e:
                self.error_handler.log_error(f"Process {pid} not found: {e}")
                raise
        else:
            self._process = psutil.Process()  # Current process
    
    @property
    def info(self) -> ProcessInfo:
        """Get process information."""
        try:
            with self._process.oneshot():
                return ProcessInfo(
                    pid=self._process.pid,
                    name=self._process.name(),
                    status=self._process.status(),
                    username=self._process.username(),
                    create_time=self._process.create_time(),
                    cpu_percent=self._process.cpu_percent(interval=0.1),
                    memory_percent=self._process.memory_percent(),
                    memory_info=self._process.memory_info()._asdict(),
                    cmdline=self._process.cmdline(),
                    exe=self._process.exe(),
                    cwd=self._process.cwd() if hasattr(self._process, 'cwd') else None,
                    environment=dict(self._process.environ()) if hasattr(self._process, 'environ') else None
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error getting process info: {e}")
            raise
    
    def get_children(self, recursive: bool = False) -> List['Process']:
        """Get child processes."""
        try:
            children = self._process.children(recursive=recursive)
            return [Process(process=child) for child in children]
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error getting child processes: {e}")
            return []
    
    def get_parent(self) -> Optional['Process']:
        """Get parent process."""
        try:
            parent = self._process.parent()
            return Process(process=parent) if parent else None
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error getting parent process: {e}")
            return None
    
    def get_connections(self) -> List[Dict]:
        """Get network connections used by the process."""
        try:
            return [conn._asdict() for conn in self._process.connections()]
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error getting process connections: {e}")
            return []
    
    def get_open_files(self) -> List[str]:
        """Get files opened by the process."""
        try:
            return [f.path for f in self._process.open_files()]
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error getting open files: {e}")
            return []
    
    def send_signal(self, sig: int) -> bool:
        """Send a signal to the process."""
        try:
            self._process.send_signal(sig)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error sending signal {sig} to process: {e}")
            return False
    
    def suspend(self) -> bool:
        """Suspend process execution."""
        try:
            self._process.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error suspending process: {e}")
            return False
    
    def resume(self) -> bool:
        """Resume process execution."""
        try:
            self._process.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error resuming process: {e}")
            return False
    
    def terminate(self, timeout: int = 5) -> bool:
        """Terminate the process gracefully."""
        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
                return True
            except psutil.TimeoutExpired:
                self.kill()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error terminating process: {e}")
            return False
    
    def kill(self) -> bool:
        """Kill the process immediately."""
        try:
            self._process.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.error_handler.log_error(f"Error killing process: {e}")
            return False


class ProcessManager:
    """Manager for system processes."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    def list_processes(self, attrs: Optional[List[str]] = None) -> List[ProcessInfo]:
        """List all running processes."""
        processes = []
        default_attrs = ['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent']
        attrs = attrs or default_attrs
        
        for proc in psutil.process_iter(attrs=attrs):
            try:
                process_info = proc.info
                process_info['memory_info'] = proc.memory_info()._asdict() if hasattr(proc, 'memory_info') else {}
                processes.append(ProcessInfo(**process_info))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.error_handler.log_error(f"Error getting process info: {e}")
                continue
        
        return processes
    
    def find_processes(self, name: Optional[str] = None, cmdline: Optional[str] = None) -> List[Process]:
        """Find processes by name or command line."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name and name.lower() in proc.info['name'].lower():
                    processes.append(Process(process=proc))
                elif cmdline and any(cmdline in ' '.join(cmd) for cmd in proc.info['cmdline'] if cmd):
                    processes.append(Process(process=proc))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def get_process(self, pid: int) -> Optional[Process]:
        """Get process by PID."""
        try:
            return Process(pid=pid)
        except psutil.NoSuchProcess:
            return None
    
    def run_command(self, command: Union[str, List[str]], 
                   cwd: Optional[str] = None,
                   env: Optional[Dict[str, str]] = None,
                   shell: bool = False,
                   capture_output: bool = True,
                   timeout: Optional[float] = None) -> subprocess.CompletedProcess:
        """Run a shell command and return the result."""
        try:
            if isinstance(command, str) and not shell:
                command = command.split()
            
            return subprocess.run(
                command,
                cwd=cwd,
                env=env,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False
            )
        except Exception as e:
            self.error_handler.log_error(f"Error running command {command}: {e}")
            raise
    
    def create_process(self, command: Union[str, List[str]], 
                      cwd: Optional[str] = None,
                      env: Optional[Dict[str, str]] = None,
                      shell: bool = False) -> subprocess.Popen:
        """Create a new process and return the Popen object."""
        try:
            if isinstance(command, str) and not shell:
                command = command.split()
            
            return subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                shell=shell,
                text=True,
                start_new_session=True
            )
        except Exception as e:
            self.error_handler.log_error(f"Error creating process: {e}")
            raise
    
    def terminate_all(self, name: str, signal: int = signal.SIGTERM) -> int:
        """Terminate all processes with the given name."""
        count = 0
        for proc in self.find_processes(name=name):
            try:
                proc.send_signal(signal)
                count += 1
            except Exception as e:
                self.error_handler.log_error(f"Error terminating process {proc.info.pid}: {e}")
        return count
