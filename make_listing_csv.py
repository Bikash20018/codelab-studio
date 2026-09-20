#!/usr/bin/env python3
"""Fill a Partner Center Store-listing .csv from store-listing/en-us.txt.

Partner Center's importer requires the Field, ID and Type columns to arrive
exactly as it wrote them, so a .csv cannot be authored from scratch - the ID
numbers are assigned per product. The workflow is therefore:

    1. Partner Center > Store listings > Export listing   (gives listing.csv)
    2. python make_listing_csv.py <exported.csv>
    3. import the produced store-listing.zip

Only the language column is touched. Fields named in en-us.txt that the export
does not contain are reported rather than invented, and fields the export has
but the content file does not are left exactly as they were.

    python make_listing_csv.py exported.csv            # -> store-listing.zip
    python make_listing_csv.py exported.csv --lang fr-fr
    python make_listing_csv.py --selftest
"""

import csv
import os
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
CONTENT = HERE / 'store-listing' / 'en-us.txt'
OUT_ZIP = HERE / 'store-listing.zip'


def read_content(path):
    """Parse the '## Field' blocks into {field: value}, preserving blank lines."""
    fields, name, body = {}, None, []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            if name:
                fields[name] = '\n'.join(body).strip()
            name, body = line[3:].strip(), []
        elif line.startswith('#'):
            continue          # comment, but only at the left margin
        elif name:
            body.append(line)
    if name:
        fields[name] = '\n'.join(body).strip()
    return fields


def fill(export_csv, content, language):
    with open(export_csv, newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.reader(stream))
    if not rows:
        raise SystemExit(f'{export_csv} is empty - re-export it from Partner Center.')

    header = rows[0]
    try:
        field_col = header.index('Field')
    except ValueError:
        raise SystemExit('No "Field" column found. Is this really the exported '
                         'listing .csv from Partner Center?')
    if language in header:
        lang_col = header.index(language)
    else:
        lang_col = len(header)
        header.append(language)

    wanted = {k.lower(): v for k, v in content.items()}
    filled, seen = [], set()
    for row in rows[1:]:
        if not row or field_col >= len(row):
            continue
        while len(row) <= lang_col:
            row.append('')
        key = row[field_col].strip().lower()
        if key in wanted:
            row[lang_col] = wanted[key]
            filled.append(row[field_col].strip())
            seen.add(key)

    missing = [k for k in content if k.lower() not in seen]
    return rows, filled, missing


def main(argv):
    if '--selftest' in argv:
        return selftest()
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 1:
        raise SystemExit(__doc__)
    language = argv[argv.index('--lang') + 1] if '--lang' in argv else 'en-us'

    content = read_content(CONTENT)
    rows, filled, missing = fill(args[0], content, language)

    staged = HERE / 'store-listing'
    out_csv = staged / 'listing.csv'
    with open(out_csv, 'w', newline='', encoding='utf-8-sig') as stream:
        csv.writer(stream).writerows(rows)

    # The importer wants a zip whose entries live under one root folder, and the
    # asset paths in the .csv are relative to that same root.
    with zipfile.ZipFile(OUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for item in sorted(staged.iterdir()):
            if item.suffix.lower() in ('.csv', '.png', '.jpg', '.jpeg'):
                bundle.write(item, f'store-listing/{item.name}')

    print(f'filled {len(filled)} fields for {language}:')
    print('  ' + ', '.join(filled))
    if missing:
        print(f'\nNOT in the exported .csv, so not written ({len(missing)}):')
        print('  ' + ', '.join(missing))
        print('  Check the exact spelling in the export\'s Field column and fix')
        print(f'  {CONTENT.name}, or enter these by hand in Partner Center.')
    shots = [f for f in staged.iterdir() if f.suffix.lower() in ('.png', '.jpg', '.jpeg')]
    if not shots:
        print('\nWARNING: no screenshots in store-listing/. At least one is required.')
    print(f'\nwrote {OUT_ZIP.relative_to(HERE)} - import that in Partner Center.')


def selftest():
    """Merging must hit the right row, add a missing language column, and leave
    Field/ID/Type untouched - that last part is what the importer checks."""
    import tempfile
    sample = [['Field', 'ID', 'Type', 'default'],
              ['Title', '101', 'Text', ''],
              ['Description', '102', 'Text', 'old text'],
              ['Feature1', '103', 'Text', ''],
              ['TrailerTitle', '199', 'Text', 'keep me']]
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / 'export.csv'
        with open(path, 'w', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerows(sample)
        content = {'Title': 'CodeLab Studio', 'Description': 'new text',
                   'Feature1': 'a feature', 'NotAField': 'ignored'}
        rows, filled, missing = fill(path, content, 'en-us')

    assert rows[0] == ['Field', 'ID', 'Type', 'default', 'en-us'], rows[0]
    assert rows[1] == ['Title', '101', 'Text', '', 'CodeLab Studio'], rows[1]
    assert rows[2][4] == 'new text' and rows[2][3] == 'old text', rows[2]
    assert rows[4] == ['TrailerTitle', '199', 'Text', 'keep me', ''], rows[4]
    assert sorted(filled) == ['Description', 'Feature1', 'Title'], filled
    assert missing == ['NotAField'], missing

    # Every ID and Type must survive untouched, or the import is rejected.
    for before, after in zip(sample[1:], rows[1:]):
        assert before[:3] == after[:3], (before, after)
    print('selftest ok')


if __name__ == '__main__':
    main(sys.argv[1:])
