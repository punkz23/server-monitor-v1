import unittest
from unittest.mock import MagicMock
import os
import sys
import json
import time
import subprocess
import logging
import re
import shutil
from pathlib import Path
from datetime import datetime # Import datetime for utcnow mock
import threading # Added missing import for threading
import urllib # Added missing import for urllib
import urllib.error # Added missing import for urllib.error

# Setup Django environment for AutomatedAgentDeployer import
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverwatch.settings')
import django
django.setup()

from auto_deploy_agents import AutomatedAgentDeployer

# Temporarily suppress logging during test setup to avoid clutter
logging.disable(logging.CRITICAL)

# Global mocks for os.path.exists and os.path.isdir
mock_os_path_exists_global = MagicMock()
mock_os_path_isdir_global = MagicMock()


class TestAgentDirectoryMetrics(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Global mock for subprocess.run so all test methods can access and reset it
        cls.mock_agent_subprocess_run = MagicMock()
        
        # Create a dummy AutomatedAgentDeployer to generate the agent files
        cls.deployer = AutomatedAgentDeployer()
        cls.agent_files_dir = Path("agent_files_test_env") # Use a separate test directory
        
        # Ensure the test directory is clean before creating files
        if cls.agent_files_dir.exists():
            shutil.rmtree(cls.agent_files_dir)
        cls.agent_files_dir.mkdir(exist_ok=True)
        
        # Call create_agent_files to generate the embedded agent script into our test dir
        original_create_agent_files = cls.deployer.create_agent_files
        def mocked_create_agent_files():
            # The original method will generate files to "agent_files" in the root
            original_agent_dir = original_create_agent_files()
            
            # Now, copy them to our test-specific agent_files_dir
            shutil.copy(original_agent_dir / "serverwatch-agent.py", cls.agent_files_dir)
            shutil.copy(original_agent_dir / "requirements.txt", cls.agent_files_dir)
            shutil.copy(original_agent_dir / "install.sh", cls.agent_files_dir)
            
            # Clean up the root agent_files dir created by the deployer
            if original_agent_dir.exists():
                 shutil.rmtree(original_agent_dir)
            return cls.agent_files_dir

        cls.deployer.create_agent_files = mocked_create_agent_files
        generated_agent_dir = cls.deployer.create_agent_files()
        
        # Read the generated agent script
        agent_script_path = generated_agent_dir / "serverwatch-agent.py"
        with open(agent_script_path, "r", encoding='utf-8') as f:
            agent_script_content = f.read()

        # Dynamically load the ServerAgent class from the generated script
        # Mock datetime.utcnow in agent context
        mock_utcnow = MagicMock(return_value=datetime.now())
        mock_datetime_class = MagicMock()
        mock_datetime_class.utcnow = mock_utcnow
        mock_datetime_class.now = MagicMock(return_value=datetime.now()) # For get_cpu_times sleep calc
        
        # Create a mock for the subprocess module
        mock_subprocess_module = MagicMock()
        mock_subprocess_module.run = cls.mock_agent_subprocess_run # Use the class-level mock
        mock_subprocess_module.TimeoutExpired = subprocess.TimeoutExpired

        # Prepare mocks for os.path functions that the agent will use
        mock_os_path_module = MagicMock()
        mock_os_path_module.exists = mock_os_path_exists_global
        mock_os_path_module.isdir = mock_os_path_isdir_global

        # Prepare the execution context for the agent script
        # This mocks out all external dependencies the agent script uses
        cls.agent_module_globals = {
            'os': MagicMock( # Mock the entire os module
                path=mock_os_path_module, # Use our specific path mocks
                getloadavg=MagicMock(return_value=(0.5, 0.3, 0.1)),
                listdir=MagicMock(return_value=['1', '2', '3']),
                statvfs=MagicMock(return_value=MagicMock(f_blocks=1000, f_frsize=1024, f_bavail=500)), # Mock statvfs
                makedirs=MagicMock(),
                pathconf=MagicMock(return_value=4096) # Mocked for pathlib.Path
            ),
            'sys': sys, # Real sys module needed for exec
            'time': time, # Real time module for sleep
            'json': json,
            'socket': MagicMock(),
            'logging': logging, # Use real logging, but disabled above
            'threading': threading, # Real threading
            'subprocess': mock_subprocess_module, # Use our explicit mock_subprocess_module
            'urllib': MagicMock(request=MagicMock(urlopen=MagicMock(), Request=MagicMock()), error=urllib.error), # Mock urllib methods
            'datetime': mock_datetime_class, # Use our mock datetime
            'Path': Path # Real Path object
        }
        
        exec(agent_script_content, cls.agent_module_globals)
        cls.ServerAgent = cls.agent_module_globals['ServerAgent']

        # Create dummy directories and files for testing os.path.exists and isdir
        os.makedirs('/test/path1', exist_ok=True)
        with open('/test/path1/file1.txt', 'w') as f:
            f.write('test')
        os.makedirs('/test/path2/subdir', exist_ok=True)
        with open('/test/path2/subdir/file2.txt', 'w') as f:
            f.write('test')

    @classmethod
    def tearDownClass(cls):
        # Clean up generated agent files and dummy directories
        if cls.agent_files_dir.exists():
            shutil.rmtree(cls.agent_files_dir)
        if os.path.exists('/test'):
            shutil.rmtree('/test')
        
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.agent = self.ServerAgent(config_file="nonexistent_config.json")
        self.agent.config = {
            "log_level": "CRITICAL", # Suppress agent's internal logging during test
            "monitored_directories": ["/test/path1", "/test/path2"],
            "directory_timeout": 5
        }
        # Use the mocked logger from the exec context
        self.agent.logger = MagicMock()
        
        # Reset subprocess.run mock for each test
        self.__class__.mock_agent_subprocess_run.reset_mock()
        self.__class__.mock_agent_subprocess_run.side_effect = None # Clear any previous side effects
        
        # Reset os.path mocks
        mock_os_path_exists_global.reset_mock()
        mock_os_path_isdir_global.reset_mock()
        mock_os_path_exists_global.side_effect = lambda x: x.startswith('/test') or os.path.exists(x)
        mock_os_path_isdir_global.side_effect = lambda x: x.startswith('/test') or os.path.isdir(x)
        
    def test_get_directory_metrics_success_case(self):
        # Mock find . -type f | wc -l for path1
        self.__class__.mock_agent_subprocess_run.side_effect = [
            MagicMock(stdout='500\n', returncode=0),
            MagicMock(stdout='100\t/test/path1\n', returncode=0),
        ]
        
        metrics = self.agent.get_directory_metrics("/test/path1")
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics['path'], "/test/path1")
        self.assertEqual(metrics['file_count'], 500)
        self.assertEqual(metrics['size_mb'], 100)
        self.assertEqual(metrics['status'], 'ok')
        self.assertIsNone(metrics['error'])

    def test_get_directory_metrics_malformed_size_output(self):
        # Test error if du -sm output is malformed
        self.__class__.mock_agent_subprocess_run.side_effect = [
            MagicMock(stdout='500\n', returncode=0), # find . -type f | wc -l for path1
            MagicMock(stdout='malformed output\n', returncode=0), # du -sm for path1
        ]
        metrics_malformed_size = self.agent.get_directory_metrics("/test/path1")
        self.assertEqual(metrics_malformed_size['status'], 'error')
        self.assertIn('invalid literal for int()', metrics_malformed_size['error'])


    def test_get_directory_metrics_timeout(self):
        # Mock a timeout for du -sm
        self.__class__.mock_agent_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="du", timeout=5, output=b"", stderr=b"")
        
        metrics = self.agent.get_directory_metrics("/test/path1")
        
        self.assertEqual(metrics['path'], "/test/path1")
        self.assertIsNone(metrics['size_mb'])
        self.assertIsNone(metrics['file_count'])
        self.assertEqual(metrics['status'], 'error')
        self.assertIn('timed out', metrics['error'])

    def test_get_directory_metrics_non_existent_path(self):
        # Configure mocks for os.path.exists and isdir
        mock_os_path_exists_global.side_effect = lambda x: False
        mock_os_path_isdir_global.side_effect = lambda x: False

        metrics = self.agent.get_directory_metrics("/nonexistent/path")
        self.assertEqual(metrics['status'], 'error')
        self.assertIn('Directory not found', metrics['error'])
        self.__class__.mock_agent_subprocess_run.assert_not_called() # No subprocess calls if path doesn't exist

    def test_get_system_metrics_with_directory_metrics(self):
        # Mock subprocess.run for both system and directory metrics
        # The agent makes several calls to subprocess.run (e.g., for CPU % calc, then for each dir)
        self.__class__.mock_agent_subprocess_run.side_effect = [
            # CPU stat1 read in get_system_metrics
            MagicMock(stdout='cpu  100 200 300 400 500 600 700 800 900 1000\n', returncode=0),
            # CPU stat2 read in get_system_metrics
            MagicMock(stdout='cpu  101 201 301 401 501 601 701 801 901 1001\n', returncode=0),
            # Directory /test/path1 (file_count then size_mb)
            MagicMock(stdout='500\n', returncode=0), # find . -type f | wc -l for /test/path1
            MagicMock(stdout='100\t/test/path1\n', returncode=0), # du -sm for /test/path1
            # Directory /test/path2 (file_count then size_mb)
            MagicMock(stdout='100\n', returncode=0), # find . -type f | wc -l for /test/path2
            MagicMock(stdout='50\t/test/path2\n', returncode=0), # du -sm for /test/path2
        ]
        
        # Mock os functions. Already mocked at the exec context, but ensure side_effects are correct
        mock_os_path_exists_global.side_effect = lambda x: x.startswith('/test') or os.path.exists(x)
        mock_os_path_isdir_global.side_effect = lambda x: x.startswith('/test') or os.path.isdir(x)
        self.__class__.agent_module_globals['os'].getloadavg.return_value = (0.5, 0.3, 0.1)
        self.__class__.agent_module_globals['os'].listdir.return_value = ['1', '2']
        self.__class__.agent_module_globals['os'].statvfs.return_value = MagicMock(f_blocks=1000, f_frsize=1024, f_bavail=500)

        metrics = self.agent.get_system_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('directory_metrics', metrics)
        self.assertEqual(len(metrics['directory_metrics']), 2)
        
        dir1 = metrics['directory_metrics'][0]
        self.assertEqual(dir1['path'], '/test/path1')
        self.assertEqual(dir1['file_count'], 500)
        self.assertEqual(dir1['size_mb'], 100)

        dir2 = metrics['directory_metrics'][1]
        self.assertEqual(dir2['path'], '/test/path2')
        self.assertEqual(dir2['file_count'], 100)
        self.assertEqual(dir2['size_mb'], 50)
