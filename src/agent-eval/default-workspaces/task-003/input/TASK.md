# Task 003: List Sorting and Searching

## Objective
Create functions to sort and search through lists of data.

## Requirements
1. Create a function `sort_numbers(numbers)` that returns a sorted list of numbers in ascending order
2. Create a function `find_max(numbers)` that returns the maximum value in a list
3. Create a function `find_element(numbers, target)` that returns the index of target in the list, or -1 if not found
4. Create a function `remove_duplicates(numbers)` that returns a new list with duplicates removed, preserving order
5. Handle edge cases like empty lists appropriately
6. Write all functions to `./output/list_operations.py`

## Expected Behavior
```python
print(sort_numbers([3, 1, 4, 1, 5]))           # [1, 1, 3, 4, 5]
print(find_max([3, 1, 4, 1, 5]))              # 5
print(find_element([3, 1, 4, 1, 5], 4))       # 2
print(find_element([3, 1, 4, 1, 5], 6))       # -1
print(remove_duplicates([3, 1, 4, 1, 5, 1]))  # [3, 1, 4, 5]
```

## Scoring Criteria
- **Compilation (1 point)**: Python script runs without syntax errors
- **Test Validation (1 point)**: All functions work correctly with edge cases