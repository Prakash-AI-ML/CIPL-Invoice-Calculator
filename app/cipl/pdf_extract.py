import copy
import pandas as pd
import re
from datetime import datetime
import pdfplumber


# A "section" row is a label-only row such as "MDA1 ..." or "ROW 3" with no quantity/price.
# NOTE: a priced item whose description merely starts with "MDA2 ..." is a REAL item.
SECTION_RE = re.compile(r'^(MDA\s?\d+|ROW\s?\d+)')


def is_section_row(item):
    """True only for label rows (MDA/ROW) that carry no quantity."""
    return bool(SECTION_RE.match(item['description'])) and not str(item.get('quantity', '')).strip()


def regex(raw_text):
    lines = raw_text.split("\n")

    result = []
    current = lines[0]

    for line in lines[1:]:
        if re.match(r'^(MDA\d+|\d|Support|Cooling|Kit)', line):
            result.append(current)
            current = line
        else:
            current += " " + line  # keep newline
    result.append(current)

    return result


def calculate_cbm1(lines):
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
            cbm_per_item = (length * width * height) / 1_000_000
            total_cbm += cbm_per_item * quantity

            print(data, cbm_per_item * quantity, total_cbm)

    return f'{total_cbm:,.2f}'


def calculate_cbm(lines):
    total_cbm = 0.0
    for line in lines:
        line = line.strip()
        if not line:
            continue

        data1 = line.split('/')
        if len(data1) < 2:
            continue

        data = {
            'quantity': data1[0],
            'area': data1[1].replace('cm', '').replace('-', '').strip(),
            'weight': data1[-1]
        }
        qty_match = re.match(r"^\s*(\d+)", data['quantity'])
        if not qty_match:
            continue

        quantity = int(qty_match.group(1))
        data['quantity'] = quantity

        dims = [d.strip() for d in data['area'].split('x')]
        if len(dims) != 3 or not all(d.isdigit() for d in dims):
            continue

        length, width, height = [int(d) for d in dims]

        # dimensions are in cm regardless of whether the line's unit suffix was present
        cbm_per_item = (length * width * height) / 1_000_000
        total_cbm += cbm_per_item * quantity

        print(data, cbm_per_item * quantity, 'total cbm', total_cbm)

    return f'{total_cbm:,.2f}'


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

    desc_map = dict(zip(DESCRIPTIONS_DATA['modified'], DESCRIPTIONS_DATA['lines']))
    id_map = dict(zip(DESCRIPTIONS_DATA['item_id'], DESCRIPTIONS_DATA['lines']))
    count = 0
    for item in data['items']:
        if is_section_row(item):
            count += 2
        elif item['description'] in desc_map:
            count += desc_map[item['description']] + 1
        elif item['gpn'] and item['gpn'] in id_map:  # guard against blank GPN
            count += id_map[item['gpn']] + 1
        else:
            count += 3
    if data['packing_details']:
        if data['packing_details']['details']:
            count += len(data['packing_details']['details']) + 2  # 1 for header and another for \n

        if data['packing_details']['total']:
            count += len(data['packing_details']['total']) + 1  # 1 for \n line

        if data['packing_details']['shipping']:
            count += len(data['packing_details']['shipping']) + 2  # 1 for header and another for \n

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
        if (w1 == "port" or w1 == "airport") and w2 == "of" and w3 == "loading":
            x0 = words[i]["x0"]
            x1 = words[i+2]["x1"]
            top = min(words[i]["top"], words[i+1]["top"], words[i+2]["top"])
            bottom = max(words[i]["bottom"], words[i+1]["bottom"], words[i+2]["bottom"])

            results["port_of_loading"] = (x0, top, x1, bottom)

        # Port of Discharge
        if (w1 == "port" or w1 == "airport") and w2 == "of" and w3 == "discharge":
            x0 = words[i]["x0"]
            x1 = words[i+2]["x1"]
            top = min(words[i]["top"], words[i+1]["top"], words[i+2]["top"])
            bottom = max(words[i]["bottom"], words[i+1]["bottom"], words[i+2]["bottom"])

            results["port_of_discharge"] = (x0, top, x1, bottom)
    height = (results['port_of_loading'][3] - results['port_of_loading'][1]) * 4
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
    m1 = re.search(r'PO\s*no:\s*([A-Za-z0-9\-]+)\s*Date:\s*([\d/]+)', table[3][3], re.IGNORECASE)

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


