import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_functions_exist():
    """Test that all required functions exist"""
    try:
        import string_processing
        assert hasattr(string_processing, 'reverse_string'), "reverse_string function not found"
        assert hasattr(string_processing, 'is_palindrome'), "is_palindrome function not found"
        assert hasattr(string_processing, 'count_vowels'), "count_vowels function not found"
        assert hasattr(string_processing, 'title_case'), "title_case function not found"
        assert hasattr(string_processing, 'remove_spaces'), "remove_spaces function not found"
    except ImportError:
        pytest.fail("string_processing.py file not found in output directory")

def test_reverse_string():
    """Test reverse_string function"""
    import string_processing
    
    assert string_processing.reverse_string("hello") == "olleh"
    assert string_processing.reverse_string("") == ""
    assert string_processing.reverse_string("a") == "a"
    assert string_processing.reverse_string("abc") == "cba"

def test_is_palindrome():
    """Test is_palindrome function"""
    import string_processing
    
    assert string_processing.is_palindrome("A man a plan a canal Panama") == True
    assert string_processing.is_palindrome("racecar") == True
    assert string_processing.is_palindrome("hello") == False
    assert string_processing.is_palindrome("") == True
    assert string_processing.is_palindrome("a") == True

def test_count_vowels():
    """Test count_vowels function"""
    import string_processing
    
    assert string_processing.count_vowels("Hello World") == 3  # e, o, o
    assert string_processing.count_vowels("aeiou") == 5
    assert string_processing.count_vowels("bcdfg") == 0
    assert string_processing.count_vowels("") == 0
    assert string_processing.count_vowels("AEIOU") == 5

def test_title_case():
    """Test title_case function"""
    import string_processing
    
    assert string_processing.title_case("hello world") == "Hello World"
    assert string_processing.title_case("") == ""
    assert string_processing.title_case("a") == "A"
    assert string_processing.title_case("hello") == "Hello"

def test_remove_spaces():
    """Test remove_spaces function"""
    import string_processing
    
    assert string_processing.remove_spaces("hello world") == "helloworld"
    assert string_processing.remove_spaces("") == ""
    assert string_processing.remove_spaces("a b c") == "abc"
    assert string_processing.remove_spaces("nospaces") == "nospaces"