import pytest
import sys
import os
import tempfile

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_functions_exist():
    """Test that all required functions exist"""
    try:
        import file_operations
        assert hasattr(file_operations, 'write_file'), "write_file function not found"
        assert hasattr(file_operations, 'read_file'), "read_file function not found"
        assert hasattr(file_operations, 'count_lines'), "count_lines function not found"
        assert hasattr(file_operations, 'count_words'), "count_words function not found"
    except ImportError:
        pytest.fail("file_operations.py file not found in output directory")

def test_write_and_read_file():
    """Test write_file and read_file functions"""
    import file_operations
    
    # Use temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    try:
        test_content = "Hello World\nThis is a test"
        
        # Test write
        result = file_operations.write_file(temp_filename, test_content)
        assert result is True or result is None  # Some implementations might not return boolean
        
        # Test read
        content = file_operations.read_file(temp_filename)
        assert content == test_content
        
    finally:
        # Clean up
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def test_count_lines():
    """Test count_lines function"""
    import file_operations
    
    # Use temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    try:
        test_content = "Line 1\nLine 2\nLine 3"
        
        file_operations.write_file(temp_filename, test_content)
        lines = file_operations.count_lines(temp_filename)
        assert lines == 3
        
    finally:
        # Clean up
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def test_count_words():
    """Test count_words function"""
    import file_operations
    
    # Use temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_filename = temp_file.name
    
    try:
        test_content = "Hello World\nThis is a test\nThird line"
        
        file_operations.write_file(temp_filename, test_content)
        words = file_operations.count_words(temp_filename)
        assert words == 8  # Hello, World, This, is, a, test, Third, line
        
    finally:
        # Clean up
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

def test_file_not_found():
    """Test error handling for non-existent files"""
    import file_operations
    
    non_existent_file = "this_file_does_not_exist.txt"
    
    # read_file should return None for non-existent file
    content = file_operations.read_file(non_existent_file)
    assert content is None
    
    # count_lines should return 0 for non-existent file
    lines = file_operations.count_lines(non_existent_file)
    assert lines is None
    
    # count_words should return 0 for non-existent file
    words = file_operations.count_words(non_existent_file)
    assert words is None
