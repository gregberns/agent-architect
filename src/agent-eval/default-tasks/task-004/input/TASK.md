# Task 004: File I/O Operations

## Objective
Create functions to read from and write to text files.

## Requirements
1. Create a function `write_file(filename, content)` that writes content to a file
2. Create a function `read_file(filename)` that reads and returns the content of a file
3. Create a function `count_lines(filename)` that returns the number of lines in a file
4. Create a function `count_words(filename)` that returns the total number of words in a file
5. Handle file not found errors gracefully by returning None or appropriate error messages
6. Write all functions to `./output/file_operations.py`

## Expected Behavior
```python
write_file("test.txt", "Hello World\nThis is a test\nThird line")
content = read_file("test.txt")  # Returns the content as string
lines = count_lines("test.txt")  # Returns 3
words = count_words("test.txt")  # Returns 7
```

## Scoring Criteria
- **Compilation (1 point)**: Python script runs without syntax errors
- **Test Validation (1 point)**: All functions work correctly with proper error handling