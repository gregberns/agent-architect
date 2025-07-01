import pytest
import sys
import os
from io import StringIO

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_say_hello_function_exists():
    """Test that say_hello function exists"""
    try:
        import say_hello
        assert hasattr(say_hello, 'say_hello'), "say_hello function not found"
    except ImportError:
        pytest.fail("say-hello.py file not found in output directory")

def test_say_hello_output():
    """Test that say_hello function produces correct output"""
    try:
        import say_hello
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Call the function
        say_hello.say_hello()
        
        # Reset stdout
        sys.stdout = sys.__stdout__
        
        # Check output
        output = captured_output.getvalue().strip()
        assert output == "Hello World", f"Expected 'Hello World', got '{output}'"
        
    except ImportError:
        pytest.fail("say-hello.py file not found in output directory")