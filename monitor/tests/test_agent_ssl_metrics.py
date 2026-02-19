import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
import time
import subprocess
import logging
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import threading
import urllib
import urllib.error

# Setup Django environment for AutomatedAgentDeployer import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
import django
django.setup()

from auto_deploy_agents import AutomatedAgentDeployer

# Temporarily suppress logging during test setup
logging.disable(logging.CRITICAL)

class TestAgentSSLMetrics(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.mock_agent_subprocess_run = MagicMock()
        cls.mock_agent_os_path_exists = MagicMock()
        cls.mock_agent_os_path_isdir = MagicMock()
        cls.mock_agent_os_listdir = MagicMock()

        cls.deployer = AutomatedAgentDeployer()
        cls.agent_files_dir = Path("agent_files_ssl_test")
        
        if cls.agent_files_dir.exists():
            shutil.rmtree(cls.agent_files_dir)
        cls.agent_files_dir.mkdir(exist_ok=True)
        
        original_create_agent_files = cls.deployer.create_agent_files
        def mocked_create_agent_files():
            original_agent_dir = original_create_agent_files()
            shutil.copy(original_agent_dir / "serverwatch-agent.py", cls.agent_files_dir)
            if original_agent_dir.exists():
                 shutil.rmtree(original_agent_dir)
            return cls.agent_files_dir

        cls.deployer.create_agent_files = mocked_create_agent_files
        generated_agent_dir = cls.deployer.create_agent_files()
        
        agent_script_path = generated_agent_dir / "serverwatch-agent.py"
        with open(agent_script_path, "r", encoding='utf-8') as f:
            agent_script_content = f.read()

        cls.mock_subprocess = MagicMock()
        cls.mock_subprocess.run = cls.mock_agent_subprocess_run
        cls.mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired
        
        # Patching globally to ensure exec uses them
        cls.patchers = [
            patch('subprocess.run', cls.mock_agent_subprocess_run),
            patch('os.path.exists', cls.mock_agent_os_path_exists),
            patch('os.path.isdir', cls.mock_agent_os_path_isdir),
            patch('os.listdir', cls.mock_agent_os_listdir),
        ]
        for p in cls.patchers:
            p.start()

        mock_utcnow = MagicMock(return_value=datetime.now())
        mock_datetime_class = MagicMock()
        mock_datetime_class.utcnow = mock_utcnow
        mock_datetime_class.now = MagicMock(return_value=datetime.now())
        mock_datetime_class.fromtimestamp = datetime.fromtimestamp
        mock_datetime_class.strptime = datetime.strptime

        mock_os_path_module = MagicMock()
        mock_os_path_module.exists = cls.mock_agent_os_path_exists
        mock_os_path_module.isdir = cls.mock_agent_os_path_isdir
        mock_os_path_module.join = os.path.join
        mock_os_path_module.basename = os.path.basename

        cls.agent_module_globals = {
            'os': MagicMock(
                path=mock_os_path_module,
                getloadavg=MagicMock(return_value=(0.5, 0.3, 0.1)),
                listdir=cls.mock_agent_os_listdir,
                statvfs=MagicMock(return_value=MagicMock(f_blocks=1000, f_frsize=1024, f_bavail=500)),
                makedirs=MagicMock(),
                pathconf=MagicMock(return_value=4096),
                getmtime=MagicMock(return_value=time.time())
            ),
            'sys': sys,
            'time': time,
            'json': json,
            'socket': MagicMock(),
            'logging': logging,
            'threading': threading,
            'subprocess': cls.mock_subprocess,
            'urllib': MagicMock(request=MagicMock(urlopen=MagicMock(), Request=MagicMock()), error=urllib.error),
            'datetime': mock_datetime_class,
            'Path': Path
        }
        
        exec(agent_script_content, cls.agent_module_globals)
        cls.ServerAgent = cls.agent_module_globals['ServerAgent']

    @classmethod
    def tearDownClass(cls):
        for p in cls.patchers:
            p.stop()

        if cls.agent_files_dir.exists():
            shutil.rmtree(cls.agent_files_dir)
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.agent = self.ServerAgent(config_file="nonexistent_config.json")
        self.agent.logger = MagicMock()
        self.__class__.mock_agent_subprocess_run.reset_mock()
        self.__class__.mock_agent_subprocess_run.side_effect = None
        
        self.__class__.mock_agent_os_path_exists.reset_mock()
        self.__class__.mock_agent_os_path_isdir.reset_mock()
        self.__class__.mock_agent_os_listdir.reset_mock()

    def test_get_ssl_metrics_success(self):
        """Test successful collection of SSL metrics from a valid certificate"""
        cert_path = "/etc/letsencrypt/live/example.com/cert.pem"
        self.__class__.mock_agent_os_path_exists.return_value = True
        
        # Mock openssl output for expiry and issuer/subject
        def custom_run(cmd, **kwargs):
            if "openssl x509 -enddate" in cmd:
                return MagicMock(stdout="notAfter=Jan 27 23:59:59 2027 GMT\n", returncode=0)
            if "openssl x509 -subject -issuer" in cmd:
                return MagicMock(stdout="subject=CN = example.com\nissuer=C = US, O = Let's Encrypt, CN = R3\n", returncode=0)
            return MagicMock(stdout="", returncode=0)
        
        self.__class__.mock_agent_subprocess_run.side_effect = custom_run
        
        metrics = self.agent.get_ssl_metrics([cert_path])
        
        self.assertEqual(len(metrics), 1)
        m = metrics[0]
        self.assertEqual(m['common_name'], "example.com")
        self.assertEqual(m['issuer'], "Let's Encrypt")
        self.assertIn("2027", m['expiry_date'])
        self.assertGreater(m['days_remaining'], 300)
        self.assertEqual(m['status'], 'ok')

    def test_discover_ssl_certificates(self):
        """Test automatic discovery of SSL certificates in standard paths"""
        self.__class__.mock_agent_os_path_exists.return_value = True
        self.__class__.mock_agent_os_path_isdir.return_value = True
        self.__class__.mock_agent_os_listdir.return_value = ["example.com", "other.com", "README"]
        
        certs = self.agent.discover_ssl_certificates()
        print(f"DEBUG: Found certs: {certs}")
        print(f"DEBUG: exists calls: {self.__class__.mock_agent_os_path_exists.call_args_list}")
        
        self.assertIn(os.path.join("/etc/letsencrypt/live", "example.com", "fullchain.pem"), certs)
        self.assertIn(os.path.join("/etc/letsencrypt/live", "other.com", "fullchain.pem"), certs)