def clean_dataframe(dic, description=None):

    new_data = []
    for data in dic:
        gpn = data.get('GPN', '')
        # --- normalize GPN ---
        if pd.isna(gpn) or str(gpn).strip().lower() == 'nan':
            ref = ''
        else:
            ref = str(gpn).strip()

        item = data.get('ITEM')
        desc = (data.get('DESCRIPTION') or '')
        desc = desc if " DESCRIPTION " not in desc else desc.partition("DESCRIPTION")[-1].strip()

        country = data.get('COUNTRY OF ORIGIN')
        uom = data.get('UOM')
        qty = data.get('QUANTITY')
        fob_price = data.get('FOB PRICE SGD')
        fob_amount = data.get('FOB AMOUNT SGD')
        if 'FOB PRICE SGD' not in data:
            fob_price = data.get('PRICE SGD')
            fob_amount = data.get('AMOUNT SGD')

        if re.fullmatch(r'ROW\s*\d+', desc):
            pass

        if pd.isnull(gpn) and pd.isnull(ref) or '' == ref and desc and new_data and description == None:

            new_data[-1]['description'] += " " + desc

        elif pd.isnull(gpn) and ref and new_data and description == None:
            if desc:
                new_data[-1]['description'] += " " + desc

        else:
            data_ = {
                "item": "" if pd.isnull(item) else str(item),
                'description': "" if pd.isnull(desc) else desc,
                'gpn': "" if pd.isnull(ref) else None if pd.isna(ref) else ref,
                'uom': "" if pd.isnull(uom) else uom,
                'country_of_origin': "" if pd.isnull(country) else country,
                'quantity': "" if pd.isnull(qty) else f"{qty}",
                'fob_price_sgd': "" if fob_price is not None and '' == fob_price else "$" + (" " * (9 + 2 - len(f"{fob_price:,.{2}f}"))) + f"{fob_price:,.{2}f}",
                'fob_amount_sgd': "" if fob_amount is not None and '' == fob_amount else "$" + (" " * (13 + 5 - len(f"{fob_amount:,.{2}f}"))) + f"{fob_amount:,.{2}f}",
                'description_modified': 0
            }
            new_data.append(data_)
    return new_data


def get_table_items(
    table,
    table_name='packing_details',
    divided_by=None,
    descriptions=None
):
    if table_name == 'packing_details':
        return clean_dataframe([], description=descriptions), 0

    items = []
    total_amount = 0

    if not descriptions:
        descriptions = regex(table[7][2])

    row = table[7]

    def split_column(value, clean_currency=False):
        if value is None or value == '':
            return []

        values = str(value).strip().split('\n')

        if clean_currency:
            values = [
                v.replace('$ ', '')
                 .replace(',', '')
                 .strip()
                for v in values
            ]

        return values

    def get_value(values, index, default=''):
        return values[index] if index < len(values) else default

    item_col = split_column(row[0])
    gpn_col = split_column(row[1])
    origin_col = split_column(row[3])
    uom_col = split_column(row[4])
    quantity_col = split_column(row[5])
    fob_price_col = split_column(row[6], clean_currency=True)
    fob_amount_col = split_column(row[7], clean_currency=True)

    # If there are as many descriptions as priced rows, none of them is a label-only
    # row, so an item like "MDA2 701-PCWR-8-01) #3 pipe" must be treated as a real item.
    n_priced = max(len(item_col), len(fob_amount_col))
    allow_section_rows = len(descriptions) != n_priced

    idx = 0

    for desc in descriptions:
        if allow_section_rows and SECTION_RE.match(desc):
            item = {
                'ITEM': '',
                'GPN': '',
                'DESCRIPTION': desc,
                'COUNTRY OF ORIGIN': '',
                'UOM': '',
                'QUANTITY': '',
                'FOB PRICE SGD': '',
                'FOB AMOUNT SGD': ''
            }
        else:
            fob_price = get_value(fob_price_col, idx)
            fob_amount = get_value(fob_amount_col, idx)

            item = {
                'ITEM': get_value(item_col, idx),
                'GPN': get_value(gpn_col, idx),
                'DESCRIPTION': desc,
                'COUNTRY OF ORIGIN': get_value(origin_col, idx),
                'UOM': get_value(uom_col, idx),
                'QUANTITY': get_value(quantity_col, idx),
                'FOB PRICE SGD': (
                    float(fob_price)
                    if fob_price not in (None, '')
                    else ''
                ),
                'FOB AMOUNT SGD': (
                    float(fob_amount)
                    if fob_amount not in (None, '')
                    else ''
                )
            }

            idx += 1

        items.append(item)

    if divided_by:
        items, total_amount = get_final_recalculate_data(
            items, divided_by
        )

    return clean_dataframe(items, description=descriptions), total_amount


