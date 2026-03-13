import copy
import pandas as pd
import re
from datetime import datetime
import pdfplumber


def regex(raw_text):
    lines = raw_text.split("\n")

    result = []
    current = lines[0]

    for line in lines[1:]:
        # if re.match(r'^\d|^Cooling|^Kit', line):  # new row if line starts with digit
        if re.match(r'^(MDA\d+|\d|Support|Cooling|Kit)', line):
            result.append(current)
            current = line
        else:
            current += " " + line  # keep newline
    result.append(current)

    return result



def calculate_cbm(lines):
    total_cbm = 0.0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        data1 = line.split('/')
        data = {'quantity': data1[0], 'area': data1[1].replace('cm', '').replace('-', '').strip(), 'weight': data1[-1]}
        qty_match = re.match(r"^\s*(\d+)", data['quantity'])
        if not qty_match:
            continue

        quantity = int(qty_match.group(1))
        data['quantity'] = quantity
        length, width, height = [int(i.strip()) for i in data['area'].split('x')]
        if 'cm' in line:
            
            # 4️⃣ Convert to CBM (cm³ → m³)
            cbm_per_item = (length * width * height) / 1_000_000
            total_cbm += cbm_per_item * quantity
            
            print(data, cbm_per_item * quantity, total_cbm)

    return round(total_cbm, 2)


def get_final_recalculate_data(data, divided_by):
    total_amount = 0.0
    
    for row in data:
        # Skip rows with empty FOB price
        fob_price = row.get('FOB PRICE SGD', '')
        quantity = row.get('QUANTITY', '')
        if type(fob_price) != float:
            if not fob_price or fob_price.strip() == '':
                continue
        
        # Clean and convert fob_price to float
        if type(fob_price) != float:
            fob_price = float(fob_price.replace('$', '').replace(',', '').strip())
        quantity = float(quantity) if quantity else 0
        
        # Recalculate FOB price and amount
        new_fob_price = round(fob_price / divided_by, 2)
        new_fob_amount = round(new_fob_price * quantity, 2)
        
        # Update the row with formatted values
        row['FOB PRICE SGD'] = new_fob_price
        row['FOB AMOUNT SGD'] = new_fob_amount
        
        total_amount += new_fob_amount

    return data, round(total_amount, 2)

def get_line_count(data, DESCRIPTIONS_DATA):
    count = 0
    for item in data['items']:
        if item['description'].startswith('ROW'):
            count +=2
        if item['description'].startswith('MDA'):
            count +=2
        # elif item['description'] in DESCRIPTION_LINE_MAPPING:
        #     count += DESCRIPTION_LINE_MAPPING[item['description']]
        elif item['description'] in DESCRIPTIONS_DATA['original']:
            idx = DESCRIPTIONS_DATA['original'].index(item['description'])
            count += DESCRIPTIONS_DATA['lines'][idx] + 1
        elif item['gpn'] in DESCRIPTIONS_DATA['item_id']:
            idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
            count += DESCRIPTIONS_DATA['lines'][idx] + 1
        else:
            count +=3
    if data['packing_details']:
        if data['packing_details']['details']:
            count += len(data['packing_details']['details']) + 2 # 1 for header and another for \n
        if data['packing_details']['total']:
            count += len(data['packing_details']['total']) + 1 # 1 for \n line
        if data['packing_details']['shipping']:
            count += len(data['packing_details']['shipping']) + 2 # 1 for header and another for \n

    data['packing_details']['present_lines'] = count

    return data

def date_conversion(date_str):
    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
    formatted = date_obj.strftime('%d-%b-%y')
    return formatted


def extract_text_from_bbox(words, bbox):
    x0, top, x1, bottom = bbox

    extracted_words = [
        w["text"]
        for w in words
        if (w["x0"] >= x0 and w["x1"] <= x1 and
            w["top"] >= top and w["bottom"] <= bottom)
    ]

    return " ".join(extracted_words)

