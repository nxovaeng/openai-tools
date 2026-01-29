"""
Utility modules for system management.
"""

from .system_installer import (
    DistroFamily,
    InstallStatus,
    detect_distro_family,
    check_software_installed,
    run_command
)

from .xray_installer import (
    check_xray_installed,
    install_xray,
    update_xray,
    remove_xray,
    get_xray_status
)

from .nginx_installer import (
    check_nginx_installed,
    install_nginx,
    update_nginx,
    remove_nginx,
    get_nginx_status,
    test_nginx_config,
    reload_nginx,
    restart_nginx
)

__all__ = [
    # System installer
    "DistroFamily",
    "InstallStatus",
    "detect_distro_family",
    "check_software_installed",
    "run_command",
    
    # Xray installer
    "check_xray_installed",
    "install_xray",
    "update_xray",
    "remove_xray",
    "get_xray_status",
    
    # Nginx installer
    "check_nginx_installed",
    "install_nginx",
    "update_nginx",
    "remove_nginx",
    "get_nginx_status",
    "test_nginx_config",
    "reload_nginx",
    "restart_nginx",
]
