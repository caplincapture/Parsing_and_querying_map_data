
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import string

# file to audit
osm_file = open("sample.osm", "r")

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_type_prefix = re.compile(r'^\b\S+\.?', re.IGNORECASE)

expected_prefix = ["Clos", "Route", "Avenue", "Chemin", "Rue", "Boulevard", "Cours", "Quai", "Rampe", "Promenade", "Place", "Ruelle", "Terrasse", "Rond-point", "Passage", "Galerie", "Carrefour", "Plateau", "Square", "Parc"]

mapping_prefix = {
            "rue": "Rue",
            "Blvd." : "Boulevard",
            "clos" : "Clos",
            "rte" : "Route",
            "ave" : "Avenue"}

def audit_street_type(street_types, street_name):
    m = street_type_prefix.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected_prefix:
            street_types[street_type].add(street_name)
        
def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v) 

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
    

# tag attrib as the street name

def audit(osmfile):
    osm_file=open(osmfile, "r")
    street_types = defaultdict(set)
    street_names = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    street_names.add(tag.attrib['v'])
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()

def update_name(name):

    m = street_type_prefix.search(name)
    better_name = name
    
    if m:
        if m.group() in mapping_prefix:
            better_street_type = mapping_prefix[m.group()]
            better_name = street_type_prefix.sub(better_street_type, name)
    better_name = re.sub("-", " ", better_name)
    better_name = re.sub(r"\s+", " ", better_name, flags=re.UNICODE)
    better_name = string.capwords(better_name)

    return better_name


def test():
    st_types = audit(osm_file)
    pprint.pprint(dict(st_types))
    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name)
            print name, "->", better_name
    
    
if __name__ == '__main__':
    test()
    