def find_port_data(words):
    """
    Find bounding boxes for 'Port of Loading' and 'Port of Discharge'
    from pdf word tokens.
    
    Returns:
        dict with bbox = (x0, top, x1, bottom)
    """
    
    results = {}
    result = {}

    for i in range(len(words) - 2):
        w1 = words[i]["text"].lower()
        w2 = words[i+1]["text"].lower()
        w3 = words[i+2]["text"].lower().replace(":", "")

        # Port of Loading
        if w1 == "port" and w2 == "of" and w3 == "loading":
            x0 = words[i]["x0"]
            x1 = words[i+2]["x1"]
            top = min(words[i]["top"], words[i+1]["top"], words[i+2]["top"])
            bottom = max(words[i]["bottom"], words[i+1]["bottom"], words[i+2]["bottom"])

            results["port_of_loading"] = (x0, top, x1, bottom)
            

        # Port of Discharge
        if w1 == "port" and w2 == "of" and w3 == "discharge":
            x0 = words[i]["x0"]
            x1 = words[i+2]["x1"]
            top = min(words[i]["top"], words[i+1]["top"], words[i+2]["top"])
            bottom = max(words[i]["bottom"], words[i+1]["bottom"], words[i+2]["bottom"])

            results["port_of_discharge"] = (x0, top, x1, bottom)
    height = (results['port_of_loading'][3] - results['port_of_loading'][1]) *4
    results["port_of_loading_"] = (results['port_of_loading'][0], results['port_of_loading'][3], results['port_of_discharge'][0], results['port_of_loading'][3] + height)
    width = results['port_of_loading_'][2] - results['port_of_loading_'][0]
    results['port_of_discharge_'] = (results['port_of_discharge'][0], results['port_of_discharge'][3], results['port_of_discharge'][0] + width, results['port_of_discharge'][3] + height)
    result["port_of_loading"] = extract_text_from_bbox(
            words, results["port_of_loading_"]
        )
    result["port_of_discharge"] = extract_text_from_bbox(
            words, results["port_of_discharge_"]
        )

    return results, result



def get_data(table, words):
    
    region, text = find_port_data(words)

    m = re.search(r'Reference\s*No:\s*([A-Za-z0-9\-]+)\s*Date:\s*([\d/]+)', table[1][3], re.IGNORECASE)

    if m:
        reference_no = m.group(1)
        reference_no_date = m.group(2)
    m1= re.search(r'PO\s*no:\s*([A-Za-z0-9\-]+)\s*Date:\s*([\d/]+)', table[3][3], re.IGNORECASE)

    if m1:
        po_no = m1.group(1)
        po_no_date_ = m1.group(2)

   

    shipper_ = re.split(r'shipper:\n', table[0][0], flags=re.IGNORECASE)[-1].split('\n')
    importer_ = re.split(r'Importer of Record:\n', table[2][0], flags=re.IGNORECASE)[-1].split('\n')
    ship_to_ = re.split(r'Ship to:\n', table[4][0], flags=re.IGNORECASE)[-1].split('\n')
    port_loading_ = text['port_of_loading']
    port_discharge = text['port_of_discharge']
    reference_no_ = reference_no if m else None
    reference_no_date = date_conversion(reference_no_date)
    po_no_ = po_no if m1 else None
    po_no_date = date_conversion(po_no_date_)
    
    
    return shipper_, importer_, ship_to_, reference_no_, reference_no_date, port_loading_, port_discharge, po_no_, po_no_date



