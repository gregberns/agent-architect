import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_function_exists():
    """Test that the required function exists"""
    try:
        import min_cost
        assert hasattr(min_cost, 'min_cost'), "min_cost function not found"
    except ImportError:
        pytest.fail("min_cost.py file not found in output directory")

def test_case_1():
    """Test case 1: assert min_cost([[1, 2, 3], [4, 8, 2], [1, 5, 3]], 2, 2) == 8"""
    import min_cost
    assert min_cost([[1, 2, 3], [4, 8, 2], [1, 5, 3]], 2, 2) == 8

def test_case_2():
    """Test case 2: assert min_cost([[2, 3, 4], [5, 9, 3], [2, 6, 4]], 2, 2) == 12"""
    import min_cost
    assert min_cost([[2, 3, 4], [5, 9, 3], [2, 6, 4]], 2, 2) == 12

def test_case_3():
    """Test case 3: assert min_cost([[3, 4, 5], [6, 10, 4], [3, 7, 5]], 2, 2) == 16"""
    import min_cost
    assert min_cost([[3, 4, 5], [6, 10, 4], [3, 7, 5]], 2, 2) == 16

