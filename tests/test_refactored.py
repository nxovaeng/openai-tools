"""
Tests for refactored code.

Tests the new utils modules and updated installer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.utils import (
    DistroFamily,
    InstallStatus,
    detect_distro_family,
    check_software_installed,
    check_xray_installed,
    check_nginx_installed,
    install_xray,
    install_nginx,
    update_xray,
    update_nginx,
    get_xray_status,
    get_nginx_status,
    test_nginx_config,
    reload_nginx
)

from src.core.installer import Installer


class TestSystemInstaller:
    """Test system installer utilities."""
    
    def test_install_status_to_dict(self):
        """Test InstallStatus to_dict method."""
        status = InstallStatus(
            installed=True,
            version="1.8.0",
            path="/usr/local/bin/xray"
        )
        
        result = status.to_dict()
        
        assert result["installed"] is True
        assert result["version"] == "1.8.0"
        assert result["path"] == "/usr/local/bin/xray"
    
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_detect_distro_debian(self, mock_read, mock_exists):
        """Test Debian distribution detection."""
        mock_exists.return_value = True
        mock_read.return_value = "ID=ubuntu\nNAME=Ubuntu"
        
        distro = detect_distro_family()
        
        assert distro == DistroFamily.DEBIAN
    
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_detect_distro_rhel(self, mock_read, mock_exists):
        """Test RHEL distribution detection."""
        mock_exists.return_value = True
        mock_read.return_value = "ID=centos\nNAME=CentOS"
        
        distro = detect_distro_family()
        
        assert distro == DistroFamily.RHEL
    
    @patch("shutil.which")
    def test_check_software_installed_found(self, mock_which):
        """Test software check when installed."""
        mock_which.return_value = "/usr/bin/nginx"
        
        status = check_software_installed("nginx")
        
        assert status.installed is True
        assert status.path == "/usr/bin/nginx"
    
    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    def test_check_software_installed_not_found(self, mock_exists, mock_which):
        """Test software check when not installed."""
        mock_which.return_value = None
        mock_exists.return_value = False
        
        status = check_software_installed("nginx")
        
        assert status.installed is False
        assert status.path is None


class TestXrayInstaller:
    """Test Xray installer utilities."""
    
    @patch("src.utils.xray_installer.check_software_installed")
    def test_check_xray_installed(self, mock_check):
        """Test Xray installation check."""
        mock_check.return_value = InstallStatus(
            installed=True,
            version="1.8.0",
            path="/usr/local/bin/xray"
        )
        
        status = check_xray_installed()
        
        assert status.installed is True
        assert status.version == "1.8.0"
    
    @patch("src.utils.xray_installer.run_command")
    def test_install_xray_success(self, mock_run):
        """Test successful Xray installation."""
        mock_run.return_value = (True, "Installation complete")
        
        success, message = install_xray()
        
        assert success is True
        assert "successfully" in message.lower()
    
    @patch("src.utils.xray_installer.run_command")
    def test_install_xray_failure(self, mock_run):
        """Test failed Xray installation."""
        mock_run.return_value = (False, "Installation failed")
        
        success, message = install_xray()
        
        assert success is False
        assert "failed" in message.lower()
    
    @patch("src.utils.xray_installer.check_xray_installed")
    @patch("src.utils.xray_installer.run_command")
    def test_update_xray_not_installed(self, mock_run, mock_check):
        """Test update when Xray is not installed."""
        mock_check.return_value = InstallStatus(installed=False)
        
        success, message = update_xray()
        
        assert success is False
        assert "not installed" in message.lower()


class TestNginxInstaller:
    """Test Nginx installer utilities."""
    
    @patch("src.utils.nginx_installer.check_software_installed")
    def test_check_nginx_installed(self, mock_check):
        """Test Nginx installation check."""
        mock_check.return_value = InstallStatus(
            installed=True,
            version="1.18.0",
            path="/usr/sbin/nginx"
        )
        
        status = check_nginx_installed()
        
        assert status.installed is True
        assert status.version == "1.18.0"
    
    @patch("src.utils.nginx_installer.detect_distro_family")
    @patch("src.utils.nginx_installer.run_command")
    def test_install_nginx_debian(self, mock_run, mock_distro):
        """Test Nginx installation on Debian."""
        mock_distro.return_value = DistroFamily.DEBIAN
        mock_run.return_value = (True, "OK")
        
        success, message = install_nginx()
        
        assert success is True
        assert "successfully" in message.lower()
    
    @patch("src.utils.nginx_installer.detect_distro_family")
    def test_install_nginx_unsupported(self, mock_distro):
        """Test Nginx installation on unsupported distro."""
        mock_distro.return_value = DistroFamily.UNKNOWN
        
        success, message = install_nginx()
        
        assert success is False
        assert "unsupported" in message.lower()
    
    @patch("src.utils.nginx_installer.run_command")
    def test_test_nginx_config_success(self, mock_run):
        """Test successful Nginx config test."""
        mock_run.return_value = (True, "syntax is ok")
        
        success, output = test_nginx_config()
        
        assert success is True
    
    @patch("src.utils.nginx_installer.test_nginx_config")
    @patch("src.utils.nginx_installer.run_command")
    def test_reload_nginx_success(self, mock_run, mock_test):
        """Test successful Nginx reload."""
        mock_test.return_value = (True, "OK")
        mock_run.return_value = (True, "OK")
        
        success, message = reload_nginx()
        
        assert success is True
        assert "successfully" in message.lower()
    
    @patch("src.utils.nginx_installer.test_nginx_config")
    def test_reload_nginx_config_fail(self, mock_test):
        """Test Nginx reload with failed config test."""
        mock_test.return_value = (False, "syntax error")
        
        success, message = reload_nginx()
        
        assert success is False
        assert "failed" in message.lower()


class TestInstaller:
    """Test main Installer class."""
    
    @patch("src.core.installer.detect_distro_family")
    def test_installer_init(self, mock_distro):
        """Test Installer initialization."""
        mock_distro.return_value = DistroFamily.DEBIAN
        
        installer = Installer()
        
        assert installer.distro == DistroFamily.DEBIAN
    
    @patch("os.geteuid")
    def test_is_root_true(self, mock_geteuid):
        """Test root check when running as root."""
        mock_geteuid.return_value = 0
        
        assert Installer.is_root() is True
    
    @patch("os.geteuid")
    def test_is_root_false(self, mock_geteuid):
        """Test root check when not running as root."""
        mock_geteuid.return_value = 1000
        
        assert Installer.is_root() is False
    
    @patch("src.core.installer.check_xray_installed")
    @patch("src.core.installer.check_nginx_installed")
    @patch("src.core.installer.detect_distro_family")
    def test_check_environment(self, mock_distro, mock_nginx, mock_xray):
        """Test environment check."""
        mock_distro.return_value = DistroFamily.DEBIAN
        mock_xray.return_value = InstallStatus(installed=True, version="1.8.0")
        mock_nginx.return_value = InstallStatus(installed=True, version="1.18.0")
        
        installer = Installer()
        env = installer.check_environment()
        
        assert env["distro"] == "debian"
        assert env["xray"]["installed"] is True
        assert env["nginx"]["installed"] is True
    
    @patch("src.core.installer.Installer.is_root")
    def test_install_missing_not_root(self, mock_root):
        """Test install_missing without root privileges."""
        mock_root.return_value = False
        
        installer = Installer()
        result = installer.install_missing()
        
        assert result["success"] is False
        assert "root" in result["error"].lower()
    
    @patch("src.core.installer.Installer.is_root")
    @patch("src.core.installer.check_xray_installed")
    @patch("src.core.installer.check_nginx_installed")
    @patch("src.core.installer.install_xray")
    @patch("src.core.installer.install_nginx")
    def test_install_missing_success(
        self, mock_install_nginx, mock_install_xray,
        mock_check_nginx, mock_check_xray, mock_root
    ):
        """Test successful installation of missing components."""
        mock_root.return_value = True
        mock_check_xray.return_value = InstallStatus(installed=False)
        mock_check_nginx.return_value = InstallStatus(installed=False)
        mock_install_xray.return_value = (True, "Xray installed")
        mock_install_nginx.return_value = (True, "Nginx installed")
        
        installer = Installer()
        result = installer.install_missing()
        
        assert result["xray"]["success"] is True
        assert result["nginx"]["success"] is True
    
    @patch("src.core.installer.Installer.is_root")
    @patch("src.core.installer.check_xray_installed")
    @patch("src.core.installer.check_nginx_installed")
    def test_install_missing_already_installed(
        self, mock_check_nginx, mock_check_xray, mock_root
    ):
        """Test install_missing when components already installed."""
        mock_root.return_value = True
        mock_check_xray.return_value = InstallStatus(installed=True)
        mock_check_nginx.return_value = InstallStatus(installed=True)
        
        installer = Installer()
        result = installer.install_missing()
        
        assert result["xray"]["success"] is True
        assert "already" in result["xray"]["message"].lower()
        assert result["nginx"]["success"] is True
        assert "already" in result["nginx"]["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
