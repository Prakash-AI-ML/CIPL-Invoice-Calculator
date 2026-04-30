import copy
import pandas as pd
import re

def create_thai_data(data):
    original_data, final_data = [], []
    for key, ci in data.items():
        ref =ci['reference_no']
        ref_date = ci['reference_date']
        idx = 1
        for item in  ci['items']:
            if item['description'].lower().startswith('row') and item['fob_price_sgd'] == '' and item['fob_amount_sgd'] == '':
                continue
            dic = {'REF NO': ref, 'REF DATE': ref_date,
                        'ITEM NO.': idx, #item['item'],
                        'DESCRIPTION': item['description'],
                        'SERIAL NO.': item['gpn'],
                        'UOM': item['uom'],
                        'COO': item['country_of_origin'],
                        'QUANTITY': int(item['quantity']),
                        'UNIT PRICE': float(item['fob_price_sgd'].replace('$', '').replace(',', '')),
                        'AMOUNT': float(item['fob_amount_sgd'].replace('$', '').replace(',', '')),
            }
            if 'ori' in key.lower():
                original_data.append(dic)
            else:
                final_data.append(dic)
            idx +=1
    original_data.sort(key=lambda x: x['REF NO'])
    final_data.sort(key=lambda x: x['REF NO'])
    ref_nos = [item['REF NO'] for item in original_data]
    return insert_elements(original_data), insert_elements(final_data), f'{min(ref_nos)}-{max(ref_nos)}'

def insert_elements(lst):
    result = []
    new_element = { 'REF NO': "",
                    'REF DATE': '',
                    'ITEM NO.': '',
                    'DESCRIPTION': '',
                    'SERIAL NO.': '',
                    'UOM': '',
                    'COO': '',
                    'QUANTITY': '',
                    'UNIT PRICE': '',
                    'AMOUNT': '',
        }
    for i, val in enumerate(lst):
        result.append(val)
        
        # After 3rd element OR every 6 elements after that
        if i == 2 or (i > 2 and (i - 2) % 6 == 0):
            result.append(new_element)
    
    return result


def create_thai_sheet(original, final, excel_file = "THAI_DOC_SHEET.xlsx"):

    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        original.to_excel(writer, index=False, header=False, startrow=1, sheet_name='ORIGINAL')
        writer = thai_sheet_writer(writer, original, 'ORIGINAL')
        
        final.to_excel(writer, index=False, header=False, startrow=1, sheet_name='FINAL')
        # Tally sheet financial
        writer = thai_sheet_writer(writer, final, 'FINAL')
        


def thai_sheet_writer(writer, df, sheet_name = 'ORIGINAL'):
    workbook  = writer.book
    worksheet = writer.sheets[sheet_name]
 
    text_format = workbook.add_format({
        'align': 'center',
        'border': 1,
        'valign': 'vcenter'
    })
    
    num_format = workbook.add_format({
        'num_format': '###,##0.00',
        'align': 'center',
        'border': 1,
        'valign': 'vcenter'
    })

    num_format1 = workbook.add_format({
        'num_format': '###0',
        'align': 'center',
        'border': 1,
        'valign': 'vcenter'
    })
    # -------------------------
    # Formats
    # -------------------------
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': True 
    })


    bold_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'border': 1,
        'valign': 'vcenter'
    })

    
    # -------------------------
    # Column Width
    # -------------------------
    worksheet.set_column('A:C', width=9, cell_format=text_format)
    worksheet.set_column('D:D', width=100, cell_format=text_format)
    worksheet.set_column('E:G', width=9, cell_format=text_format)
    worksheet.set_column('I:J', width=15, cell_format=num_format)
    worksheet.set_column('H:H', width=9, cell_format=num_format1)
    worksheet.set_column('K:O', width=17, cell_format=num_format)
    # worksheet.set_column('H:H', width=9, cell_format=num_format1)
    # worksheet.set_column('C:C', width=44, cell_format= text_format)
    # worksheet.set_column('D:F', width=14, cell_format=num_format)
    header_ = ['THB', '10%', 'THB+10%', '7%', 'PAGE TOTAL']
    worksheet.write(f'Q1', 'THB VALUE:')
    worksheet.write(f'Q2', 24.967)
    length = len(df)
    for idx in range(5):
        worksheet.write(f'{chr(75+idx)}1', header_[idx])
        if idx < 4:
            page_total = False
            page = 0
            prev = 2
            for row in range(length + 1):
                if row == 4 or page_total:
                    # worksheet =  write_page_total(worksheet, row, prev)
                    for i in range(1, 6):
                        worksheet.write_formula(row, 8 +i, f'=SUM({chr(73+i)}{prev}:{chr(73+i)}{row})')
                    worksheet.write_formula(row, 14, f'=L{row +1} + N{row +1}')
                    worksheet.write_formula(row, 7, f'=SUM(H{prev}:H{row})')
                    page_total = False 
                    page = 0
                    prev = row +1
                    continue
                if idx ==0:
                    worksheet.write_formula(row, 10, f'=ROUND(J{row +1} * Q2, 2)')
                elif idx ==1:
                    worksheet.write_formula(row, 11, f'=ROUND(K{row +1} * 10%, 2)')
                elif idx ==2:
                    worksheet.write_formula(row, 12, f'=ROUND(K{row +1} + L{row +1}, 2 )')
                elif idx ==3:
                    worksheet.write_formula(row, 13, f'=ROUND(M{row +1} * 7%, 2)')
                page += 1
                if page == 6:
                    page_total = True
    # -------------------------
    # Bold Last Row
    # -------------------------
    # last_row = len(df)

    # for col_num in range(len(df.columns)):
    #     worksheet.write(last_row, col_num, df.iloc[-1, col_num], bold_format)
    
    if prev-1 != df.shape[0]:
        for i in range(1, 6):
            worksheet.write_formula(row +1, 8 +i, f'=SUM({chr(73+i)}{prev}:{chr(73+i)}{row +1})')
        worksheet.write_formula(row +1, 14, f'=L{row +2} + N{row +2}')
        worksheet.write_formula(row +1, 7, f'=SUM(H{prev}:H{row+1})')
    header = list(df.columns)
    header.extend(header_)
    # # -------------------------
    # Add Table (optional style)
    # -------------------------
    table_style_len = len(df)+1 if prev -1 != df.shape[0] else len(df)
    worksheet.add_table(0, 0, table_style_len, len(header)-1, {
        'columns':  [
            {'header': col, 'header_format': header_format}
            for col in header #df.columns
        ],
        'style': 'Table Style Medium 23'
    })
    return writer
