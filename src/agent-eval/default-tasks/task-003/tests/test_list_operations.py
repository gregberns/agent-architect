import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_functions_exist():
    """Test that all required functions exist"""
    try:
        import list_operations
        assert hasattr(list_operations, 'sort_numbers'), "sort_numbers function not found"
        assert hasattr(list_operations, 'find_max'), "find_max function not found"
        assert hasattr(list_operations, 'find_element'), "find_element function not found"
        assert hasattr(list_operations, 'remove_duplicates'), "remove_duplicates function not found"
    except ImportError:
        pytest.fail("list_operations.py file not found in output directory")

def test_sort_numbers():
    """Test sort_numbers function"""
    import list_operations
    
    assert list_operations.sort_numbers([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]
    assert list_operations.sort_numbers([]) == []
    assert list_operations.sort_numbers([5]) == [5]
    assert list_operations.sort_numbers([2, 1]) == [1, 2]

def test_find_max():
    """Test find_max function"""
    import list_operations
    
    assert list_operations.find_max([3, 1, 4, 1, 5]) == 5
    assert list_operations.find_max([1]) == 1
    assert list_operations.find_max([-5, -1, -10]) == -1
    assert list_operations.find_max([]) is None

def test_find_element():
    """Test find_element function"""
    import list_operations
    
    assert list_operations.find_element([3, 1, 4, 1, 5], 4) == 2
    assert list_operations.find_element([3, 1, 4, 1, 5], 1) == 1  # First occurrence
    assert list_operations.find_element([3, 1, 4, 1, 5], 6) == -1
    assert list_operations.find_element([], 1) == -1

def test_remove_duplicates():
    """Test remove_duplicates function"""
    import list_operations
    
    assert list_operations.remove_duplicates([3, 1, 4, 1, 5, 1]) == [3, 1, 4, 5]
    assert list_operations.remove_duplicates([1, 1, 1]) == [1]
    assert list_operations.remove_duplicates([1, 2, 3]) == [1, 2, 3]
    assert list_operations.remove_duplicates([]) == []