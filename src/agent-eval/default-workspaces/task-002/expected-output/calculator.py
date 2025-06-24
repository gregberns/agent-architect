class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))        # 8
    print(calc.subtract(10, 4))  # 6
    print(calc.multiply(3, 7))   # 21
    print(calc.divide(15, 3))    # 5.0
    try:
        print(calc.divide(10, 0))
    except ValueError as e:
        print(f"Error: {e}")