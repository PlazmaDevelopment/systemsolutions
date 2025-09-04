"""
File system utilities and operations.
"""

import os
import shutil
import tempfile
import zipfile
import tarfile
import fnmatch
import hashlib
import glob
import stat
import pathlib
from typing import List, Dict, Optional, Union, BinaryIO, TextIO, Iterator, Any
from datetime import datetime
from .utils import ErrorHandler, logger

class FileSystem:
    """A class to handle file system operations with error handling and utilities."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    # ========== File Operations ==========
    
    def read_file(self, file_path: str, mode: str = 'r', encoding: str = 'utf-8', 
                 errors: str = 'strict') -> Union[str, bytes]:
        """Read content from a file."""
        try:
            with open(file_path, mode, encoding=encoding, errors=errors) as f:
                return f.read()
        except Exception as e:
            self.error_handler.log_error(f"Error reading file {file_path}: {e}")
            raise
    
    def write_file(self, file_path: str, content: Union[str, bytes], 
                  mode: str = 'w', encoding: str = 'utf-8',
                  create_dirs: bool = True) -> bool:
        """Write content to a file."""
        try:
            if create_dirs:
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
            if 'b' in mode:
                with open(file_path, mode) as f:
                    f.write(content)
            else:
                with open(file_path, mode, encoding=encoding) as f:
                    f.write(content)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error writing to file {file_path}: {e}")
            return False
    
    def copy_file(self, src: str, dst: str, overwrite: bool = True) -> bool:
        """Copy a file from source to destination."""
        try:
            if os.path.exists(dst) and not overwrite:
                return False
                
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error copying file from {src} to {dst}: {e}")
            return False
    
    def move_file(self, src: str, dst: str, overwrite: bool = True) -> bool:
        """Move a file from source to destination."""
        try:
            if os.path.exists(dst):
                if overwrite:
                    os.remove(dst)
                else:
                    return False
                    
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error moving file from {src} to {dst}: {e}")
            return False
    
    def delete_file(self, file_path: str, missing_ok: bool = True) -> bool:
        """Delete a file."""
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            if not missing_ok:
                self.error_handler.log_error(f"File not found: {file_path}")
            return False
        except Exception as e:
            self.error_handler.log_error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a file."""
        try:
            stat_info = os.stat(file_path)
            return {
                'path': os.path.abspath(file_path),
                'size': stat_info.st_size,
                'created': datetime.fromtimestamp(stat_info.st_ctime),
                'modified': datetime.fromtimestamp(stat_info.st_mtime),
                'accessed': datetime.fromtimestamp(stat_info.st_atime),
                'mode': stat.filemode(stat_info.st_mode),
                'inode': stat_info.st_ino,
                'device': stat_info.st_dev,
                'hard_links': stat_info.st_nlink,
                'user_id': stat_info.st_uid,
                'group_id': stat_info.st_gid
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting file info for {file_path}: {e}")
            return None
    
    # ========== Directory Operations ==========
    
    def create_dir(self, dir_path: str, exist_ok: bool = True) -> bool:
        """Create a directory."""
        try:
            os.makedirs(dir_path, exist_ok=exist_ok)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error creating directory {dir_path}: {e}")
            return False
    
    def list_dir(self, dir_path: str, pattern: str = '*', 
                recursive: bool = False) -> List[str]:
        """List files and directories matching a pattern."""
        try:
            if recursive:
                matches = []
                for root, _, files in os.walk(dir_path):
                    for filename in fnmatch.filter(files, pattern):
                        matches.append(os.path.join(root, filename))
                return matches
            else:
                return [f for f in os.listdir(dir_path) 
                       if fnmatch.fnmatch(f, pattern)]
        except Exception as e:
            self.error_handler.log_error(f"Error listing directory {dir_path}: {e}")
            return []
    
    def delete_dir(self, dir_path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        try:
            if recursive:
                shutil.rmtree(dir_path)
            else:
                os.rmdir(dir_path)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error deleting directory {dir_path}: {e}")
            return False
    
    def copy_dir(self, src: str, dst: str, symlinks: bool = False, 
                ignore: Optional[callable] = None) -> bool:
        """Copy a directory recursively."""
        try:
            shutil.copytree(src, dst, symlinks=symlinks, ignore=ignore, 
                          dirs_exist_ok=True)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error copying directory from {src} to {dst}: {e}")
            return False
    
    # ========== File Search ==========
    
    def find_files(self, root_dir: str, pattern: str = '*', 
                  recursive: bool = True) -> List[str]:
        """Find files matching a pattern."""
        try:
            if recursive:
                matches = []
                for root, _, filenames in os.walk(root_dir):
                    for filename in fnmatch.filter(filenames, pattern):
                        matches.append(os.path.join(root, filename))
                return matches
            else:
                return glob.glob(os.path.join(root_dir, pattern))
        except Exception as e:
            self.error_handler.log_error(f"Error finding files in {root_dir}: {e}")
            return []
    
    def find_dirs(self, root_dir: str, pattern: str = '*', 
                 recursive: bool = True) -> List[str]:
        """Find directories matching a pattern."""
        try:
            if recursive:
                matches = []
                for root, dirnames, _ in os.walk(root_dir):
                    for dirname in fnmatch.filter(dirnames, pattern):
                        matches.append(os.path.join(root, dirname))
                return matches
            else:
                return [d for d in os.listdir(root_dir) 
                       if os.path.isdir(os.path.join(root_dir, d)) and 
                       fnmatch.fnmatch(d, pattern)]
        except Exception as e:
            self.error_handler.log_error(f"Error finding directories in {root_dir}: {e}")
            return []
    
    # ========== File Hashing ==========
    
    def get_file_hash(self, file_path: str, algorithm: str = 'sha256', 
                     chunk_size: int = 8192) -> Optional[str]:
        """Calculate hash of a file."""
        try:
            hash_func = getattr(hashlib, algorithm.lower(), None)
            if not hash_func:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
                
            h = hash_func()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    h.update(chunk)
            return h.hexdigest()
        except Exception as e:
            self.error_handler.log_error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    # ========== Archive Operations ==========
    
    def create_archive(self, source_dir: str, output_path: str, 
                      format: str = 'zip') -> bool:
        """Create an archive from a directory."""
        try:
            shutil.make_archive(
                os.path.splitext(output_path)[0],
                format,
                os.path.dirname(source_dir),
                os.path.basename(source_dir)
            )
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error creating archive {output_path}: {e}")
            return False
    
    def extract_archive(self, archive_path: str, extract_dir: str = None, 
                       format: str = None) -> bool:
        """Extract an archive to a directory."""
        try:
            if extract_dir is None:
                extract_dir = os.path.dirname(archive_path)
                
            if format is None:
                if archive_path.endswith('.zip'):
                    format = 'zip'
                elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                    format = 'gztar'
                elif archive_path.endswith('.tar.bz2') or archive_path.endswith('.tbz2'):
                    format = 'bztar'
                elif archive_path.endswith('.tar'):
                    format = 'tar'
                else:
                    raise ValueError("Could not determine archive format")
            
            shutil.unpack_archive(archive_path, extract_dir, format)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error extracting archive {archive_path}: {e}")
            return False
    
    # ========== Temporary Files/Directories ==========
    
    def create_temp_file(self, suffix: str = '', prefix: str = 'tmp', 
                        dir: str = None, text: bool = True) -> str:
        """Create a temporary file and return its path."""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                prefix=prefix,
                dir=dir,
                delete=False,
                mode='w' if text else 'wb'
            ) as f:
                return f.name
        except Exception as e:
            self.error_handler.log_error(f"Error creating temporary file: {e}")
            raise
    
    def create_temp_dir(self, suffix: str = '', prefix: str = 'tmp', 
                       dir: str = None) -> str:
        """Create a temporary directory and return its path."""
        try:
            return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        except Exception as e:
            self.error_handler.log_error(f"Error creating temporary directory: {e}")
            raise
    
    # ========== File Permissions ==========
    
    def set_permissions(self, path: str, mode: int, 
                       recursive: bool = False) -> bool:
        """Set file or directory permissions."""
        try:
            if recursive and os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    os.chmod(root, mode)
                    for d in dirs:
                        os.chmod(os.path.join(root, d), mode)
                    for f in files:
                        os.chmod(os.path.join(root, f), mode)
            else:
                os.chmod(path, mode)
            return True
        except Exception as e:
            self.error_handler.log_error(f"Error setting permissions for {path}: {e}")
            return False
    
    def get_permissions(self, path: str) -> Optional[str]:
        """Get file or directory permissions in octal format."""
        try:
            return oct(os.stat(path).st_mode & 0o777)
        except Exception as e:
            self.error_handler.log_error(f"Error getting permissions for {path}: {e}")
            return None
    
    # ========== File System Information ==========
    
    def get_disk_usage(self, path: str = '/') -> Optional[Dict[str, int]]:
        """Get disk usage statistics."""
        try:
            usage = shutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent_used': (usage.used / usage.total) * 100 if usage.total > 0 else 0
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting disk usage for {path}: {e}")
            return None
    
    def get_file_system_info(self, path: str = '/') -> Optional[Dict[str, Any]]:
        """Get file system information."""
        try:
            statvfs = os.statvfs(path)
            return {
                'block_size': statvfs.f_bsize,
                'fragment_size': statvfs.f_frsize,
                'blocks_total': statvfs.f_blocks,
                'blocks_free': statvfs.f_bfree,
                'blocks_available': statvfs.f_bavail,
                'inodes_total': statvfs.f_files,
                'inodes_free': statvfs.f_ffree,
                'inodes_available': statvfs.f_favail,
                'max_filename_length': statvfs.f_namemax
            }
        except Exception as e:
            self.error_handler.log_error(f"Error getting file system info for {path}: {e}")
            return None
