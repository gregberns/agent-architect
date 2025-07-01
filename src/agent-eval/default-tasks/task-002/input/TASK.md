# Task 002: Basic Calculator

## Objective
Create a simple calculator class with basic arithmetic operations.

## Requirements
1. Create a class named `Calculator` with the following methods:
   - `add(a, b)` - returns the sum of a and b
   - `subtract(a, b)` - returns the difference of a and b
   - `multiply(a, b)` - returns the product of a and b
   - `divide(a, b)` - returns the quotient of a and b (handle division by zero)
2. Include error handling for division by zero (raise ValueError with message "Cannot divide by zero")
3. Write the class to `./output/calculator.py`

## Expected Behavior
```python
calc = Calculator()
print(calc.add(5, 3))        # 8
print(calc.subtract(10, 4))  # 6
print(calc.multiply(3, 7))   # 21
print(calc.divide(15, 3))    # 5.0
print(calc.divide(10, 0))    # ValueError: Cannot divide by zero
```

## Scoring Criteria
- **Compilation (1 point)**: Python script runs without syntax errors
- **Test Validation (1 point)**: All methods work correctly with proper error handling