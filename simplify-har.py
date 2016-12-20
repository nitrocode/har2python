#!/usr/bin/env python
import json
import argparse
import os.path
from copy import deepcopy
# from curl2py import create_request
import pdb


def get_value_from_path(listKeys, jsonData):
    localData = jsonData.copy()
    for k in listKeys:
        try:
            localData = localData[int(k)] if k.isdigit() else localData[k]
        except:
            return None
    return localData


def find_common(jsonData, common, index=0, loc=''):
    """Recursively iterate through a dictionary to find common key/value pairs

    :param jsonData: dictionary to sift through
    :param common: common flattened dictionary to search for values
    :param index: the index of the request (redundant due to param loc?)
    :param loc: the location to the json object
    """
    newCommon = common.copy()
    for k, v in jsonData.iteritems():
        if loc == '':
            curLoc = k
        else:
            curLoc = loc + '.' + str(k)
        if type(v) == dict:
            newCommon = find_common(v, newCommon, index, curLoc)
        elif type(v) in (str, unicode):
            newLoc = {
                'index': index,
                'loc': curLoc
            }
            if v in newCommon:
                newV = newCommon[v].copy()
                newV['count'] += 1
                newV['locations'] += [newLoc]
                newCommon[v] = newV
            else:
                newCommon[v] = {
                    'count': 1,
                    'locations': [newLoc]
                }
    return newCommon


def simplify_har(har, guids_only=False):
    """Attempts to simplify a har file by analyzing for patterns

    The function takes the following steps:

    - Reads an entry
        - scans POST data
        - scans GET data
        - scans response body
        - scans URL


    :param har: har json data
    :param guids_only: only return values between 32 and 36 chars
    :returns: data_common which contains a dict of values as keys and
              simplified_har which is a dict containing the interested entries
    """
    # simplified har
    shar = deepcopy(har)
    data_common = {}

    # find common entries
    for i, entry in enumerate(har['log']['entries']):
        loc = 'log.entries.{0}'.format(i)
        # check POST data
        try:
            # only grab the first mime type if its semicolon delimited
            dataMime = entry['request']['postData']['mimeType'].split(';')[0]
            data = entry['request']['postData']['text']
            if dataMime in \
                    ('application/json', 'application/x-www-form-urlencoded'):
                try:
                    data = json.loads(data)
                except:
                    # if in the form: key1=value1&key2=value2
                    data = dict([v.split('=') for v in mystr.split('&')])
                data_common.update(
                    find_common(
                        data, data_common, index=i,
                        loc=loc + '.request.postData.text'
                    )
                )
        except:
            data = None
        # check GET data
        queries = entry['request']['queryString']
        for i, q in enumerate(queries):
            data = {'value': q['value']}
            data_common.update(
                find_common(
                    data, data_common, index=i,
                    loc=loc + '.request.queryString.' + str(i)
                )
            )
        # check response
        # pdb.set_trace()
        try:
            data = json.loads(entry['response']['content']['text'])
            data_common.update(
                find_common(
                    data, data_common, index=i,
                    loc=loc + '.response.content.text'
                )
            )
        except (ValueError, KeyError):
            pass
        # check url
        url = entry['request']['url'].replace(
            'https://workbench-rc.netprospex.com/api/v1/', ''
        )
        url_parts = url.split('/')
        data = {i: u for i, u in enumerate(url_parts)}
        data_common.update(
            find_common(
                data, data_common, index=i, loc=loc + '.request.url'
            )
        )
    # iterate through common entries and replace with good var names
    # TODO: find the good variable names? longest? most common?
    # TODO: when simplifying, should we prompt for each variable?
    #       '8b8c6778-e741-4855-abaa-78a8110b9f2d' used 6 times.
    #       Add name to this var and all following its value? [y/N]: y
    shar['log']['entries'] = []
    if guids_only:
        for k, v in data_common.iteritems():
            # if v['count'] > 1 and len(k) in (32, 36):
            if len(k) in (32, 36):
                # pdb.set_trace()
                for loc in v['locations']:
                    try:
                        entry = int(loc['loc'].split('.')[2])
                    except:
                        continue
                    shar['log']['entries'].append(
                        har['log']['entries'][entry].copy())
                    # myd = get_value_from_path(locSplit, har)
            # else:
            #     print(k)
            #     print(len(k))
    return data_common, shar


def main(args):
    """Main function that only takes args as input

    :param args: parsed args from argparse
    """
    with args.input_file as f:
        try:
            har_data = json.loads(f.read())
        except TypeError:
            print("The file '{0}' is not valid JSON.".format(args.input_file))
            return None

    code = [
        '#!/usr/bin/env python',
        'import requests',
        'import pdb\n'
    ]
    data = None

    common, shar = simplify_har(har_data, guids_only=args.guids_only)
    if args.output_file:
        with open(args.output_file, "wb") as f:
            f.write(json.dumps(shar))
    print("Finished simplifying")
    pdb.set_trace()

    # for i, entry in enumerate(shar_data['log']['entries']):
    #     headers = {h['name']: h['value'] \
    #               for h in entry['request']['headers']}
    #     # c = entry['request']['cookies']
    #     cookies = {c['name']: c['value'] \
    #               for c in entry['request']['cookies']}
    #     url = entry['request']['url']
    #     method = entry['request']['method'].lower()
    #     try:
    #         data = entry['request']['postData']
    #     except:
    #         data = None
    #     code += create_request(url, data, method, cookies, headers)
    # print '\n'.join(code)

def is_valid_file(parser, arg):
    """Verifies if an input file is valid.

    Source: http://stackoverflow.com/a/11541450
    """
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # return an open file handle


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyzer HAR files')
    parser.add_argument("-i", "--input", dest="input_file", required=True,
                        help="input har file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument("-o", "--output", dest="output_file", required=True,
                        help="output har file")
    parser.add_argument("-g", "--guids-only", action='store_true',
                        help="grab strings between 32 and 36 chars")
    args = parser.parse_args()
    main(args)
