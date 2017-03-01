#!/usr/bin/python
# coding=UTF-8
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
import argparse
import time
import os

import csv
def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def csvUnicodeDictReader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.DictReader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def make_inherited_tree_name(csv, entry):
    if entry.get('parent') != None:
        if entry.get('parent') != 0:
            return make_inherited_tree_name(csv, csv['data'][entry.get('parent')]) + "->" + entry['name']
    return entry['name']

def get_inheritance_tree_depth(csv, entry):
    if entry.get('parent') != None:
        if entry.get('parent') != 0:
            return get_inheritance_tree_depth(csv, csv['data'][entry.get('parent')]) + 1
    return 0

#Produces an output Dictionary of the following form:
#{
#   id = {
#       'name' = 'name',
#       'parent' = id,
#       'childs' = [id, ...],
#       'timing' = {
#           'minimum' = UINT_MAX,
#           'maximum' = 0,
#           'total' = 0,
#           'calls' = 0,
#       },
#       'timer' = 'time_between_calls',
#       'delta' = {
#           'timestamp' = ['work', 'timer'],
#       },
#   },
#}
def parse_csv(file):
    fileHandle = None
    csvReader = None
    
    try:
        fileHandle = open(file, "r", encoding='utf-8')
    except IOError as e:
        print("Error opening file '{}': {}".format(file, SystemError.exc_info()))
    
    lookupTable = {}
    rlookupTable = {}
    finalTable = {
        'data': lookupTable,
        'lookup' : rlookupTable,
    }
    
    csvReader = csv.DictReader(fileHandle, delimiter=',', quotechar='"')
    for row in csvReader:
        intId = int(row['id'], 16)
        intParent = int(row['parent_id'], 16)
        intTimer = int(row['expected_time_between_calls'])
        intDeltaTimer = int(row['actual_time_between_calls'])
        intDeltaCall = int(row['time_delta_µs'])
        intTimestamp = int(row['start_time'])
        
        # Ensure that the base structure for tracking exists.
        if not intId in lookupTable:
            # Basic Structure
            lookupTable[intId] = {
                'name': row['name'],
                'parent': intParent,
                'childs': [],
                'call': {
                    'minimum': 9223372036854775808,
                    'maximum': 0,
                    'total': 0,
                    'count': 0,
                    'data': {},
                    'times': {},
                },
                'timer': {
                    'interval': intTimer,
                    'minimum': 9223372036854775808,
                    'maximum': 0,
                    'total': 0,
                    'count': 0,
                    'data': {},
                    'times': {},
                }
            }
            # And for reverse lookup (Name -> Id)
            rlookupTable[make_inherited_tree_name(finalTable, lookupTable[intId])] = intId
        
        # Find the existing entry
        entry = lookupTable[intId]
        if intParent != 0: # We have a parent, so lets add ourselves as a child to it.
            if not intId in lookupTable[intParent]['childs']:
                lookupTable[intParent]['childs'].append(intId)
        
        entry['call']['data'][intTimestamp] = intDeltaCall
        if intDeltaCall < entry['call']['minimum']:
            entry['call']['minimum'] = intDeltaCall
        if intDeltaCall > entry['call']['maximum']:
            entry['call']['maximum'] = intDeltaCall
        entry['call']['total'] += intDeltaCall
        entry['call']['count'] += 1
        if intDeltaCall in entry['call']['times']:
            entry['call']['times'][intDeltaCall] += 1
        else:
            entry['call']['times'][intDeltaCall] = 1

        if entry['timer']['interval'] != 0:
            entry['timer']['data'][intTimestamp] = intDeltaTimer
            if intDeltaTimer < entry['timer']['minimum']:
                entry['timer']['minimum'] = intDeltaTimer
            if intDeltaTimer > entry['timer']['maximum']:
                entry['timer']['maximum'] = intDeltaTimer
            entry['timer']['total'] += intDeltaTimer
            entry['timer']['count'] += 1
            if intDeltaTimer in entry['timer']['times']:
                entry['timer']['times'][intDeltaTimer] += 1
            else:
                entry['timer']['times'][intDeltaTimer] = 1

    return finalTable

def compare_single(lut, c_ref, e_ref, c_cmp, e_cmp, full_name, sensitivity, depth=0):
    data = {}
    e = c = None
    c_min = c_avg = c_max = 0
    t_min = t_avg = t_max = 0
    
    if (e_cmp != None) and (e_ref != None):
        c_min = e_cmp['call']['minimum'] - e_ref['call']['minimum']
        c_max = e_cmp['call']['maximum'] - e_ref['call']['maximum']
        c_avg = (e_cmp['call']['total'] / e_cmp['call']['count']) - (e_ref['call']['total'] / e_ref['call']['count'])
        if e_ref['timer']['interval'] != 0:
            t_min = e_cmp['timer']['minimum'] - e_ref['timer']['minimum']
            t_max = e_cmp['timer']['maximum'] - e_ref['timer']['maximum']
            t_avg = (e_cmp['timer']['total'] / e_cmp['timer']['count']) - (e_ref['timer']['total'] / e_ref['timer']['count'])
        e = e_ref
        c = c_ref
    else:
        mult = 1
        if (e_ref != None):
            e = e_ref
            c = c_ref
            mult = -1
        if (e_cmp != None):
            e = e_cmp
            c = c_cmp

        c_min = e['call']['minimum'] * mult
        c_max = e['call']['maximum'] * mult
        c_avg = (e['call']['total'] / e['call']['count']) * mult
        if e['timer']['interval'] != 0:
            t_min = e['timer']['minimum'] * mult
            t_max = e['timer']['maximum'] * mult
            t_avg = (e['timer']['total'] / e['timer']['count']) * mult

    data[full_name] = {
        'id': c['lookup'][full_name],
        'name': "{}{}".format('\t'*get_inheritance_tree_depth(c, e), e['name']),
        'call': {
            'minimum': c_min,
            'average': c_avg,
            'maximum': c_max,
        },
        'timer': {
            'minimum': t_min,
            'average': t_avg,
            'maximum': t_max,
        },
    }

    return data

