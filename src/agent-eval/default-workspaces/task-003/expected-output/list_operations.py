def sort_numbers(numbers):
    """Sort a list of numbers in ascending order"""
    if not numbers:
        return []
    return sorted(numbers)

def find_max(numbers):
    """Find the maximum value in a list"""
    if not numbers:
        return None
    return max(numbers)

def find_element(numbers, target):
    """Find the index of target in the list, return -1 if not found"""
    try:
        return numbers.index(target)
    except ValueError:
        return -1

def remove_duplicates(numbers):
    """Remove duplicates from list while preserving order"""
    if not numbers:
        return []
    
    seen = set()
    result = []
    for num in numbers:
        if num not in seen:
            seen.add(num)
            result.append(num)
    return result

if __name__ == "__main__":
    print(sort_numbers([3, 1, 4, 1, 5]))           # [1, 1, 3, 4, 5]
    print(find_max([3, 1, 4, 1, 5]))              # 5
    print(find_element([3, 1, 4, 1, 5], 4))       # 2
    print(find_element([3, 1, 4, 1, 5], 6))       # -1
    print(remove_duplicates([3, 1, 4, 1, 5, 1]))  # [3, 1, 4, 5]