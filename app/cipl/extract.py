import copy
import pandas as pd
import re
from datetime import datetime



DESCRIPTION_MAPPING = {
'5400MM, 14" PCW Header Pipe Spools, North Outer Transport, Straight, APAC, Brooklyn, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) header pipe spool, 14", L=5400mm, welded assembly',
'3992MM, 20" PCW Header Pipe Spools, South Outer Transport, Active, APAC, Brooklyn, MDA, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=3992mm, welded assembly',
'6399MM, 14" PCW Header Pipe Spools, North Outer Transport, Active, APAC Brooklyn, MDA, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) header pipe spool, 14", L=6399mm, welded assembly',
'6399MM, 20" PCW Header Pipe Spools, South Outer Transport, Active, APAC Brooklyn, MDA, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L= 6399mm welded assembly',
'860MM, 3" PCW Deschutes Extension Wide HAC Pipe Spools, APAC Brooklyn, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) pipe spool, 3", L=860mm',
'Support Deschutes Extension, Wide HAC': 'Fabricated carbon steel pipe support extension',
'Kit, Ship Loose, Mechanical, NA, Brooklyn General Arrangement 1.0.3': 'Fabricated carbon steel mechanical piping components supplied as loose shipment, for industrial piping system installation',
'4" & 3" Deschutes PCW Extension Fabrication & Assembly Details Brooklyn 1.5': 'Fabricated carbon steel process cooling water (PCW) extension pipe assembly, 4" & 3", welded and assembled section',
'4" & 3" Deschutes PCW Extension Fabrication & Assembly Details Brooklyn 1.5': 'Fabricated carbon steel process cooling water (PCW) extension pipe assembly, 4" & 3", welded and assembled section',
'8" PCW Ladder Pipe Spool, Rhino Connection, APAC, Brooklyn, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, for industrial piping system installation',	
'8" PCW Ladder Pipe Spool, Rhino Connection (Mechanical End), APAC Brooklyn, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, mechanical end, welded assembly',
'8" PCW Ladder Pipe Spool, Rhino Connection with Deschutes - Electrical End, APAC, Brooklyn, Fabrication Details' : 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter with extension section, welded assembly',
'8" PCW Ladder Pipe Spool, South Outer TA, APAC, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section',
'8" PCW Ladder Pipe Spool, North Outer TA, APAC, Brooklyn, Fabrication Details' : 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section',
'8" PCW Ladder Pipe Spool, No Rhino Connection, MDA, APAC Brooklyn, Fabrication Details' : 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded assembly',
'8" PCW Ladder Pipe Spool, No Rhino Connection, Elect End, MDA, APAC Brooklyn, Fabrication Details' : 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded assembly',	
'8" PCW Ladder Pipe Spool, MID TA, APAC, Brooklyn, Fabrication Details' : 'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section',
'Kit, Ship Loose, Mechanical, NA, Brooklyn General Arrangement 1.0.3':'Fabricated carbon steel mechanical piping components supplied as loose shipment, for industrial piping system installation',
'Cooling Module Connection South' : 'Fabricated carbon steel pipe, cooling module connection',
'5397MM, 20" PCW Header Pipe Spools, South Outer Transport Drain Valve, Air Vent, Apac, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=5397 mm, welded assembly, fitted with drain valve and air vent',
'4372MM, 20" PCW Header Pipe Spools, South Outer Transport Drain Valve, Air Vent, Apac, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=4372 mm, welded assembly, fitted with drain valve and air vent',
'5612MM, 20" PCW Header Pipe Spools, South Outer Transport Drain Valve, Air Vent, Apac, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=5612 mm, welded assembly, fitted with drain valve and air vent',
'6264MM, 14" PCW Header Pipe Spools, North Outer Transport, Drain Valve, Air Vent, APAC, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=6264 mm, welded assembly, fitted with drain valve and air vent',
'860MM, 3" PCW Deschutes Extension Wide HAC Pipe Spools APAC Brooklyn, Fabrication Details': 'Fabricated carbon steel process cooling water (PCW) pipe spool, 3", L=860mm',
'4748MM, 20" PCW Header Pipe Spools, South Outer Transport Drain Valve, Air Vent, Apac, Brooklyn, Fabrication Details':'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=4748 mm, welded assembly, fitted with drain valve and air vent',
'8" Bray S31H, Butterfly Valve DI Body, 316SS Disc, 416SS Stem, EPDM seat c/w Gear operated': '8” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat',
'14" Bray S31H, Butterfly Valve DI Body, 316SS Disc, 416SS Stem, EPDM seat c/w Gear operated': '14” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat',
'20" Bray S31H, Butterfly Valve DI Body, 316SS Disc, 416SS Stem, EPDM seat c/w Gear operated': '20” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat',

}


