"""
Installer module for Xray and Nginx.

Handles auto-detection of existing installations and
installs missing dependencies on Linux systems.
"""

import os

from src.utils import (
    detect_distro_family,
    check_xray_installed,
    check_nginx_installed,
    install_xray,
    install_nginx
)


class Installer:
    """Main installer class for Xray and Nginx."""
    
    def __init__(self):
        self.distro = detect_distro_family()
    
    @staticmethod
    def is_root() -> bool:
        """Check if running as root."""
        return os.geteuid() == 0
    
    def check_environment(self) -> dict:
        """Check installation status of all components."""
        xray_status = check_xray_installed()
        nginx_status = check_nginx_installed()
        
        return {
            "distro": self.distro.value,
            "is_root": self.is_root(),
            "xray": xray_status.to_dict(),
            "nginx": nginx_status.to_dict()
        }
    
    def install_missing(self) -> dict:
        """Install missing components."""
        if not self.is_root():
            return {"success": False, "error": "Root privileges required"}
        
        results = {"xray": None, "nginx": None}
        
        # Install Xray if needed
        xray_status = check_xray_installed()
        if not xray_status.installed:
            success, msg = install_xray()
            results["xray"] = {"success": success, "message": msg}
        else:
            results["xray"] = {"success": True, "message": "Already installed"}
        
        # Install Nginx if needed
        nginx_status = check_nginx_installed()
        if not nginx_status.installed:
            success, msg = install_nginx()
            results["nginx"] = {"success": success, "message": msg}
        else:
            results["nginx"] = {"success": True, "message": "Already installed"}
        
        return results


if __name__ == "__main__":
    installer = Installer()
    print("Environment check:")
    import json
    print(json.dumps(installer.check_environment(), indent=2))