def get_packing_details(table, lines):
    pcks = re.split(r'packing details:?\n', table[7][2], flags=re.IGNORECASE)[-1].split('\n')
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

                # extract weight (int) - accepts "kg" or "kgs"
                weight_match = re.search(r'(\d+)\s*kg(?:s)?', item, re.IGNORECASE)
                weight = int(weight_match.group(1)) if weight_match else 0

                total_weight = qty * weight
                gross_w += total_weight

                # normalize unit spelling to "kgs" (never inserts/removes "each")
                base = item.strip()
                base = re.sub(
                    r'(\d+\s*kg)(s?)',
                    r'\1s',
                    base,
                    count=1,
                    flags=re.IGNORECASE
                )
                if base:
                    if '=' in base:
                        base = base.partition('=')[0].strip()
                    if 'each' in base.lower():
                        base = base.partition('each')[0].strip()

                output.append(f"{base} = {total_weight:,} KGs")

    total_w = total_w.replace('kgs', '').strip()

    return pcks, output, total_pcks, total_w, gross_w, total_w == f'{gross_w:,}'


def find_table_region(lines):

    result = {'header': [], 'footer': []}
    header_lines = ['COUNTRY PRICE AMOUNT', 'COUNTRY FOB PRICE FOB AMOUNT', 'ITEM GPN DESCRIPTION UOM QUANTITY', 'OF ORIGIN SGD SGD']
    for line in lines[10:]:
        if line['text'].strip() in header_lines:
            result['header'].append(line)
        if re.match(r"^TOTAL \$ [\d,\s]+\.\d{2}$", line['text'], re.IGNORECASE):  # \s for space in between the numbers
            result['footer'].append(line)

    header_items = result['header']

    x0 = min(item['x0'] for item in header_items)
    y0 = min(item['top'] for item in header_items)
    x1 = max(item['x1'] for item in header_items)
    y1 = max(item['bottom'] for item in header_items)

    header_bbox = [x0, y0, x1, y1]

    footer_items = result['footer']

    x0 = min(item['x0'] for item in footer_items)
    y0 = min(item['top'] for item in footer_items)
    x1 = max(item['x1'] for item in footer_items)
    y1 = max(item['bottom'] for item in footer_items)

    footer_bbox = [x0, y0, x1, y1]
    data = {'header': header_bbox, 'footer': footer_bbox}

    return data


