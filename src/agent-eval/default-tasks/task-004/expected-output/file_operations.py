def write_file(filename, content):
    """Write content to a file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

def read_file(filename):
    """Read and return the content of a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def count_lines(filename):
    """Count the number of lines in a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except FileNotFoundError:
        return 0
    except Exception as e:
        print(f"Error counting lines: {e}")
        return 0

def count_words(filename):
    """Count the total number of words in a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            words = content.split()
            return len(words)
    except FileNotFoundError:
        return 0
    except Exception as e:
        print(f"Error counting words: {e}")
        return 0

if __name__ == "__main__":
    # Example usage
    test_content = "Hello World\nThis is a test\nThird line"
    
    write_file("test.txt", test_content)
    content = read_file("test.txt")
    print(f"Content: {repr(content)}")
    
    lines = count_lines("test.txt")
    print(f"Lines: {lines}")
    
    words = count_words("test.txt")
    print(f"Words: {words}")
    
    # Clean up
    import os
    if os.path.exists("test.txt"):
        os.remove("test.txt")