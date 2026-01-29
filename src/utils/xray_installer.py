"""
Xray installation and update utilities.
"""

from .system_installer import (
    InstallStatus,
    check_software_installed,
    run_command
)


XRAY_INSTALL_SCRIPT = "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"


def check_xray_installed() -> InstallStatus:
    """Check if Xray is installed."""
    return check_software_installed("xray", "xray version")


def install_xray() -> tuple[bool, str]:
    """
    Install Xray using official script.
    
    Returns:
        (success, message)
    """
    cmd = f"bash <(curl -L {XRAY_INSTALL_SCRIPT}) install"
    success, output = run_command(cmd, shell=True)
    
    if success:
        return True, "Xray installed successfully"
    else:
        return False, f"Xray installation failed: {output}"


def update_xray() -> tuple[bool, str]:
    """
    Update Xray to the latest version.
    
    Returns:
        (success, message)
    """
    # Check if installed first
    status = check_xray_installed()
    if not status.installed:
        return False, "Xray is not installed. Use install_xray() first."
    
    # Use official script to update
    cmd = f"bash <(curl -L {XRAY_INSTALL_SCRIPT}) install"
    success, output = run_command(cmd, shell=True)
    
    if success:
        return True, "Xray updated successfully"
    else:
        return False, f"Xray update failed: {output}"


def remove_xray() -> tuple[bool, str]:
    """
    Remove Xray installation.
    
    Returns:
        (success, message)
    """
    cmd = f"bash <(curl -L {XRAY_INSTALL_SCRIPT}) remove"
    success, output = run_command(cmd, shell=True)
    
    if success:
        return True, "Xray removed successfully"
    else:
        return False, f"Xray removal failed: {output}"


def get_xray_status() -> dict:
    """
    Get Xray service status.
    
    Returns:
        Status information
    """
    import subprocess
    
    status = {}
    
    # Check installation
    install_status = check_xray_installed()
    status["installed"] = install_status.installed
    status["version"] = install_status.version
    status["path"] = install_status.path
    
    # Check service status
    if install_status.installed:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "xray"],
                capture_output=True,
                text=True,
                timeout=5
            )
            status["service_active"] = result.stdout.strip() == "active"
            status["service_status"] = result.stdout.strip()
        except Exception as e:
            status["service_active"] = False
            status["service_error"] = str(e)
    
    return status
