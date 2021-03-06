#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json


OSMFILE = 'data/vancouver_canada_subset.osm'

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
double_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
address_re = re.compile(r'^addr\:')
street_re = re.compile(r'^street')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

mapping = { "St": "Street",
            "St.": "Street",
            "Rd.": "Road",
            "Ave": "Avenue",
            "Hwy": "Highway",
            "Hwy.": "Highway",
            "HWY": "Highway",
            "HIGHWAY": "Highway",
            "Moncton": "Moncton Street",
            "Pender": "Pender Street",
            "Tsawwassen": "North Tsawwassen",
            "av": "Avenue",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Edmonds": "Edmonds Street",
            "Hastings": "Hastings Street",
            "Blvd": "Boulevard",
            "Jervis": "Jarvis"
            }

def update_name(name, mapping):
    ''' 
    apply mapping transformation to address names
    '''
    try:
        street_name = name.split(' ')
        street_name[-1] = mapping[street_name[-1]]
        return ' '.join(street_name)

    except KeyError:
        mapping['name'] = 'name'
        return name

def shape_element(element):
    '''
    parse through elements for json export
    '''
    node = {}
    address = {}
    pos_attrib = ['lat', 'lon']
    if element.tag == "node" or element.tag == "way" :
        
        # populate tag type
        node['type'] = element.tag

        # parse through attributes
        for attrib in element.attrib:
            if attrib in CREATED:
                if 'created' not in node:
                    node['created'] = {}
                node['created'][attrib] = element.get(attrib)
            elif attrib in pos_attrib:
                continue
            else:
                node[attrib] = element.get(attrib)

        # populate position
        if set(pos_attrib).issubset(element.attrib):
            node['pos'] = [float(element.get('lat')), float(element.get('lon'))]

        # parse second-level tags for nodes
        for child in element:
            # parse second-level tags for ways and populate `node_refs`
            if child.tag == 'nd':
                if 'node_refs' not in node:
                    node['node_refs'] = []
                if 'ref' in child.attrib:
                    node['node_refs'].append(child.get('ref'))

            # throw out not-tag elements and elements without `k` or `v`
            if child.tag != 'tag' or 'k' not in child.attrib or 'v' not in child.attrib:
                continue
            key = child.get('k')
            val = child.get('v')

            # skip problematic characters
            if re.search(problemchars, key) or re.search(double_colon, key):
                continue

            # parse address
            elif re.search(address_re, key):
                # clean up the street names using mapping dict
                if key == 'addr:street':
                    val = update_name(val, mapping)

                key = key.replace('addr:', '')
                address[key] = val

            # everything else
            else:
                node[key] = val
                
        # compile address
        if len(address) > 0:
            node['address'] = {}
            street_full = None
            street_dict = {}
            street_format = ['prefix', 'name', 'type']
            # parse through address objects
            for key in address:
                val = address[key]
                if re.search(street_re, key):
                    if key == 'street':
                        street_full = val
                    elif 'street:' in key:
                        street_dict[key.replace('street:', '')] = val
                else:
                    node['address'][key] = val
            # assign street or catch-all to compile street dict
            if street_full:
                node['address']['street'] = street_full
            elif len(street_dict) > 0:
                node['address']['street'] = ' '.join([street_dict[key] for key in street_format])
        return node        
        
    else:
        return None

def process_map(file_in, pretty = False):
    '''
    main function that initiate the file transformation
    '''
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

if __name__ == "__main__":
    process_map(OSMFILE, True)