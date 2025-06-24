def reverse_string(text):
    """Return the reverse of the input string"""
    if not text:
        return ""
    return text[::-1]

def is_palindrome(text):
    """Check if text is a palindrome (ignoring case and spaces)"""
    if not text:
        return True
    
    # Remove spaces and convert to lowercase
    cleaned = text.replace(" ", "").lower()
    return cleaned == cleaned[::-1]

def count_vowels(text):
    """Count the number of vowels in the text"""
    if not text:
        return 0
    
    vowels = "aeiouAEIOU"
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count

def title_case(text):
    """Return text with each word capitalized"""
    if not text:
        return ""
    return text.title()

def remove_spaces(text):
    """Return text with all spaces removed"""
    if not text:
        return ""
    return text.replace(" ", "")

if __name__ == "__main__":
    print(reverse_string("hello"))                              # "olleh"
    print(is_palindrome("A man a plan a canal Panama"))         # True
    print(count_vowels("Hello World"))                          # 3
    print(title_case("hello world"))                            # "Hello World"
    print(remove_spaces("hello world"))                         # "helloworld"