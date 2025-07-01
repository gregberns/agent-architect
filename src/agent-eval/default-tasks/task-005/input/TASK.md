# Task 005: String Processing

## Objective
Create functions to process and manipulate text strings.

## Requirements
1. Create a function `reverse_string(text)` that returns the reverse of the input string
2. Create a function `is_palindrome(text)` that returns True if the text is a palindrome (ignoring case and spaces)
3. Create a function `count_vowels(text)` that returns the number of vowels (a, e, i, o, u) in the text
4. Create a function `title_case(text)` that returns the text with each word capitalized
5. Create a function `remove_spaces(text)` that returns the text with all spaces removed
6. Handle edge cases like empty strings appropriately
7. Write all functions to `./output/string_processing.py`

## Expected Behavior
```python
print(reverse_string("hello"))           # "olleh"
print(is_palindrome("A man a plan a canal Panama"))  # True
print(count_vowels("Hello World"))       # 3
print(title_case("hello world"))         # "Hello World"
print(remove_spaces("hello world"))      # "helloworld"
```

## Scoring Criteria
- **Compilation (1 point)**: Python script runs without syntax errors
- **Test Validation (1 point)**: All functions work correctly with edge cases