import os

def find_encoding_errors(directory):
    """
    Recursively finds Python files with encoding errors in a directory.
    """
    error_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    error_files.append(filepath)
                    print(f"Encoding error in: {filepath}")
    return error_files

if __name__ == "__main__":
    print("Starting encoding check...")
    errors = find_encoding_errors(".")
    if not errors:
        print("No encoding errors found.")
    else:
        print(f"Found {len(errors)} files with encoding errors.")

