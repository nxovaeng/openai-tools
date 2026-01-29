"""
Nginx installation and update utilities.
"""

from .system_installer import (
    DistroFamily,
    InstallStatus,
    check_software_installed,
    detect_distro_family,
    run_command
)


def check_nginx_installed() -> InstallStatus:
    """Check if Nginx is installed."""
    return check_software_installed("nginx", "nginx -v")


def install_nginx() -> tuple[bool, str]:
    """
    Install Nginx using system package manager.
    
    Returns:
        (success, message)
    """
    distro = detect_distro_family()
    
    if distro == DistroFamily.DEBIAN:
        commands = [
            "apt-get update",
            "apt-get install -y nginx"
        ]
    elif distro == DistroFamily.RHEL:
        commands = [
            "yum install -y epel-release || dnf install -y epel-release",
            "yum install -y nginx || dnf install -y nginx"
        ]
    elif distro == DistroFamily.ARCH:
        commands = ["pacman -Sy --noconfirm nginx"]
    else:
        return False, f"Unsupported distribution: {distro.value}"
    
    for cmd in commands:
        success, output = run_command(cmd)
        if not success and "already installed" not in output.lower():
            return False, f"Command failed: {cmd}\n{output}"
    
    return True, "Nginx installed successfully"


def update_nginx() -> tuple[bool, str]:
    """
    Update Nginx to the latest version.
    
    Returns:
        (success, message)
    """
    # Check if installed first
    status = check_nginx_installed()
    if not status.installed:
        return False, "Nginx is not installed. Use install_nginx() first."
    
    distro = detect_distro_family()
    
    if distro == DistroFamily.DEBIAN:
        commands = [
            "apt-get update",
            "apt-get upgrade -y nginx"
        ]
    elif distro == DistroFamily.RHEL:
        commands = ["yum update -y nginx || dnf update -y nginx"]
    elif distro == DistroFamily.ARCH:
        commands = ["pacman -Syu --noconfirm nginx"]
    else:
        return False, f"Unsupported distribution: {distro.value}"
    
    for cmd in commands:
        success, output = run_command(cmd)
        if not success:
            return False, f"Update failed: {output}"
    
    return True, "Nginx updated successfully"


def remove_nginx() -> tuple[bool, str]:
    """
    Remove Nginx installation.
    
    Returns:
        (success, message)
    """
    distro = detect_distro_family()
    
    if distro == DistroFamily.DEBIAN:
        cmd = "apt-get remove -y nginx && apt-get autoremove -y"
    elif distro == DistroFamily.RHEL:
        cmd = "yum remove -y nginx || dnf remove -y nginx"
    elif distro == DistroFamily.ARCH:
        cmd = "pacman -R --noconfirm nginx"
    else:
        return False, f"Unsupported distribution: {distro.value}"
    
    success, output = run_command(cmd)
    
    if success:
        return True, "Nginx removed successfully"
    else:
        return False, f"Nginx removal failed: {output}"


def get_nginx_status() -> dict:
    """
    Get Nginx service status.
    
    Returns:
        Status information
    """
    import subprocess
    
    status = {}
    
    # Check installation
    install_status = check_nginx_installed()
    status["installed"] = install_status.installed
    status["version"] = install_status.version
    status["path"] = install_status.path
    
    # Check service status
    if install_status.installed:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "nginx"],
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


def test_nginx_config() -> tuple[bool, str]:
    """
    Test Nginx configuration syntax.
    
    Returns:
        (success, output)
    """
    success, output = run_command("nginx -t")
    return success, output


def reload_nginx() -> tuple[bool, str]:
    """
    Reload Nginx configuration without downtime.
    
    Returns:
        (success, message)
    """
    # Test config first
    test_success, test_output = test_nginx_config()
    if not test_success:
        return False, f"Configuration test failed: {test_output}"
    
    # Reload
    success, output = run_command("nginx -s reload")
    
    if success:
        return True, "Nginx reloaded successfully"
    else:
        return False, f"Nginx reload failed: {output}"


def restart_nginx() -> tuple[bool, str]:
    """
    Restart Nginx service.
    
    Returns:
        (success, message)
    """
    success, output = run_command("systemctl restart nginx")
    
    if success:
        return True, "Nginx restarted successfully"
    else:
        return False, f"Nginx restart failed: {output}"
