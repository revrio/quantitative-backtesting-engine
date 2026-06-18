import os
import re
import tokenize
import io

def remove_python_comments(source_code):
    io_obj = io.StringIO(source_code)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    
    try:
        tokens = tokenize.generate_tokens(io_obj.readline)
        for tok in tokens:
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            ltext = tok[4]
            
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            
            if token_type == tokenize.COMMENT:
                pass
            else:
                out += token_string
                
            last_lineno = end_line
            last_col = end_col
        # remove blank lines created by comment removal
        return "\n".join([line for line in out.splitlines() if line.strip() != ""])
    except tokenize.TokenError:
        return source_code

def remove_js_comments(source_code):
    # Remove single line comments //
    source_code = re.sub(r'//.*', '', source_code)
    # Remove block comments /* */
    source_code = re.sub(r'/\*[\s\S]*?\*/', '', source_code)
    # Remove JSX comments {/* */}
    source_code = re.sub(r'\{\s*/\*[\s\S]*?\*/\s*\}', '', source_code)
    # remove blank lines
    return "\n".join([line for line in source_code.splitlines() if line.strip() != ""])

def process_directory(path):
    for root, dirs, files in os.walk(path):
        if 'node_modules' in root or '.git' in root or 'archive' in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.py'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content = remove_python_comments(content)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Cleaned {filepath}")
            elif file.endswith(('.js', '.jsx')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content = remove_js_comments(content)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Cleaned {filepath}")

if __name__ == "__main__":
    process_directory('backend')
    process_directory('frontend/src')
