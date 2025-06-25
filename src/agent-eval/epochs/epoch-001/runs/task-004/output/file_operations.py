def write_file(filename, content):
    try:
        with open(filename, 'w') as file:
            file.write(content)
    except IOError as e:
        return f"Error writing to file {filename}: {e}"


def read_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return None
    except IOError as e:
        return f"Error reading file {filename}: {e}"


def count_lines(filename):
    content = read_file(filename)
    if content is None:
        return None
    return len(content.splitlines())


def count_words(filename):
    content = read_file(filename)
    if content is None:
        return None
    words = content.split()
    return len(words)