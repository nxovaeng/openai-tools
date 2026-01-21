"""
Installer module for Caddy and Xray.

Handles auto-detection of existing installations and
installs missing dependencies on Linux systems.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
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


class SystemDetector:
    """Detect system information."""
    
    @staticmethod
    def get_distro_family() -> DistroFamily:
        """Detect Linux distribution family."""
        os_release = "/etc/os-release"
        if not os.path.exists(os_release):
            return DistroFamily.UNKNOWN
        
        with open(os_release) as f:
            content = f.read().lower()
        
        if "debian" in content or "ubuntu" in content:
            return DistroFamily.DEBIAN
        elif "rhel" in content or "centos" in content or "fedora" in content:
            return DistroFamily.RHEL
        elif "arch" in content:
            return DistroFamily.ARCH
        
        return DistroFamily.UNKNOWN
    
    @staticmethod
    def is_root() -> bool:
        """Check if running as root."""
        return os.geteuid() == 0


class CaddyInstaller:
    """Caddy installation handler."""
    
    @staticmethod
    def check_installed() -> InstallStatus:
        """Check if Caddy is installed."""
        caddy_path = shutil.which("caddy")
        if not caddy_path:
            return InstallStatus(installed=False)
        
        try:
            result = subprocess.run(
                ["caddy", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            version = result.stdout.strip().split()[0] if result.stdout else None
            return InstallStatus(installed=True, version=version, path=caddy_path)
        except Exception:
            return InstallStatus(installed=True, path=caddy_path)
    
    @staticmethod
    def install(distro: DistroFamily) -> tuple[bool, str]:
        """
        Install Caddy using official method.
        
        Returns (success, message).
        """
        if distro == DistroFamily.DEBIAN:
            commands = [
                "apt-get update",
                "apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl",
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg",
                "curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list",
                "apt-get update",
                "apt-get install -y caddy"
            ]
        elif distro == DistroFamily.RHEL:
            commands = [
                "yum install -y 'dnf-command(copr)' || true",
                "dnf copr enable -y @caddy/caddy || yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/g/caddy/caddy/repo/epel-7/group_caddy-caddy-epel-7.repo",
                "dnf install -y caddy || yum install -y caddy"
            ]
        elif distro == DistroFamily.ARCH:
            commands = ["pacman -Sy --noconfirm caddy"]
        else:
            return False, f"Unsupported distribution: {distro.value}"
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0 and "already installed" not in result.stderr.lower():
                return False, f"Command failed: {cmd}\n{result.stderr}"
        
        return True, "Caddy installed successfully"


class XrayInstaller:
    """Xray installation handler."""
    
    INSTALL_SCRIPT = "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"
    
    @staticmethod
    def check_installed() -> InstallStatus:
        """Check if Xray is installed."""
        xray_path = shutil.which("xray")
        if not xray_path:
            # Check common installation paths
            common_paths = ["/usr/local/bin/xray", "/usr/bin/xray"]
            for path in common_paths:
                if os.path.exists(path):
                    xray_path = path
                    break
        
        if not xray_path:
            return InstallStatus(installed=False)
        
        try:
            result = subprocess.run(
                [xray_path, "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse version from output like "Xray 1.8.x ..."
            lines = result.stdout.strip().split("\n")
            version = lines[0].split()[1] if lines and len(lines[0].split()) > 1 else None
            return InstallStatus(installed=True, version=version, path=xray_path)
        except Exception:
            return InstallStatus(installed=True, path=xray_path)
    
    @staticmethod
    def install() -> tuple[bool, str]:
        """
        Install Xray using official script.
        
        Returns (success, message).
        """
        cmd = f"bash <(curl -L {XrayInstaller.INSTALL_SCRIPT}) install"
        result = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False, f"Xray installation failed:\n{result.stderr}"
        
        return True, "Xray installed successfully"


class Installer:
    """Main installer class."""
    
    def __init__(self):
        self.detector = SystemDetector()
        self.distro = self.detector.get_distro_family()
        self.caddy = CaddyInstaller()
        self.xray = XrayInstaller()
    
    def check_environment(self) -> dict:
        """Check installation status of all components."""
        return {
            "distro": self.distro.value,
            "is_root": self.detector.is_root(),
            "caddy": self.caddy.check_installed().to_dict(),
            "xray": self.xray.check_installed().to_dict()
        }
    
    def install_missing(self) -> dict:
        """Install missing components."""
        if not self.detector.is_root():
            return {"success": False, "error": "Root privileges required"}
        
        results = {"caddy": None, "xray": None}
        
        # Install Caddy if needed
        caddy_status = self.caddy.check_installed()
        if not caddy_status.installed:
            success, msg = self.caddy.install(self.distro)
            results["caddy"] = {"success": success, "message": msg}
        else:
            results["caddy"] = {"success": True, "message": "Already installed"}
        
        # Install Xray if needed
        xray_status = self.xray.check_installed()
        if not xray_status.installed:
            success, msg = self.xray.install()
            results["xray"] = {"success": success, "message": msg}
        else:
            results["xray"] = {"success": True, "message": "Already installed"}
        
        return results


if __name__ == "__main__":
    installer = Installer()
    print("Environment check:")
    import json
    print(json.dumps(installer.check_environment(), indent=2))
