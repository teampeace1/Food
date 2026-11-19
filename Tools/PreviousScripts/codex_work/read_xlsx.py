import openpyxl
import sys

sys.stdout = open(sys.argv[2], 'w', encoding='utf-8')
book = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
for sheet in book:
    print(f'## {sheet.title} ({sheet.max_row} rows x {sheet.max_column} cols)')
    for row in sheet:
        parts = [f'{cell.coordinate}:{str(cell.value).replace(chr(10), " / ")}' for cell in row if cell.value is not None]
        if parts:
            print(' | '.join(parts))