def clean_dataframe(dic):
    new_data = []
    for data in dic:
        # print(data.get('CONTRY OF ORIGIN'), data['COUNTRY OF ORIGIN'], data)
        gpn = data.get('GPN', '')
        # --- normalize GPN ---
        if pd.isna(gpn) or str(gpn).strip().lower() == 'nan':
            ref = ''
        else:
            ref = str(gpn).strip()
        # ref = str(gpn).strip() if gpn is not None else ''
       
        item = data.get('ITEM')
        desc = (data.get('DESCRIPTION') or '')

        country = data.get('COUNTRY OF ORIGIN')
        # print(data, country)
        uom = data.get('UOM')
        qty = data.get('QUANTITY')
        fob_price = data.get('FOB PRICE SGD')
        fob_amount = data.get('FOB AMOUNT SGD')
        if 'FOB PRICE SGD' not in data:
            fob_price = data.get('PRICE SGD')
            fob_amount = data.get('AMOUNT SGD')

        if re.fullmatch(r'ROW\s*\d+', desc):
            pass

        if pd.isnull(gpn) and pd.isnull(ref) or '' == ref  and desc and new_data:
            
            new_data[-1]['description'] += " " + desc
        
        elif pd.isnull(gpn) and ref and new_data:
            if desc:
                new_data[-1]['description'] += " " + desc
            # new_data[-1]['GPN'] += " \n * " + ref
                    
        else:
            data_ = {
            "item": "" if pd.isnull(item) else str(item), 
            'description': "" if pd.isnull(desc) else desc,
            'gpn': "" if pd.isnull(ref) else None if pd.isna(ref) else ref,
            'uom': "" if pd.isnull(uom) else uom,
            'country_of_origin': "" if pd.isnull(country) else country, 
            'quantity': "" if pd.isnull(qty) else f"{qty}",
            'fob_price_sgd': "" if fob_price is not None and '' == fob_price else "$" + (" " * (9 +2 -len(f"{fob_price:,.{2}f}"))) + f"{fob_price:,.{2}f}",
            'fob_amount_sgd': "" if fob_amount is not None and '' == fob_amount else "$" + (" " * (13 + 5 -len(f"{fob_amount:,.{2}f}"))) + f"{fob_amount:,.{2}f}",
            'description_modified': 0
        }
            new_data.append(data_)
    return new_data


def get_table_items(table, table_name= 'packing_details', divided_by = None):
    if table_name != 'packing_details':
        items = []
        total_amount = 0
        descriptions = regex(table[7][2])
        idx = 0
        for desc in descriptions:
            if re.match(r'^(MDA\d+|ROW\d+|MDA \d+|ROW \d+)', desc):
                item = {'ITEM':'',
                    'GPN': '',
                    'DESCRIPTION': desc,
                    'COUNTRY OF ORIGIN':'',
                    'UOM': '',
                    'QUANTITY':'',
                    'FOB PRICE SGD':'',
                    'FOB AMOUNT SGD':''}

            else:
                fob_price = '' if table[7][6] == '' else table[7][6].replace('$ ', "").replace(',', "").strip().split('\n')[idx]
                fob_amount = '' if table[7][6] == '' else table[7][7].replace('$ ', "").replace(',', "").strip().split('\n')[idx]
                item = {'ITEM':table[7][0].split('\n')[idx],
                        'GPN': table[7][1].split('\n')[idx],
                        'DESCRIPTION': desc,
                        'COUNTRY OF ORIGIN':table[7][3].split('\n')[idx],
                        'UOM': table[7][4].split('\n')[idx],
                        'QUANTITY':table[7][5].split('\n')[idx],
                        # 'FOB PRICE SGD':float(table[7][6].replace('$ ', "").replace(',', "").strip().split('\n')[idx]),
                        # 'FOB AMOUNT SGD':float(table[7][7].replace('$ ', "").replace(',', "").strip().split('\n')[idx])
                        'FOB PRICE SGD':float(fob_price) if fob_price !=None and fob_price != '' else '',
                        'FOB AMOUNT SGD':float(fob_amount) if fob_amount !=None and fob_amount != '' else ''
                        }
                idx +=1
            items.append(item)
        
        if divided_by:
            print(divided_by)
            items, total_amount = get_final_recalculate_data(items, divided_by)
         
            
    return clean_dataframe(items), total_amount

