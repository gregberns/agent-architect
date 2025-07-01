import pytest
import sys
import os

# Add output directory to path to import the solution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'output'))

def test_calculator_class_exists():
    """Test that Calculator class exists"""
    try:
        import calculator
        assert hasattr(calculator, 'Calculator'), "Calculator class not found"
    except ImportError:
        pytest.fail("calculator.py file not found in output directory")

def test_calculator_methods_exist():
    """Test that all required methods exist"""
    import calculator
    calc = calculator.Calculator()
    
    assert hasattr(calc, 'add'), "add method not found"
    assert hasattr(calc, 'subtract'), "subtract method not found"
    assert hasattr(calc, 'multiply'), "multiply method not found"
    assert hasattr(calc, 'divide'), "divide method not found"

def test_add_operation():
    """Test addition operation"""
    import calculator
    calc = calculator.Calculator()
    
    assert calc.add(5, 3) == 8
    assert calc.add(-2, 7) == 5
    assert calc.add(0, 0) == 0

def test_subtract_operation():
    """Test subtraction operation"""
    import calculator
    calc = calculator.Calculator()
    
    assert calc.subtract(10, 4) == 6
    assert calc.subtract(5, 8) == -3
    assert calc.subtract(0, 0) == 0

def test_multiply_operation():
    """Test multiplication operation"""
    import calculator
    calc = calculator.Calculator()
    
    assert calc.multiply(3, 7) == 21
    assert calc.multiply(-2, 4) == -8
    assert calc.multiply(0, 5) == 0

def test_divide_operation():
    """Test division operation"""
    import calculator
    calc = calculator.Calculator()
    
    assert calc.divide(15, 3) == 5.0
    assert calc.divide(7, 2) == 3.5
    assert calc.divide(-10, 2) == -5.0

def test_divide_by_zero():
    """Test division by zero error handling"""
    import calculator
    calc = calculator.Calculator()
    
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.divide(10, 0)