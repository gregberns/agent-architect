def reverse_string(text):
    return text[::-1]

def is_palindrome(text):
    cleaned_text = ''.join(char.lower() for char in text if char.isalnum())
    return cleaned_text == cleaned_text[::-1]

def count_vowels(text):
    vowels = 'aeiouAEIOU'
    return sum(1 for char in text if char in vowels)

def title_case(text):
    return text.title()

def remove_spaces(text):
    return text.replace(' ', '')