def get_packing_details(table, lines):
    pcks = re.split(r'packing details:\n', table[7][2], flags=re.IGNORECASE)[-1].split('\n')
    m = re.search(r'Reference\s*No:\s*([A-Za-z0-9\-]+)\s*Date:\s*([\d/]+)', table[1][3], re.IGNORECASE)

    if m:
        reference_no = m.group(1)
        date = m.group(2)

    total_packages = None
    gross_weight = None

    for line in lines:
        m1 = re.search(r'TOTAL\s+PACKAGES:\s*(\d+)', line, re.IGNORECASE)
        if m1:
            total_pcks = m1.group(1)

        m2 = re.search(r'GROSS\s+WEIGHT:\s*([\d,\.]+\s*\w+)', line, re.IGNORECASE)
        if m2:
            total_w = m2.group(1)


    output = []
    gross_w = 0
    if pcks:
        for item in pcks:
            # extract number of pieces (int)
            if item.split()[0].isnumeric():
                qty_match = re.match(r'(\d+)', item)
                qty = int(qty_match.group(1)) if qty_match else 1

                # extract weight (int)
                weight_match = re.search(r'(\d+)\s*kgs', item, re.IGNORECASE)
                weight = int(weight_match.group(1)) if weight_match else 0

                total_weight = qty * weight
                gross_w += total_weight
                # ensure "each" format in string
                base = item.strip()
                if 'each' not in base.lower():
                    base = base.replace('kgs', 'kgs each')

                output.append(f"{base} = {total_weight:,} KGs")
    total_w =total_w.replace('kgs', '').strip()
    
    return pcks, output, total_pcks, total_w, gross_w, total_w == f'{gross_w:,}'

def analysis_pl(page,  divided_by = None):
    table = page.extract_table()
    words = page.extract_words()
    lines = [line['text'] for line  in page.extract_text_lines()]

    shipper, importer_of_record, ship_to, reference_no, reference_date, port_loading, port_discharge, po_no, po_no_date = get_data(table= table, words= words)
    original_pcks, modified_pcks, total_pcks, total_w, gross_w, is_total_weight_verfy = get_packing_details(table, lines)
    cbm = calculate_cbm(original_pcks)
    # original_items, total_amount = get_table_items(table, table_name = 'invoice', divided_by = divided_by)
    # modified_items = copy.deepcopy(original_items)
    # total_idx = df1[df1.iloc[:, 6].astype(str).str.contains('total', case=False, na=False)].index[0]
    importer_of_record[0] = f"CONSIGNEE:\n{importer_of_record[0]}"
    total_w = f'{int(total_w.replace(',', '')):,}'

    # if divided_by == None:
    #     total = float(table[8][-1].replace('$', '').replace(',', '').strip())
    # else:
    #     total = total_amount


    # for item in modified_items:
    #     if item['description'] in DESCRIPTION_MAPPING:
    #         item['description'] = DESCRIPTION_MAPPING[item['description']]
    
    data = dict(
                shipper = shipper,
                importer_of_record = importer_of_record,
                ship_to = ship_to,
                invoice_type = table[0][3],
                reference_no = reference_no,
                reference_date = reference_date,
                po_no = po_no,
                po_no_date = po_no_date,
                port_of_loading = port_loading,
                port_of_discharge = port_discharge,

                labels = {
                "REF NO :": reference_no,
                "DATE :": reference_date,
                "PORT OF LOADING :": port_loading,
                "PORT OF DISCHARGE :": port_discharge,
                "TERMS :": "DDP",
                "CONT NO :": "TBA",
                "SEAL NO :": "TBA"
            },
                packing_details = {"details":modified_pcks,
                                   "total" :{'TOTAL PACKAGES:': total_pcks,
                                            "GROSS WEIGHT:" : f'{total_w} kgs',
                                            'TOTAL CBM (m³) :': f'{cbm}'
                                            },},
                original_packing_details = original_pcks,
                totals = {'TOTAL PACKAGES:': total_pcks,
                        "GROSS WEIGHT:" : f'{total_w} kgs',
                        'TOTAL VOLUME :': f'{cbm}',
                        "is_verify": is_total_weight_verfy
                        },
              
                
    )
    data['packing_details']['shipping'] =[ f"REF: {reference_no} – {data['labels']['CONT NO :']}/{data['labels']['SEAL NO :']}"]

    # data = get_line_count(data)

    
    return data



