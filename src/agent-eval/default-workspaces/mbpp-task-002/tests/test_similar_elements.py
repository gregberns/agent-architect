import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_function_exists():
    """Test that the required function exists"""
    try:
        import similar_elements
        assert hasattr(similar_elements, 'similar_elements'), "similar_elements function not found"
    except ImportError:
        pytest.fail("similar_elements.py file not found in output directory")

def test_case_1():
    """Test case 1: assert similar_elements((3, 4, 5, 6),(5, 7, 4, 10)) == (4, 5)"""
    import similar_elements
    assert similar_elements((3, 4, 5, 6),(5, 7, 4, 10)) == (4, 5)

def test_case_2():
    """Test case 2: assert similar_elements((1, 2, 3, 4),(5, 4, 3, 7)) == (3, 4)"""
    import similar_elements
    assert similar_elements((1, 2, 3, 4),(5, 4, 3, 7)) == (3, 4)

def test_case_3():
    """Test case 3: assert similar_elements((11, 12, 14, 13),(17, 15, 14, 13)) == (13, 14)"""
    import similar_elements
    assert similar_elements((11, 12, 14, 13),(17, 15, 14, 13)) == (13, 14)

