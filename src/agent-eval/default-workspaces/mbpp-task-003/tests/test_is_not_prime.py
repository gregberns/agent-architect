import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_function_exists():
    """Test that the required function exists"""
    try:
        import is_not_prime
        assert hasattr(is_not_prime, 'is_not_prime'), "is_not_prime function not found"
    except ImportError:
        pytest.fail("is_not_prime.py file not found in output directory")

def test_case_1():
    """Test case 1: assert is_not_prime(2) == False"""
    import is_not_prime
    assert is_not_prime(2) == False

def test_case_2():
    """Test case 2: assert is_not_prime(10) == True"""
    import is_not_prime
    assert is_not_prime(10) == True

def test_case_3():
    """Test case 3: assert is_not_prime(35) == True"""
    import is_not_prime
    assert is_not_prime(35) == True

