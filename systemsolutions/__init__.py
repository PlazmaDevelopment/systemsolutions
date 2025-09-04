"""
SystemSolutions - A comprehensive system interaction and automation library.

This module provides a unified interface for system operations including process management,
file system operations, window management, network utilities, and system monitoring.
"""

# Core modules
from .system import SystemInfo, SystemMonitor
from .process import ProcessManager, Process
from .filesystem import FileSystem
from .window import WindowManager
from .network import NetworkManager
from .automation import Automation
from .utils import logger, ErrorHandler

# Version
__version__ = '0.1.0'

# Initialize default instances
system_info = SystemInfo()
process_manager = ProcessManager()
file_system = FileSystem()
window_manager = WindowManager()
network_manager = NetworkManager()
automation = Automation()

# Clean up
__all__ = [
    # Core classes
    'SystemInfo', 'SystemMonitor',
    'ProcessManager', 'Process',
    'FileSystem',
    'WindowManager',
    'NetworkManager',
    'Automation',
    'ErrorHandler',
    
    # Instances
    'system_info',
    'process_manager',
    'file_system',
    'window_manager',
    'network_manager',
    'automation',
    'logger'
]
