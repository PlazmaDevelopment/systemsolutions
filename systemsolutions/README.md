# SystemSolutions

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive Python library for system interaction and automation, providing easy-to-use interfaces for system information, process management, file system operations, window management, and network utilities.

## Features

- **System Information**: Get detailed system and hardware information
- **Process Management**: Manage and monitor system processes
- **File System**: Comprehensive file and directory operations
- **Window Management**: Control GUI windows and automate interactions
- **Network Utilities**: Network information, testing, and HTTP requests
- **Automation**: Tools for automating system tasks
- **Error Handling**: Robust error handling and logging

## Installation

```bash
pip install systemsolutions
```

## Quick Start

```python
from systemsolutions import SystemInfo, ProcessManager, FileSystem, WindowManager, NetworkManager

# Get system information
system_info = SystemInfo()
print(f"OS: {system_info.os_name} {system_info.os_version}")
print(f"CPU: {system_info.cpu_info['brand_raw']} ({system_info.cpu_cores} cores)")
print(f"Memory: {system_info.memory_info['total'] / (1024**3):.2f} GB")

# Manage processes
pm = ProcessManager()
chrome_processes = pm.find_processes(name='chrome.exe')
for proc in chrome_processes:
    print(f"Process: {proc['name']} (PID: {proc['pid']})")

# File system operations
fs = FileSystem()
files = fs.list_dir('C:\\Users\\User\\Documents')
print(f"Files in Documents: {files}")

# Window management
wm = WindowManager()
active_window = wm.get_active_window()
print(f"Active window: {active_window.title}" if active_window else "No active window")

# Network operations
nm = NetworkManager()
ping_result = nm.ping('google.com')
print(f"Ping to Google: {ping_result['avg_time']}ms")
```

## Documentation

### System Module

#### SystemInfo

```python
from systemsolutions.system import SystemInfo

# Get system information
sys_info = SystemInfo()

# System information
print(sys_info.os_name)           # e.g., 'Windows 10'
print(sys_info.os_version)        # e.g., '10.0.19043'
print(sys_info.hostname)          # Computer name
print(sys_info.architecture)      # e.g., '64bit'
print(sys_info.boot_time)         # System boot time (datetime)

# CPU information
print(sys_info.cpu_cores)         # Number of CPU cores
print(sys_info.cpu_info)          # Detailed CPU information
print(sys_info.cpu_usage())       # Current CPU usage percentage

# Memory information
print(sys_info.memory_info)       # Total, available, used memory
print(sys_info.memory_usage())    # Memory usage percentage

# Disk information
print(sys_info.disk_info)         # Disk partitions and usage
print(sys_info.disk_usage('C:'))  # Usage for specific partition

# Network information
print(sys_info.network_info)      # Network interfaces and addresses
print(sys_info.network_io())      # Network I/O statistics
```

### Process Module

#### ProcessManager

```python
from systemsolutions.process import ProcessManager

pm = ProcessManager()

# List all processes
all_processes = pm.get_processes()
for proc in all_processes:
    print(f"{proc['pid']}: {proc['name']} ({proc['status']})")

# Find processes by name
chrome_processes = pm.find_processes(name='chrome.exe')

# Get process details
if chrome_processes:
    proc_info = pm.get_process_info(chrome_processes[0]['pid'])
    print(f"CPU: {proc_info['cpu_percent']}%")
    print(f"Memory: {proc_info['memory_info']['rss'] / (1024*1024):.2f} MB")

# Start a new process
pid = pm.start_process('notepad.exe')

# Terminate a process
pm.terminate_process(pid)
```

### File System Module

#### FileSystem

```python
from systemsolutions.filesystem import FileSystem

fs = FileSystem()

# File operations
content = fs.read_file('example.txt')
fs.write_file('example_copy.txt', content)
fs.copy_file('example.txt', 'backup/example.txt')
fs.move_file('example.txt', 'documents/example.txt')
fs.delete_file('example.txt')

# Directory operations
fs.create_dir('new_directory')
files = fs.list_dir('documents')
fs.copy_dir('documents', 'backup/documents')
fs.delete_dir('backup', recursive=True)

# File search
py_files = fs.find_files('/path/to/search', '*.py', recursive=True)

# File hashing
file_hash = fs.get_file_hash('large_file.iso', 'sha256')
```

### Window Management Module

#### WindowManager

```python
from systemsolutions.window import WindowManager

wm = WindowManager()

# Get window information
active_window = wm.get_active_window()
all_windows = wm.get_windows()
chrome_windows = wm.get_windows(title='Chrome')

# Control windows
if chrome_windows:
    wm.activate_window(chrome_windows[0])
    wm.maximize_window(chrome_windows[0])
    wm.move_window(chrome_windows[0], x=0, y=0, width=800, height=600)
    wm.set_window_always_on_top(chrome_windows[0], True)

# Mouse and keyboard
wm.click(100, 200)  # Click at coordinates (100, 200)
wm.type_text('Hello, World!')
wm.press_key('enter')
wm.hotkey('ctrl', 'c')  # Press Ctrl+C
```

### Network Module

#### NetworkManager

```python
from systemsolutions.network import NetworkManager

nm = NetworkManager()

# Network information
print(nm.get_hostname())
print(nm.get_ip_address())
print(nm.get_mac_address())

# Network testing
ping_result = nm.ping('google.com')
trace_result = nm.traceroute('example.com')

# HTTP requests
response = nm.http_request('https://api.github.com')
print(response['status_code'])
print(response['json'])

# File download
result = nm.download_file('https://example.com/file.zip', 'downloads/file.zip')
if result['success']:
    print(f"Downloaded {result['size']} bytes to {result['destination']}")
```

## Error Handling

All modules use a common error handling system. You can access error logs and handle exceptions consistently:

```python
try:
    # Some operation that might fail
    fs.delete_file('important_file.txt')
except Exception as e:
    error_handler = ErrorHandler()
    error_handler.log_error(f"Failed to delete file: {e}")
    
    # Get all logged errors
    for error in error_handler.get_errors():
        print(f"[{error['timestamp']}] {error['message']}")
```

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/PlazmaDevelopment/systemsolutions.git
   cd systemsolutions
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

### Running Tests

```bash
pytest tests/
```

### Building Documentation

```bash
cd docs
make html
```

### Building the Package

```bash
python -m build
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on the [GitHub repository](https://github.com/PlazmaDevelopment/systemsolutions/issues).

## Authors

- **PlazmaDevelopment** - [plazmadevacc@gmail.com](mailto:plazmadevacc@gmail.com)

## Acknowledgments

- Thanks to all contributors who have helped improve this project.
- Built with ❤️ using Python.