DESCRIPTION_LINE_MAPPING = {
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 14", L=5400mm, welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=3992mm, welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 14", L=6399mm, welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=6399mm welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) pipe spool, 3", L=860mm': 3,
'Fabricated carbon steel pipe support extension': 2,
'Fabricated carbon steel mechanical piping components supplied as loose shipment, for industrial piping system installation': 4,
'Fabricated carbon steel process cooling water (PCW) extension pipe assembly, 4" & 3", welded and assembled section': 3,
'Fabricated carbon steel process cooling water (PCW) extension pipe assembly, 4" & 3", welded and assembled section': 3,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, for industrial piping system installation': 4,	
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, mechanical end, welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter with extension section, welded assembly': 4,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section': 3,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section': 3,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded assembly': 3,
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded assembly': 3,	
'Fabricated carbon steel process cooling water (PCW) ladder pipe spool, 8" diameter, welded industrial piping section': 3,
'Fabricated carbon steel mechanical piping components supplied as loose shipment, for industrial piping system installation': 4,
'Fabricated carbon steel pipe, cooling module connection': 2,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=5397 mm, welded assembly, fitted with drain valve and air vent': 4,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=4372 mm, welded assembly, fitted with drain valve and air vent': 4,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=5612 mm, welded assembly, fitted with drain valve and air vent': 4,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=6264 mm, welded assembly, fitted with drain valve and air vent': 4,
'Fabricated carbon steel process cooling water (PCW) pipe spool, 3", L=860mm': 3,
'Fabricated carbon steel process cooling water (PCW) header pipe spool, 20", L=4748 mm, welded assembly, fitted with drain valve and air vent': 4,
'8” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat': 4,
'14” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat': 4,
'20” Industrial butterfly valve, gear operated, for pipeline fluid control, ductile iron body, stainless steel disc and stem, EPDM seat': 4,

}

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
            'fob_price_sgd': "" if pd.isnull(fob_price) else "$" + (" " * (9 +2 -len(f"{fob_price:,.{2}f}"))) + f"{fob_price:,.{2}f}",
            'fob_amount_sgd': "" if pd.isnull(fob_amount) else "$" + (" " * (13 + 5 -len(f"{fob_amount:,.{2}f}"))) + f"{fob_amount:,.{2}f}",
            'description_modified': 0
        }
            new_data.append(data_)
    return new_data

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

def get_packing_details(df):
    pck = df[df.iloc[:, 2].astype(str).str.contains('Packing Details:', case=False, na=False)].index[0]
    total_pck = df[df.iloc[:, 4].astype(str).str.contains('TOTAL PACKAGES:', case=False, na=False)].index[0]
    total_gross = df[df.iloc[:, 4].astype(str).str.contains('GROSS WEIGHT:', case=False, na=False)].index[0]

    pcks = df.iloc[pck + 1:total_pck, 2].dropna().astype(str).tolist()
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
    
    total_pcks = df.iloc[total_pck, 4].replace('TOTAL PACKAGES:', '').strip()
    total_w = df.iloc[total_gross, 4].replace('GROSS WEIGHT:', '').replace('kgs', '').strip()
    return pcks, output, total_pcks, total_w, gross_w, total_w == f'{gross_w:,}'

def date_conversion(date_str):
    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
    formatted = date_obj.strftime('%d-%b-%y')
    return formatted