def analysis_ci(page, DESCRIPTIONS_DATA, divided_by = None):
    table = page.extract_table()
    words = page.extract_words()
    lines = [line['text'] for line  in page.extract_text_lines()]

    shipper, importer_of_record, ship_to, reference_no, reference_date, port_loading, port_discharge, po_no, po_no_date = get_data(table= table, words= words)
    # original_pcks, modified_pcks, total_pcks, total_w, gross_w, is_total_weight_verfy = get_packing_details(table, lines)
    # cbm = calculate_cbm(original_pcks)
    original_items, total_amount = get_table_items(table, table_name = 'invoice', divided_by = divided_by)
    modified_items = copy.deepcopy(original_items)
    # total_idx = df1[df1.iloc[:, 6].astype(str).str.contains('total', case=False, na=False)].index[0]
    importer_of_record[0] = f"CONSIGNEE:\n{importer_of_record[0]}"
    # total_w = f'{int(total_w.replace(',', '')):,}'

    if divided_by == None:
        total = float(table[8][-1].replace('$', '').replace(',', '').replace(' ', '').strip())
    else:
        total = total_amount


    for item in modified_items:
        DESCRIPTIONS_DATA
        if item['description'] in DESCRIPTIONS_DATA['original']:
            idx = DESCRIPTIONS_DATA['original'].index(item['description'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        elif item['gpn'] in DESCRIPTIONS_DATA['item_id']:
            idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        # if item['description'] in DESCRIPTION_MAPPING:
        #     item['description'] = DESCRIPTION_MAPPING[item['description']]
        #     item['description_modified'] = 1
        if 'ROW' in item['description']:
            item['description_modified'] = 1
  
    data = dict(
                shipper = shipper,
                importer_of_record = importer_of_record,
                ship_to = ship_to,
                invoice_type = table[0][3],
                reference_no = reference_no,
                reference_date = reference_date,
                po_no = po_no,
                po_no_date = po_no_date,
                port_of_loading = port_loading,
                port_of_discharge = port_discharge,

                labels = {
                "REF NO :": reference_no,
                "DATE :": reference_date,
                "PORT OF LOADING :": port_loading,
                "PORT OF DISCHARGE :": port_discharge,
                "TERMS :": "DDP",
                "CONT NO :": "TBA",
                "SEAL NO :": "TBA"
            },
                
                original_items = original_items,
                items = modified_items,
                total = f'{total:,}'
                
    )
    
    # data = get_line_count(data)

    
    return data


def analysis_pdf_cipl(page,  DESCRIPTIONS_DATA, divided_by = None):
    table = page.extract_table()
    invoice_type = table[0][3]
    if invoice_type == 'COMMERCIAL INVOICE':
        data = analysis_ci(page, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA, divided_by = divided_by)
    else:
        data = analysis_pl(page,  divided_by = divided_by)
    return data

def create_cipl_data(results, DESCRIPTIONS_DATA):
    data = {}
    for key, res in results['commercial_invoice'].items():
        if key in results['packing_list']:
            res['labels'] = results['packing_list'][key]['labels'] 
            res['packing_details'] = results['packing_list'][key]['packing_details'] 
            res['original_packing_details'] = results['packing_list'][key]['original_packing_details'] 
            res['totals'] = results['packing_list'][key]['totals'] 

            res = get_line_count(res, DESCRIPTIONS_DATA)
            data[key] = res
            
    
    
    return data