#!/usr/bin/env python3
"""
Test file organization and path handling after reorganization.
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase

# Add orchestrator directory to path
test_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(test_dir / "orchestrator"))

from config_simple import OrchestratorConfig, RuntimePathsConfig

class TestFileOrganization(TestCase):
    """Test file organization and runtime path configuration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = OrchestratorConfig.default()
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_runtime_paths_config(self):
        """Test runtime paths configuration"""
        runtime_config = RuntimePathsConfig()
        
        # Test default paths
        self.assertEqual(runtime_config.runtime_dir, "runtime")
        self.assertEqual(runtime_config.logs_dir, "runtime/logs")
        self.assertEqual(runtime_config.state_dir, "runtime/state")
        self.assertEqual(runtime_config.temp_dir, "runtime/temp")
    
    def test_runtime_paths_absolute_resolution(self):
        """Test absolute path resolution"""
        runtime_config = RuntimePathsConfig()
        paths = runtime_config.get_absolute_paths(self.test_dir)
        
        # Check all paths are absolute and under test directory
        self.assertTrue(paths['runtime'].is_absolute())
        self.assertTrue(paths['logs'].is_absolute())
        self.assertTrue(paths['state'].is_absolute())
        self.assertTrue(paths['temp'].is_absolute())
        
        # Check paths are under test directory
        self.assertTrue(str(paths['runtime']).startswith(str(self.test_dir)))
        self.assertTrue(str(paths['logs']).startswith(str(self.test_dir)))
        self.assertTrue(str(paths['state']).startswith(str(self.test_dir)))
        self.assertTrue(str(paths['temp']).startswith(str(self.test_dir)))
    
    def test_orchestrator_config_runtime_paths(self):
        """Test orchestrator configuration includes runtime paths"""
        config = OrchestratorConfig.default()
        
        # Test runtime paths exist in config
        self.assertIsInstance(config.runtime_paths, RuntimePathsConfig)
        
        # Test get_runtime_paths method
        paths = config.get_runtime_paths(self.test_dir)
        self.assertIn('runtime', paths)
        self.assertIn('logs', paths)
        self.assertIn('state', paths)
        self.assertIn('temp', paths)
    
    def test_directory_creation(self):
        """Test that runtime directories are created correctly"""
        config = OrchestratorConfig.default()
        paths = config.get_runtime_paths(self.test_dir)
        
        # Create directories
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Verify directories exist
        for path in paths.values():
            self.assertTrue(path.exists())
            self.assertTrue(path.is_dir())
    
    def test_job_queue_path_resolution(self):
        """Test job queue file path resolution"""
        config = OrchestratorConfig.default()
        paths = config.get_runtime_paths(self.test_dir)
        
        # Job queue should be in state directory
        expected_job_queue_path = paths['state'] / config.job_queue_file
        self.assertTrue(str(expected_job_queue_path).endswith('job_queue.json'))
        self.assertTrue('runtime/state' in str(expected_job_queue_path))
    
    def test_worker_log_paths(self):
        """Test worker log file paths"""
        config = OrchestratorConfig.default()
        paths = config.get_runtime_paths(self.test_dir)
        
        workers_log_dir = paths['logs'] / 'workers'
        
        # Test worker log file paths
        for i in range(3):
            worker_id = f"task-worker-{i+1}"
            worker_log_file = workers_log_dir / f"worker-{worker_id}.log"
            
            # Path should be under logs/workers
            self.assertTrue('runtime/logs/workers' in str(worker_log_file))
            self.assertTrue(str(worker_log_file).endswith('.log'))
    
    def test_config_serialization(self):
        """Test configuration can be serialized and deserialized"""
        config = OrchestratorConfig.default()
        
        # Save to temporary file
        config_file = self.test_dir / "test_config.json"
        config.save_json(str(config_file))
        
        # Verify file was created
        self.assertTrue(config_file.exists())
        
        # Load configuration back
        loaded_config = OrchestratorConfig.from_json(str(config_file))
        
        # Verify configuration matches
        self.assertEqual(config.runtime_paths.runtime_dir, loaded_config.runtime_paths.runtime_dir)
        self.assertEqual(config.runtime_paths.logs_dir, loaded_config.runtime_paths.logs_dir)
        self.assertEqual(config.runtime_paths.state_dir, loaded_config.runtime_paths.state_dir)
        self.assertEqual(config.runtime_paths.temp_dir, loaded_config.runtime_paths.temp_dir)

def run_file_organization_tests():
    """Run file organization tests and return results"""
    import unittest
    from utilities import TestResults
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFileOrganization)
    
    # Run tests
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    execution_time = time.time() - start_time
    
    # Convert to our TestResults format
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    failures = []
    
    for test, traceback in result.failures + result.errors:
        error_line = traceback.split('\n')[-2] if traceback else 'Unknown error'
        failures.append(f"{test}: {error_line}")
    
    return TestResults(passed, failed, failures, execution_time)

if __name__ == '__main__':
    import unittest
    import time
    unittest.main()