def compare(c_ref, c_cmp, sensitivity):
    # Build matched lookup table
    lut = {}
    for k,v in c_ref['lookup'].items():
        if k in lut:
            lut[k][0] = v
        else:
            lut[k] = {0: v}
    for k,v in c_cmp['lookup'].items():
        if k in lut:
            lut[k][1] = v
        else:
            lut[k] = {1: v}
    
    data = {}
    for k,v in lut.items():
        if v.get(0) != None:
            if v.get(1) != None:
                # Compare (Have both)
                data.update(compare_single(lut, c_ref, c_ref['data'][v.get(0)], c_cmp, c_cmp['data'][v.get(1)], k, sensitivity))
            else:
                data.update(compare_single(lut, c_ref, c_ref['data'][v.get(0)], c_cmp, None, k, sensitivity))
        else:
            if v.get(1) != None:
                data.update(compare_single(lut, c_ref, None, c_cmp, c_cmp['data'][v.get(1)], k, sensitivity))
    
    return data

# Main
def main():
    ts_program_start = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", help="Input Reference CSV")
    parser.add_argument("compare_to", help="Input Comparison CSV")
    parser.add_argument("output", help="Output File")
    parser.add_argument("-s", "--sensitivity", help="Sensitivity value to use when comparing output", type=int, default=100)
    args = parser.parse_args()
    
    # Verify arguments
    if not os.path.isfile(args.reference):
        print("Reference file '{}' not found, exiting...".format(args.reference))
        return -1
    if not os.path.isfile(args.compare_to):
        print("Comparison file '{}' not found, exiting...".format(args.compare_to))
        return -1

    # Open Files
    csvRef = parse_csv(args.reference)
    csvCmp = parse_csv(args.compare_to)
    data = compare(csvRef, csvCmp, args.sensitivity)

    flOut = None
    try:
        flOut = open(args.output, "w+", encoding="utf-8")
    except:
        print("Failed to open '{}' for writing, exiting...".format(args.output))
    
    flOut.write("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>OBS Profiler Comparison Results</title>
        <style>
            body {
                background: #101010;
                color: #D0D0D0;
            }
            table {
                width: 100%;
                height: auto;
            }

            /* Headers */
            table tr:first-child th {
                background: #353535;
            }
            table tr:nth-child(2) th:nth-child(2n-1) {
                background: #252525;
            }
            table tr:nth-child(2) th:nth-child(2n) {
                background: #2A2A2A;
            }
            table tr th {
                border-bottom: 1px solid #202020;
            }
            
            /* Content */
            table tr td {
                text-align: right;
                overflow: hidden;
                margin: 0px;
                padding: 2px 10px;
                border-bottom: 1px solid #101010;
            }
            table tr:nth-child(2n-1) td {
                background: #151515;
            }
            table tr:nth-child(2n) td {
                background: #1A1A1A;
            }
            table tr:hover td {
                background: #202020;
            }
            table tr td.bad {
                color: #FFD0D0;
            }
            table tr td.good {
                color: #D0FFD0;
            }

            table tr td:first-child {
                text-align: left;
            }
            table tr td:not(:first-child) {
                max-width: 200px !important;
                width: auto !important;
                min-width: 50px !important;
            }
        </style>
    </head>
    <body style="padding: 0; margin: 0; border: 0;">""")
    flOut.write("""
        <span>Reference: {}</span><br>
        <span>Testing: {}</span><br>""".format(args.reference, args.compare_to))
    flOut.write("""
        <table cellspacing=0 cellpadding=0>
            <tr>
                <th rowspan=2>Name</th>
                <th colspan=3>Call</th>
                <th colspan=3>Timer</th>
            </tr>
            <tr>
                <th>Min</th>
                <th>Avg</th>
                <th>Max</th>
                <th>Min</th>
                <th>Avg</th>
                <th>Max</th>
            </tr>""")

    for k,v in data.items():
        htmlOut = """
            <tr>
            <td>"""
        htmlOut += v['name'].replace('\t', '&emsp;') + "</td>"
        for k2,v2 in v['call'].items():
            csscls = ""
            if v2 > args.sensitivity:
                csscls = "bad"
            elif v2 < -args.sensitivity:
                csscls = "good"
            htmlOut += """
            <td class='{}'>{} µs</td>\n""".format(csscls, int(v2))

        for k2,v2 in v['timer'].items():
            csscls = ""
            if v2 > args.sensitivity:
                csscls = "bad"
            elif v2 < -args.sensitivity:
                csscls = "good"
            htmlOut += """
            <td class='{}'>{} µs</td>\n""".format(csscls, int(v2))

        htmlOut += """
            </tr>"""
        flOut.write(htmlOut)

    flOut.write("""
        </table>
    </body>
</html>""")
    
    print("Script completed in {} seconds.".format(time.perf_counter() - ts_program_start))
    return

if __name__ == "__main__":
    main()