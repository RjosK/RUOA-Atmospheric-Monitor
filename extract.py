import json

with open('(2) METEO (1).ipynb', encoding='utf-8') as f:
    notebook = json.load(f)

code_cells = []
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        code_cells.append(''.join(cell['source']))

with open('extracted_code.py', 'w', encoding='utf-8') as f:
    f.write('\n\n# ---\n\n'.join(code_cells))
