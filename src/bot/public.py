
def get_prompt_from_file(filename: str):
    with open(f'public/{filename}', 'r', encoding='utf-8') as file:
        text = file.read()
    return text