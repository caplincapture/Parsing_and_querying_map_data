# -*- coding: utf-8 -*-

import csv
import codecs
import re
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import string

import cerberus
import schema

OSM_PATH = "Geneve_street.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER = re.compile(r'^([a-z]|_)*$')
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]', re.UNICODE)

SCHEMA = schema.schema

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_type_prefix = re.compile(r'^\b\S+\.?', re.IGNORECASE)

expected_prefix = ["Clos", "Route", "Avenue", "Chemin", "Rue", "Boulevard", "Cours", "Quai", "Rampe", "Promenade", "Place", "Ruelle", "Terrasse", "Rond-point", "Passage", "Galerie", "Carrefour", "Plateau", "Square", "Parc"]

mapping_prefix = {
            "rue": "Rue",
            "Blvd." : "Boulevard",
            "clos" : "Clos",
            "rte" : "Route",
            "ave" : "Avenue"}

def audit_street_type(street_name, mapping):
    street_name = street_name.replace('  ',' ')
    m = street_type_prefix.search(street_name)
    if m:
        street_type = m.group()
        if street_type in mapping_prefix:
            street_name = re.sub(street_type, mapping[street_type], street_name)
    return street_name
        

def update_postcode(zipcode):
    zipcode = re.sub(" ", "", zipcode)
    zipcode = re.sub(r"\s+", "", zipcode)
    zipcode = zipcode[:5]
    return zipcode



def update_phone(phone):
    better_phone = phone.replace(" ", "")
    better_phone = re.sub("-", "", better_phone)
    better_phone = re.sub(r"\s+", "", better_phone)
    return better_phone

    
# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    '''
    function takes as input an iterparse Element object and returns a dictionary of cleaned and sorted node and way attributes
    according to a layout provided in the earlier lists
    '''

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  
    position = 0 
    
    if element.tag == 'node':
        for field in NODE_FIELDS:
            node_attribs[field] = element.attrib[field]
                
        for tag in element.iter('tag'):
            tag_dict = {}
            tag_dict['id'] = element.attrib['id']
            tag_dict['value'] = tag.attrib['v']
            if PROBLEMCHARS.match(tag.attrib['k']):
                continue
            elif tag.attrib['k'] =='postcode':
                tag_dict['value']=update_postcode(tag.attrib['v'])
                tag_dict['key'] = tag.attrib['k']
                tag_dict['type'] = 'regular'
            elif tag.attrib['k']=='phone':
                tag_dict['value']=update_phone(tag.attrib['v'])
                tag_dict['key'] = tag.attrib['k']
                tag_dict['type'] = 'regular'
            elif ':' in tag.attrib['k']:
                tag_dict['type'] = tag.attrib['k'].split(':')[0]
                tag_dict['key'] = tag.attrib['k'].split(':',1)[1]
                if tag.attrib['k'] =="addr:street":
                    tag_dict['value']=audit_street_type(tag.attrib['v'],mapping_prefix)
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
            tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]
        for nd in element.iter('nd'):
            nd_dict = {}
            nd_dict['id'] = element.attrib['id']
            nd_dict['node_id'] = nd.attrib['ref']
            nd_dict['position'] = position
            position += 1
            way_nodes.append(nd_dict)
        for tag in element.iter('tag'):
            tag_dict = {}
            tag_dict['id'] = element.attrib['id']
            if PROBLEMCHARS.match(tag.attrib["k"]):
                continue
            elif ':' in tag.attrib['k']:
                tag_dict['type'] = tag.attrib['k'].split(':')[0]
                tag_dict['key'] = tag.attrib["k"].split(':',1)[1]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
            tag_dict['value'] = tag.attrib['v']
            tags.append(tag_dict)
                
    return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
    return {'node': node_attribs, 'node_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({ k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.items()})

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
             #   if validate is True:
             #       validate_element(el, validator)
                    
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
    


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
    