def get_data(df):
    shipper = df[df.iloc[:, 0].astype(str).str.contains('SHIPPER', case=False, na=False)].index[0]
    importer = df[df.iloc[:, 0].astype(str).str.contains('Importer of Record', case=False, na=False)].index[0]
    ship_to = df[df.iloc[:, 0].astype(str).str.contains('Ship to', case=False, na=False)].index[0]
    table_start = df[df.apply(lambda row: 'ITEM' in row.values and 'GPN' in row.values, axis=1)].index[0]
    port_loading = df[df.iloc[:, 3].astype(str).str.contains('Port of Loading', case=False, na=False)].index[0]
    po_no = df[df.iloc[:, 3].astype(str).str.contains('PO no:', case=False, na=False)].index[0]
    reference_no = df[df.iloc[:, 3].astype(str).str.contains('Reference No:', case=False, na=False)].index[0]
    # end_rows = df[df.iloc[:, 0].astype(str).str.contains('TOTAL', case=False, na=False)].index[0]
    shipper_ = df.iloc[shipper + 1:importer, 0].dropna().astype(str).tolist()
    importer_ = df.iloc[importer+1 : ship_to, 0].dropna().astype(str).tolist()
    ship_to_ = df.iloc[ship_to +1: table_start , 0].dropna().astype(str).tolist()
    port_loading_ = "\n".join(df.iloc[port_loading : port_loading +2, 3]).replace('Port of Loading:', "").strip()
    port_discharge = "\n".join(df.iloc[port_loading : port_loading +2, 6]).replace('Port of Discharge :', "").strip()
    reference_no_ = "\n".join(df.iloc[reference_no : reference_no +1, 3]).replace('Reference No:', "").strip()
    reference_no_date = date_conversion("\n".join(df.iloc[reference_no : reference_no +1, 7]))
    po_no_ = "\n".join(df.iloc[po_no : po_no +1, 3]).replace('PO no:', "").strip()
    po_no_date = date_conversion("\n".join(df.iloc[po_no : po_no +1, 7]))
    # total = df.iloc[end_rows, 7]
    
    return shipper_, importer_, ship_to_, reference_no_, reference_no_date, port_loading_, port_discharge, po_no_, po_no_date


def get_final_recalculate_data(df_transactions, divided_by):
    total_amount = 0
    # print(df_transactions.columns)
    if 'PRICE SGD' in df_transactions.columns:
        df_transactions = df_transactions.rename(columns={
                            'PRICE SGD': 'FOB PRICE SGD'
                        })
    if 'AMOUNT SGD' in df_transactions.columns:
        df_transactions = df_transactions.rename(columns={
                            'AMOUNT SGD': 'FOB AMOUNT SGD'
                        })
    for row in df_transactions.iterrows():
        if pd.isna(row[1]['FOB PRICE SGD']):
            pass
        else:
            row[1]['FOB PRICE SGD'] = round(row[1]['FOB PRICE SGD'] / divided_by, 2)
            row[1]['FOB AMOUNT SGD'] = round(row[1]['FOB PRICE SGD'] * row[1]['QUANTITY'], 2)

            total_amount += row[1]['FOB AMOUNT SGD']
    return df_transactions, round(total_amount, 2)