def find_table_coloumn_region(words, result):
    data = {}
    columns_data = {}
    countries = []
    prices = []
    prices_ = []
    amounts = []
    amounts_ = []
    for word in words:
        if word['text'].strip() == 'ITEM':
            data['ITEM'] = [word['x0'] - 4, word['top'], word['x1'] + 3, word['bottom']]
        if word['text'].strip() == 'GPN':
            data['GPN'] = [data['ITEM'][2], word['top'], word['x1'] + 9, word['bottom']]
        if word['text'].strip() == 'DESCRIPTION':

            data['DESCRIPTION'] = [data['GPN'][2], word['top'], word['x1'], word['bottom']]
        if word['text'].strip() == 'UOM':
            data['UOM'] = [word['x0'], word['top'], word['x1'], word['bottom']]
        if word['text'].strip() == 'QUANTITY':
            data['QUANTITY'] = [word['x0'], word['top'], word['x1'], word['bottom']]
        if word['text'].strip() in ['COUNTRY', 'OF', 'ORIGIN']:
            countries.append([word['x0'], word['top'], word['x1'], word['bottom']])
        if word['text'].strip() in ['FOB', 'PRICE', 'SGD'] and word['text'].strip() not in prices_:

            prices.append([word['x0'], word['top'], word['x1'], word['bottom']])
            prices_.append(word['text'].strip())
        elif word['text'].strip() in ['FOB', 'AMOUNT', 'SGD']:
            amounts.append([word['x0'], word['top'], word['x1'], word['bottom']])
            amounts_.append(word['text'].strip())

    data['COUNTRY OF ORIGIN'] = [min(item[0] for item in countries), min(item[1] for item in countries), max(item[2] for item in countries), max(item[3] for item in countries)]
    data['FOB PRICE SGD'] = [min(item[0] for item in prices), min(item[1] for item in prices), max(item[2] for item in prices), max(item[3] for item in prices)]
    data['FOB AMOUNT SGD'] = [min(item[0] for item in amounts), min(item[1] for item in amounts), max(item[2] for item in amounts), max(item[3] for item in amounts)]

    data['DESCRIPTION'][2] = data['COUNTRY OF ORIGIN'][0]
    data['UOM'][0] = data['COUNTRY OF ORIGIN'][2]
    data['FOB PRICE SGD'][0] = data['QUANTITY'][2]
    if 'FOB' in prices_:
        data['FOB PRICE SGD'][2] += 5
    elif 'PRICE' in prices_:
        data['FOB PRICE SGD'][2] += 15
    data['FOB AMOUNT SGD'][0] = data['FOB PRICE SGD'][2]
    if 'FOB' in amounts_:
        data['FOB PRICE SGD'][2] += 5
    elif 'AMOUNT' in amounts_:

        data['FOB AMOUNT SGD'][2] += 10
    max_bottom = max([data[col][3] for col in ['COUNTRY OF ORIGIN', 'FOB PRICE SGD', 'FOB AMOUNT SGD']])
    for key in data.keys():
        data[key][3] = max_bottom

    for key, val in data.items():
        x0, top, x1, bottom = val
        columns_data[key] = [x0, result['header'][3], x1, result['footer'][1]]
    return columns_data


def extract_table_rows(words, columns_data, table_data, item_ids, amount=True, anchor_col=None):
    """
    words: list of dicts -> [{'text', 'x0', 'x1', 'top', 'bottom'}]
    columns_data: dict -> column bounding boxes
    item_ids: list of values used as row anchors (GPN / amount / price)
    anchor_col: column whose bbox the anchor values live in (restricts the word search,
                so e.g. a price in the amount column can't be mistaken for an anchor)

    returns:
        list of rows -> [{column_name: text}]
    """
    body_top = table_data['header'][3]
    body_bottom = table_data['footer'][1]
    wanted = [i for i in item_ids if i.strip()]

    def find_anchors(pool):
        anchors, used = [], set()
        for item in item_ids:
            text = item.replace('$', '').strip() if amount else item.strip()
            if not text:
                continue
            for word in pool:
                # Skip words on a line that already anchored a row, so duplicate values
                # (e.g. two rows both priced 2,200.00) each get their own anchor.
                if word['top'] in used:
                    continue
                wtext = word['text'].strip()
                if text == wtext:
                    anchors.append({'id': item, 'top': word['top']})
                    used.add(word['top'])
                    break
                elif text in wtext:
                    new_word = copy.deepcopy(word)
                    extra_char = len(word['text']) - len(text)
                    char_x = (word['x1'] - word['x0']) / len(word['text'])
                    word['x1'] = word['x1'] - (char_x * extra_char)
                    word['text'] = word['text'][:-extra_char]

                    new_word['text'] = new_word['text'][len(new_word['text']) - extra_char:]
                    new_word['x0'] = new_word['x1'] - (char_x * extra_char) + 1.25

                    words.append(new_word)
                    anchors.append({'id': item, 'top': word['top']})
                    used.add(word['top'])
                    break
        return sorted(anchors, key=lambda a: a['top'])

    body_words = [w for w in words if w['top'] >= body_top and w['bottom'] <= body_bottom]

    anchors = []
    if anchor_col:
        x0, _, x1, _ = columns_data[anchor_col]
        col_words = [w for w in body_words if w['x0'] >= x0 - 1 and w['x1'] <= x1 + 1]
        anchors = find_anchors(col_words)
    if len(anchors) < len(wanted):  # fallback: search the whole table body
        anchors = find_anchors(body_words)

    # Add a leading region only if there is real text between the header and the first
    # anchor (e.g. an MDA/ROW label line). A plain gap (padding below the header) must NOT
    # create an empty phantom row, otherwise every description shifts down by one.
    first_top = anchors[0]['top']
    text_above_first = any(
        w['top'] >= table_data['header'][3] - 1 and w['bottom'] <= first_top
        for w in body_words
    )
    if text_above_first:
        anchors.append({
            'id': '',
            'top': table_data['header'][3]
        })
        anchors = sorted(anchors, key=lambda x: x['top'])

    # Build row regions (small tolerance because anchor words from different columns
    # can differ by a fraction of a point in their 'top' value)
    TOL = 2
    row_regions = []
    for i in range(len(anchors)):
        top = anchors[i]['top'] - (TOL if i > 0 else 0)

        if i < len(anchors) - 1:
            bottom = anchors[i + 1]['top'] - TOL
        else:
            # last row -> till table bottom
            bottom = list(columns_data.values())[0][3]

        row_regions.append((top, bottom))

    # Extract text per row & column
    rows = []

    for row_top, row_bottom in row_regions:
        row_dict = {}

        for col_name, (x0, y0, x1, y1) in columns_data.items():

            cell_words = []

            for word in words:
                wx0, wx1 = word['x0'], word['x1']
                wtop, wbottom = word['top'], word['bottom']

                # Check if word is inside column AND row.
                # x0 tolerance: a word split out of a glued token (e.g. GPN+description
                # "1191713701(750-...") has an estimated x0 a point or two left of the column.
                if (
                    wx0 >= x0 - 3 and wx1 <= x1 and
                    wtop >= row_top and wbottom <= row_bottom
                ):
                    cell_words.append(word)

            # Sort words left -> right, then top -> bottom
            cell_words = sorted(cell_words, key=lambda w: (w['top'], w['x0']))

            # Join text
            row_dict[col_name] = " ".join(w['text'] for w in cell_words)

        rows.append(row_dict)

    return rows


