def sort_numbers(numbers):
    """Returns a sorted list of numbers in ascending order."""
    return sorted(numbers)


def find_max(numbers):
    """Returns the maximum value in a list."""
    if not numbers:
        return None  # Return None for empty list
    return max(numbers)


def find_element(numbers, target):
    """Returns the index of target in the list, or -1 if not found."""
    try:
        return numbers.index(target)
    except ValueError:
        return -1


def remove_duplicates(numbers):
    """Returns a new list with duplicates removed, preserving order."""
    seen = set()
    result = []
    for num in numbers:
        if num not in seen:
            seen.add(num)
            result.append(num)
    return result