def get_table_items(df, table= 'packing_details', divided_by = None):
    header_row = df[df.apply(lambda row: 'ITEM' in row.values and 'GPN' in row.values and 'DESCRIPTION' in row.values, axis=1)]
    total_amount = 0
    if header_row.empty:
        raise ValueError("Could not find header row with 'ITEM', 'DESCRIPTION' and 'GPN'")

    header_idx = header_row.index[0]
    print(f"Header found at index: {header_idx}")

    # Find the end of the table: the row that contains "RINGGIT MALAYSIA" in column 0
    if table == 'packing_details':
        end_rows = df[df.iloc[:, 2].astype(str).str.contains('Packing Details:', case=False, na=False)]
    else:
        end_rows = df[df.iloc[:, 6].astype(str).str.contains('TOtal', case=False, na=False)]
    # end_rows = df[df.iloc[:, 0].astype(str).str.contains('Packing Details:', case=False, na=False)]

    if end_rows.empty:
        print("Warning: 'Packing Details:' not found → using full data after header")
        end_idx = len(df)
    else:
        end_idx = end_rows.index[0]
        print(f"Table ends before index: {end_idx}")
    #  Extract only the transaction rows
    df_transactions = df.iloc[header_idx:end_idx].copy()

   # Flag to track whether row 1 should be dropped
    drop_ = False

    # Merge row 1 into row 0 if value is 'SGD'
    for col in [6, 7]:
        if df_transactions.iloc[1, col] == 'SGD':
            drop_ = True
            df_transactions.iloc[0, col] = (
                str(df_transactions.iloc[0, col]) + " " + str(df_transactions.iloc[1, col])
            )

    # Drop row 1 if needed
    if drop_:
        df_transactions = df_transactions.drop(index=df_transactions.index[1])

    # Reset index BEFORE setting headers
    df_transactions = df_transactions.reset_index(drop=True)
    # Set the first row (which is the header) as column names
    df_transactions.columns = df_transactions.iloc[0]   # Use the DATE, REF.NO. row as headers
    df_transactions = df_transactions[1:]               # Remove the header row from data
    df_transactions = df_transactions.reset_index(drop=True)

    # Clean up column names and drop completely empty columns
    df_transactions.columns = df_transactions.columns.fillna('').str.strip()
    df_transactions = df_transactions.loc[:, (df_transactions != "").any(axis=0)]  # remove empty cols
    df_transactions = df_transactions.dropna(how='all').reset_index(drop=True)  
    if divided_by:
        df_transactions, total_amount = get_final_recalculate_data(df_transactions, divided_by)
    dic = df_transactions.to_dict(orient='records')
    
    # return dic
    return clean_dataframe(dic), total_amount


def get_line_count(data, DESCRIPTIONS_DATA):
    count = 0
    for item in data['items']:
        if item['description'].startswith('ROW'):
            count +=1
        if item['description'].startswith('MDA'):
            count +=1
        # elif item['description'] in DESCRIPTION_LINE_MAPPING:
        #     count += DESCRIPTION_LINE_MAPPING[item['description']]
        elif item['description'] in DESCRIPTIONS_DATA['original']:
            idx = DESCRIPTIONS_DATA['original'].index(item['description'])
            count += DESCRIPTIONS_DATA['lines'][idx] + 1
        elif item['gpn'] in DESCRIPTIONS_DATA['item_id']:
            idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
            count += DESCRIPTIONS_DATA['lines'][idx] + 1
        

        else:
            print('not working')
            count +=2
    if data['packing_details']:
        if data['packing_details']['details']:
            count += len(data['packing_details']['details']) + 2 # 1 for header and another for \n
        if data['packing_details']['total']:
            count += len(data['packing_details']['total']) + 1 # 1 for \n line
        if data['packing_details']['shipping']:
            count += len(data['packing_details']['shipping']) + 2 # 1 for header and another for \n

    data['packing_details']['present_lines'] = count

    return data

