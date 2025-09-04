"""
Window management and GUI automation utilities.
"""

import ctypes
import time
import re
import pygetwindow as gw
import pyautogui
import keyboard
import pywinauto
from typing import List, Dict, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass
from .utils import ErrorHandler, logger

# Windows API constants
HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
MONITOR_OFF = 2
MONITOR_ON = -1

@dataclass
class WindowInfo:
    """Window information container."""
    handle: int
    title: str
    class_name: str
    is_active: bool
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    x: int
    y: int
    width: int
    height: int
    process_id: int
    process_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'handle': self.handle,
            'title': self.title,
            'class_name': self.class_name,
            'is_active': self.is_active,
            'is_visible': self.is_visible,
            'is_minimized': self.is_minimized,
            'is_maximized': self.is_maximized,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'process_id': self.process_id,
            'process_name': self.process_name
        }

class WindowManager:
    """Manages windows and GUI automation."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.user32 = ctypes.windll.user32
        self._setup_pyautogui()
    
    def _setup_pyautogui(self):
        """Configure PyAutoGUI settings."""
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    # ========== Window Information ==========
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window."""
        try:
            window = gw.getActiveWindow()
            if window:
                return self._pyw_to_window_info(window)
            return None
        except Exception as e:
            self.error_handler.log_error(f"Error getting active window: {e}")
            return None
    
    def get_windows(self, title: Optional[str] = None, 
                   class_name: Optional[str] = None, 
                   process_id: Optional[int] = None) -> List[WindowInfo]:
        """Get a list of all windows matching the criteria."""
        try:
            windows = gw.getAllWindows()
            results = []
            
            for window in windows:
                if not window.visible:
                    continue
                    
                if title and not re.search(title, window.title, re.IGNORECASE):
                    continue
                    
                if class_name and hasattr(window, '_hWnd'):
                    buffer = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(window._hWnd, buffer, 256)
                    if not re.search(class_name, buffer.value, re.IGNORECASE):
                        continue
                
                if process_id and hasattr(window, '_processId'):
                    if window._processId != process_id:
                        continue
                
                results.append(self._pyw_to_window_info(window))
            
            return results
        except Exception as e:
            self.error_handler.log_error(f"Error getting windows: {e}")
            return []
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """Find a window by title."""
        try:
            window = gw.getWindowsWithTitle(title)
            if window:
                return self._pyw_to_window_info(window[0])
            return None
        except Exception as e:
            self.error_handler.log_error(f"Error finding window '{title}': {e}")
            return None
    
    def _pyw_to_window_info(self, window) -> WindowInfo:
        """Convert PyGetWindow window to WindowInfo."""
        try:
            return WindowInfo(
                handle=window._hWnd if hasattr(window, '_hWnd') else 0,
                title=window.title,
                class_name=self._get_window_class_name(window._hWnd) if hasattr(window, '_hWnd') else '',
                is_active=window.isActive,
                is_visible=window.visible,
                is_minimized=window.isMinimized,
                is_maximized=window.isMaximized,
                x=window.left,
                y=window.top,
                width=window.width,
                height=window.height,
                process_id=window._processId if hasattr(window, '_processId') else 0,
                process_name=self._get_process_name(window._processId) if hasattr(window, '_processId') else ''
            )
        except Exception as e:
            self.error_handler.log_error(f"Error converting window info: {e}")
            return WindowInfo(0, '', '', False, False, False, False, 0, 0, 0, 0, 0, '')
    
    def _get_window_class_name(self, hwnd: int) -> str:
        """Get the window class name."""
        try:
            buffer = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, buffer, 256)
            return buffer.value
        except Exception:
            return ''
    
    def _get_process_name(self, process_id: int) -> str:
        """Get the name of the process by ID."""
        try:
            import psutil
            process = psutil.Process(process_id)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, ImportError):
            return ''
    
    # ========== Window Control ==========
    
    def activate_window(self, window_info: WindowInfo) -> bool:
        """Activate a window."""
        try:
            if window_info.is_minimized:
                self.user32.ShowWindow(window_info.handle, 9)  # SW_RESTORE = 9
            
            self.user32.SetForegroundWindow(window_info.handle)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error activating window: {e}")
            return False
    
    def close_window(self, window_info: WindowInfo) -> bool:
        """Close a window."""
        try:
            self.user32.PostMessageW(window_info.handle, 0x0010, 0, 0)  # WM_CLOSE
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error closing window: {e}")
            return False
    
    def minimize_window(self, window_info: WindowInfo) -> bool:
        """Minimize a window."""
        try:
            self.user32.ShowWindow(window_info.handle, 6)  # SW_MINIMIZE = 6
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error minimizing window: {e}")
            return False
    
    def maximize_window(self, window_info: WindowInfo) -> bool:
        """Maximize a window."""
        try:
            self.user32.ShowWindow(window_info.handle, 3)  # SW_MAXIMIZE = 3
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error maximizing window: {e}")
            return False
    
    def restore_window(self, window_info: WindowInfo) -> bool:
        """Restore a window from minimized or maximized state."""
        try:
            self.user32.ShowWindow(window_info.handle, 9)  # SW_RESTORE = 9
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error restoring window: {e}")
            return False
    
    def move_window(self, window_info: WindowInfo, x: int, y: int, 
                   width: Optional[int] = None, 
                   height: Optional[int] = None) -> bool:
        """Move and/or resize a window."""
        try:
            if width is None or height is None:
                rect = ctypes.wintypes.RECT()
                self.user32.GetWindowRect(window_info.handle, ctypes.byref(rect))
                if width is None:
                    width = rect.right - rect.left
                if height is None:
                    height = rect.bottom - rect.top
            
            self.user32.MoveWindow(window_info.handle, x, y, width, height, True)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error moving/resizing window: {e}")
            return False
    
    def set_window_title(self, window_info: WindowInfo, title: str) -> bool:
        """Set window title."""
        try:
            self.user32.SetWindowTextW(window_info.handle, title)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error setting window title: {e}")
            return False
    
    def set_window_always_on_top(self, window_info: WindowInfo, 
                               always_on_top: bool = True) -> bool:
        """Set window always on top."""
        try:
            # HWND_TOPMOST = -1, HWND_NOTOPMOST = -2
            hwnd_insert_after = -1 if always_on_top else -2
            self.user32.SetWindowPos(
                window_info.handle, hwnd_insert_after,
                0, 0, 0, 0,
                0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
            )
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error setting window always on top: {e}")
            return False
    
    # ========== Screen Operations ==========
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get the primary screen resolution."""
        try:
            return (self.user32.GetSystemMetrics(0),  # SM_CXSCREEN
                   self.user32.GetSystemMetrics(1))   # SM_CYSCREEN
        except Exception as e:
            self.error_handler.log_error(f"Error getting screen size: {e}")
            return (0, 0)
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """Get the current cursor position."""
        try:
            point = ctypes.wintypes.POINT()
            self.user32.GetCursorPos(ctypes.byref(point))
            return (point.x, point.y)
        except Exception as e:
            self.error_handler.log_error(f"Error getting cursor position: {e}")
            return (0, 0)
    
    def set_cursor_position(self, x: int, y: int) -> bool:
        """Set the cursor position."""
        try:
            self.user32.SetCursorPos(x, y)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error setting cursor position: {e}")
            return False
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
             button: str = 'left', clicks: int = 1, interval: float = 0.1) -> bool:
        """Perform a mouse click."""
        try:
            if x is not None and y is not None:
                self.set_cursor_position(x, y)
            
            pyautogui.click(button=button, clicks=clicks, interval=interval)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error performing click: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.1) -> bool:
        """Type text at the current cursor position."""
        try:
            pyautogui.typewrite(text, interval=interval)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error typing text: {e}")
            return False
    
    def press_key(self, keys: Union[str, List[str]]) -> bool:
        """Press keyboard key(s)."""
        try:
            if isinstance(keys, str):
                keys = [keys]
            
            for key in keys:
                pyautogui.press(key)
            
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error pressing key(s): {e}")
            return False
    
    def hotkey(self, *args) -> bool:
        """Press a combination of keys."""
        try:
            pyautogui.hotkey(*args)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error with hotkey: {e}")
            return False
    
    # ========== System Commands ==========
    
    def lock_workstation(self) -> bool:
        """Lock the workstation."""
        try:
            self.user32.LockWorkStation()
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error locking workstation: {e}")
            return False
    
    def logoff(self) -> bool:
        """Log off the current user."""
        try:
            self.user32.ExitWindowsEx(0, 0)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error logging off: {e}")
            return False
    
    def shutdown(self, force: bool = False) -> bool:
        """Shut down the system."""
        try:
            import os
            os.system("shutdown /s /t 0" + (" /f" if force else ""))
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error shutting down: {e}")
            return False
    
    def restart(self, force: bool = False) -> bool:
        """Restart the system."""
        try:
            import os
            os.system("shutdown /r /t 0" + (" /f" if force else ""))
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error restarting: {e}")
            return False
    
    def hibernate(self) -> bool:
        """Hibernate the system."""
        try:
            import ctypes
            ctypes.windll.PowrProf.SetSuspendState(1, 1, 0)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error hibernating: {e}")
            return False
    
    def sleep(self) -> bool:
        """Put the system to sleep."""
        try:
            import ctypes
            ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error putting system to sleep: {e}")
            return False
    
    def set_display_state(self, state: str) -> bool:
        """Set the display state (on/off)."""
        try:
            if state.lower() == 'off':
                self.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)
            elif state.lower() == 'on':
                self.user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_ON)
            else:
                raise ValueError("State must be 'on' or 'off'")
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error setting display state: {e}")
            return False