def extract_table_data(page):
    table = page.extract_table()
    lines = page.extract_text_lines()
    words = page.extract_words()
    table_bbox = find_table_region(lines)
    columns_bbox = find_table_coloumn_region(words, table_bbox)

    gpn, price, amount = table[7][1].split('\n'), table[7][-2].split('\n'), table[7][-1].split('\n')

    items, desc = None, None
    if len(gpn) == len(price) == len(amount):
        items = extract_table_rows(words=words, columns_data=columns_bbox, table_data=table_bbox,
                                   item_ids=gpn, amount=False, anchor_col='GPN')
    elif len(gpn) < len(amount):
        items = extract_table_rows(words=words, columns_data=columns_bbox, table_data=table_bbox,
                                   item_ids=amount, anchor_col='FOB AMOUNT SGD')
    elif len(gpn) < len(price):
        items = extract_table_rows(words=words, columns_data=columns_bbox, table_data=table_bbox,
                                   item_ids=price, anchor_col='FOB PRICE SGD')
    if items:
        desc = [item['DESCRIPTION'] for item in items]

    return items, desc


def analysis_pl(page, divided_by=None):
    table = page.extract_table()
    words = page.extract_words()
    lines = [line['text'] for line in page.extract_text_lines()]

    shipper, importer_of_record, ship_to, reference_no, reference_date, port_loading, port_discharge, po_no, po_no_date = get_data(table=table, words=words)
    original_pcks, modified_pcks, total_pcks, total_w, gross_w, is_total_weight_verfy = get_packing_details(table, lines)
    cbm = calculate_cbm(original_pcks)

    importer_of_record[0] = f"CONSIGNEE:\n{importer_of_record[0]}"

    total_w = f"{int(total_w.replace(', ', '').replace(',', '')):,}"

    data = dict(
        shipper=shipper,
        importer_of_record=importer_of_record,
        ship_to=ship_to,
        invoice_type=table[0][3],
        reference_no=reference_no,
        reference_date=reference_date,
        po_no=po_no,
        po_no_date=po_no_date,
        port_of_loading=port_loading,
        port_of_discharge=port_discharge,

        labels={
            "REF NO :": reference_no,
            "DATE :": reference_date,
            "PORT OF LOADING :": port_loading,
            "PORT OF DISCHARGE :": port_discharge,
            "TERMS :": "DDP",
            "CONT NO :": "TBA",
            "SEAL NO :": "TBA"
        },
        packing_details={"details": modified_pcks,
                         "total": {'TOTAL PACKAGES:': total_pcks,
                                   "GROSS WEIGHT:": f'{total_w} kgs',
                                   'TOTAL CBM (m³) :': f'{cbm}'
                                   }, },
        original_packing_details=original_pcks,
        totals={'TOTAL PACKAGES:': total_pcks,
                "GROSS WEIGHT:": f'{total_w} kgs',
                'TOTAL VOLUME :': f'{cbm}',
                "is_verify": is_total_weight_verfy
                },
    )
    data['packing_details']['shipping'] = [f"REF: {reference_no} – {data['labels']['CONT NO :']}/{data['labels']['SEAL NO :']}"]

    return data