def analysis_cipl(df, df1, DESCRIPTIONS_DATA, divided_by = None):

    shipper, importer_of_record, ship_to, reference_no, reference_date, port_loading, port_discharge, po_no, po_no_date = get_data(df)
    original_pcks, modified_pcks, total_pcks, total_w, gross_w, is_total_weight_verfy = get_packing_details(df)
    cbm = calculate_cbm(original_pcks)
    original_items, total_amount = get_table_items(df1, table = 'invoice', divided_by = divided_by)
    modified_items = copy.deepcopy(original_items)
    total_idx = df1[df1.iloc[:, 6].astype(str).str.contains('total', case=False, na=False)].index[0]
    importer_of_record[0] = f"CONSIGNEE:\n{importer_of_record[0]}"
    total_w = f'{int(total_w.replace(',', '')):,}'

    if divided_by == None:
        total = df1.iloc[total_idx, 7]
    else:
        total = total_amount


    for item in modified_items:
        # if item['description'] in DESCRIPTION_MAPPING:
        #     item['description'] = DESCRIPTION_MAPPING[item['description']]
        #     item['description_modified'] = 1
        if item['description'] in DESCRIPTIONS_DATA['original']:
            idx = DESCRIPTIONS_DATA['original'].index(item['description'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        elif item['gpn'] in DESCRIPTIONS_DATA['item_id']:
            idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        if 'ROW' in item['description']:
            item['description_modified'] = 1
    
    data = dict(
                shipper = shipper,
                importer_of_record = importer_of_record,
                ship_to = ship_to,
                invoice_type = None,
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
                        'TOTAL VOLUME :': '102.04 CBM',
                        "is_verify": is_total_weight_verfy
                        },
                original_items = original_items,
                items = modified_items,
                total = f'{total:,}'
                
    )
    data['packing_details']['shipping'] =[ f"REF: {reference_no} – {data['labels']['CONT NO :']}/{data['labels']['SEAL NO :']}"]

    data = get_line_count(data, DESCRIPTIONS_DATA)

    
    return data

def get_line_count(data, DESCRIPTIONS_DATA):

    desc_map = dict(zip(DESCRIPTIONS_DATA['modified'], DESCRIPTIONS_DATA['lines']))
    id_map = dict(zip(DESCRIPTIONS_DATA['item_id'], DESCRIPTIONS_DATA['lines']))
    count = 0
    for item in data['items']:
        if item['description'].startswith('ROW'):
            count +=2
        elif item['description'].startswith('MDA'):
            count +=2
       
        elif item['description'] in desc_map:
            count += desc_map[item['description']] + 1
        elif item['gpn'] in id_map:
            count += id_map[item['gpn']] + 1
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

def get_data_to_cipl(data, DESCRIPTIONS_DATA):
    
    original_items = data['items']
    modified_items = copy.deepcopy(original_items)

    for item in modified_items:
        # if item['description'] in DESCRIPTION_MAPPING:
        #     item['description'] = DESCRIPTION_MAPPING[item['description']]
        #     item['description_modified'] = 1

        if item['description'] in DESCRIPTIONS_DATA['original']:
            idx = DESCRIPTIONS_DATA['original'].index(item['description'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        elif item['gpn'] in DESCRIPTIONS_DATA['item_id']:
            idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
            item['description'] = DESCRIPTIONS_DATA['modified'][idx]
            item['description_modified'] = 1
        elif 'ROW' in item['description']:
            item['description_modified'] = 1
        elif item['description'] in DESCRIPTIONS_DATA['modified']:
            item['description_modified'] = 1

        else:
            item['description_modified'] = 0
        
    
    data = dict(
                shipper = data['shipper'],
                importer_of_record = data['importer_of_record'],
                ship_to = data['ship_to'],
                invoice_type = None,
                reference_no = data['reference_no'],
                reference_date = data['reference_date'],
                po_no = data['po_no'],
                po_no_date = data['po_no_date'],
                port_of_loading = data['port_of_loading'],
                port_of_discharge = data['port_of_discharge'],

                labels = {
                "REF NO :": data['reference_no'],
                "DATE :": data['reference_date'],
                "PORT OF LOADING :": data['port_of_loading'],
                "PORT OF DISCHARGE :": data['port_of_discharge'],
                "TERMS :": "DDP",
                "CONT NO :": data['labels']["CONT NO :"],
                "SEAL NO :": data['labels']["SEAL NO :"]
            },
                packing_details = {"details":data['packing_details']['details'],
                                   "total" :{'TOTAL PACKAGES:': data['packing_details']["total"]['TOTAL PACKAGES:'],
                                            "GROSS WEIGHT:" : data['packing_details']["total"]["GROSS WEIGHT:"],
                                            'TOTAL CBM (m³) :': f'{data['packing_details']["total"]['TOTAL CBM (m³) :']}'
                                            },
                                    'shipping': data['packing_details']['shipping']
                                            },
                original_packing_details = data['original_packing_details'],
                totals = {'TOTAL PACKAGES:': data['totals']['TOTAL PACKAGES:'],
                        "GROSS WEIGHT:" : data['totals']["GROSS WEIGHT:"],
                        'TOTAL VOLUME :': data['totals']['TOTAL VOLUME :'],
                        "is_verify": data['totals']['is_verify']
                        },
                original_items = data['original_items'],
                items = modified_items,
                total = data['total']
                
    )

    data = get_line_count(data, DESCRIPTIONS_DATA)
    return data

    
