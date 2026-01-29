"""
System software installer utilities.

Handles installation and updates for Xray and Nginx.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class DistroFamily(Enum):
    """Linux distribution families."""
    DEBIAN = "debian"  # Debian, Ubuntu, etc.
    RHEL = "rhel"      # RHEL, CentOS, Fedora, etc.
    ARCH = "arch"      # Arch Linux
    UNKNOWN = "unknown"


@dataclass
class InstallStatus:
    """Installation status for a component."""
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "installed": self.installed,
            "version": self.version,
            "path": self.path
        }


def detect_distro_family() -> DistroFamily:
    """Detect Linux distribution family."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return DistroFamily.UNKNOWN
    
    content = os_release.read_text().lower()
    
    if "debian" in content or "ubuntu" in content:
        return DistroFamily.DEBIAN
    elif "rhel" in content or "centos" in content or "fedora" in content:
        return DistroFamily.RHEL
    elif "arch" in content:
        return DistroFamily.ARCH
    
    return DistroFamily.UNKNOWN


def run_command(cmd: str, shell: bool = True) -> tuple[bool, str]:
    """
    Run a shell command and return success status and output.
    
    Args:
        cmd: Command to run
        shell: Whether to use shell execution
    
    Returns:
        (success, output/error message)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_software_installed(name: str, version_cmd: Optional[str] = None) -> InstallStatus:
    """
    Check if software is installed.
    
    Args:
        name: Software name (e.g., "nginx", "xray")
        version_cmd: Command to get version (e.g., "nginx -v")
    
    Returns:
        Installation status
    """
    import shutil
    
    path = shutil.which(name)
    if not path:
        # Check common installation paths
        common_paths = [f"/usr/local/bin/{name}", f"/usr/bin/{name}", f"/usr/sbin/{name}"]
        for p in common_paths:
            if Path(p).exists():
                path = p
                break
    
    if not path:
        return InstallStatus(installed=False)
    
    version = None
    if version_cmd:
        try:
            result = subprocess.run(
                version_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            # Try to extract version from output
            output = result.stdout + result.stderr
            lines = output.strip().split("\n")
            if lines:
                version = lines[0].strip()
        except Exception:
            pass
    
    return InstallStatus(installed=True, version=version, path=path)
