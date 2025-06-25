def reverse_string(text):
    """Return the reverse of the input string.

    Args:
        text (str): The input string to reverse.

    Returns:
        str: The reversed string.
    """
    return text[::-1]


def is_palindrome(text):
    """Check if the input text is a palindrome (ignoring case and spaces).

    Args:
        text (str): The input string to check.

    Returns:
        bool: True if the text is a palindrome, False otherwise.
    """
    # Remove spaces and convert to lowercase
    cleaned_text = ''.join(char.lower() for char in text if char.isalnum())
    return cleaned_text == cleaned_text[::-1]


def count_vowels(text):
    """Count the number of vowels (a, e, i, o, u) in the text.

    Args:
        text (str): The input string to search.

    Returns:
        int: The number of vowels in the text.
    """
    vowels = 'aeiouAEIOU'
    return sum(1 for char in text if char in vowels)


def title_case(text):
    """Return the text with each word capitalized.

    Args:
        text (str): The input string to format.

    Returns:
        str: The text with each word capitalized.
    """
    return ' '.join(word.capitalize() for word in text.split())


def remove_spaces(text):
    """Return the text with all spaces removed.

    Args:
        text (str): The input string to process.

    Returns:
        str: The text with all spaces removed.
    """
    return text.replace(' ', '')