def analysis_ci(page, DESCRIPTIONS_DATA, divided_by=None):
    table = page.extract_table()
    words = page.extract_words()
    lines = [line['text'] for line in page.extract_text_lines()]

    shipper, importer_of_record, ship_to, reference_no, reference_date, port_loading, port_discharge, po_no, po_no_date = get_data(table=table, words=words)
    table_items, descriptions = extract_table_data(page)

    original_items, total_amount = get_table_items(table, table_name='invoice', divided_by=divided_by, descriptions=descriptions)
    modified_items = copy.deepcopy(original_items)

    if importer_of_record[0].lower() == 'Interbridge Solutions Co Ltd'.lower():
        print("Updated the consignee name from *Interbridge Solutions Co Ltd* to *Everpro Co., Ltd (Head Office)")
        importer_of_record = ['CONSIGNEE:\nEverpro Co., Ltd (Head Office)', '189/388 Village No. 5, Pharam 2Rd, Panthai Norasing, Muang,', 'Samut Sakhon 74000', 'Tel: 034-872-392', 'Fax: 034-872-393', 'Tax ID: 0115558011202']
    elif importer_of_record[0].lower() != 'Interbridge Solutions Co Ltd'.lower():
        importer_of_record[0] = f"CONSIGNEE:\n{importer_of_record[0]}"

    if divided_by == None:
        total = float(table[8][-1].replace('$', '').replace(',', '').replace(' ', '').strip())
    else:
        total = total_amount

    for item in modified_items:
        if port_loading.lower() == "singapore" and port_discharge.lower() == 'malaysia':

            item['description'] = re.sub(r'pipe', '', item['description'], flags=re.IGNORECASE)
            item['description_modified'] = 1
            if SECTION_RE.match(item['description']):
                item['description_modified'] = 1
        else:
            if is_section_row(item) or 'ROW' in item['description']:
                item['description_modified'] = 1
            if item['description'] in DESCRIPTIONS_DATA['original']:
                idx = DESCRIPTIONS_DATA['original'].index(item['description'])
                item['description'] = DESCRIPTIONS_DATA['modified'][idx]
                item['description_modified'] = 1
            elif item['gpn'] and item['gpn'] in DESCRIPTIONS_DATA['item_id']:  # guard against blank GPN
                idx = DESCRIPTIONS_DATA['item_id'].index(item['gpn'])
                item['description'] = DESCRIPTIONS_DATA['modified'][idx]
                item['description_modified'] = 1

    data = dict(
        shipper=shipper,
        importer_of_record=importer_of_record,
        ship_to=ship_to,
        invoice_type=table[0][3],
        reference_no=reference_no,
        reference_date=reference_date,
        po_no=po_no,
        po_no_date=po_no_date,
        port_of_loading=port_loading,
        port_of_discharge=port_discharge,

        labels={
            "REF NO :": reference_no,
            "DATE :": reference_date,
            "PORT OF LOADING :": port_loading,
            "PORT OF DISCHARGE :": port_discharge,
            "TERMS :": "DDP",
            "CONT NO :": "TBA",
            "SEAL NO :": "TBA"
        },

        original_items=original_items,
        items=modified_items,
        total=f'{total:,}'
    )

    return data


def analysis_pdf_cipl(page, DESCRIPTIONS_DATA, divided_by=None):
    table = page.extract_table()
    invoice_type = table[0][3]
    if invoice_type == 'COMMERCIAL INVOICE':
        data = analysis_ci(page, DESCRIPTIONS_DATA=DESCRIPTIONS_DATA, divided_by=divided_by)
    else:
        data = analysis_pl(page, divided_by=divided_by)
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