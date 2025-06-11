import json
import re
import argparse

# Map of common abbreviations to full names
ABBREVIATIONS = {
	"ALY": "Alley",
	"AVE": "Avenue",
	"BLF": "Bluff",
	"BLVD": "Boulevard",
	"CIR": "Circle",
	"CT": "Court",
	"CV": "Cove",
	"DR": "Drive",
	"EXT": "Extension",
	"GLN": "Glen",
	"GRN": "Green",
	"LN": "Lane",
	"LNDG": "Landing",
	"PARK": "Park",
	"PATH": "Path",
	"PIKE": "Pike",
	"PKWY": "Parkway",
	"PL": "Place",
	"PT": "Point",
	"RDG": "Ridge",
	"RD": "Road",
	"RUN": "Run",
	"SQ": "Square",
	"ST": "Street",
	"TER": "Terrace",
	"TRCE": "Trace",
	"TRL": "Trail",
	"VW": "View",
	"WALK": "Walk",
	"WAY": "Way",
	"XING": "Crossing",
	"N": "North",
	"S": "South",
	"E": "East",
	"W": "West",
	"NB": "North",
	"SB": "South",
	"EB": "East",
	"WB": "West",
	"SR": "State Route",
	"US": "US",
	"I": "Interstate",
	"<Null>": ""
}

# Keys to remove after transform
keys_to_remove = ["ADDRESS", "ZONE_", "EDITS", "ADDR_NO", "STREETNAME", "ZIPCODE", "X", "Y", "CITY", "ADDR_ID", "ROAD_ID", "WATER_ID", "SEWER_ID", "ESN", "LSN", "FIRE_ID", "POLICE_ID", "GlobalID", "UNIT", "STR_DIR", "PRE_DIR", "PRE_TYPE", "STR_TYPE"]

def expand_abbreviations(name):
    # Use regex to replace only whole words that match the abbreviations
    words = name.split()
    expanded = [
        ABBREVIATIONS.get(word.strip('.'), word)  # handle both "St" and "St."
        for word in words
    ]
    return " ".join(expanded)

def to_mixed_case(name):
	exceptions = {"US"}
	words = name.split()
	result = []
	for word in words:
		if word.upper() in exceptions:
			result.append(word.upper())
		else:
			result.append(word.capitalize())
	return " ".join(result)
	
def clean_string(value):
    return value.replace("~", "-").replace(" ", "")
	
def split_letter_number(s):
	return re.sub(r"([A-Za-z])(\d+)", r"\1 \2", s)

# Load GeoJSON
parser = argparse.ArgumentParser()
parser.add_argument('input', help='Input geojson file')
parser.add_argument('--output', default='output.geojson', help='Output geojson file')
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    data = json.load(f)

# Translate to OSM standard tags
for feature in data.get("features", []):
	props = feature.get("properties", {})
	if "ADDR_NO" in props:
		value = props["ADDR_NO"]
		if isinstance(value, str):
			housenumber = round(float(value))
			if housenumber > 0:
				props["addr:housenumber"] = housenumber

	if "PRE_DIR" in props:
		value = props["PRE_DIR"]
		if isinstance(value, str):
			pre_dir = expand_abbreviations(value)
			props["PRE_DIR"] = pre_dir
	else:
		pre_dir = ""

	if "PRE_TYPE" in props:
		value = props["PRE_TYPE"]
		if isinstance(value, str):
			pre_type = expand_abbreviations(value)
			props["PRE_TYPE"] = pre_type
	else:
		pre_type = ""

	if "STREETNAME" in props:
		value = props["STREETNAME"]
		if isinstance(value, str):
			# Interstates 
			if re.match(r"^I\d+\s.*", value):
				streetname = expand_abbreviations(split_letter_number(value))
			elif re.match(r"^SR\s\d.*", value):
				streetname = expand_abbreviations(value)
			else:
				streetname = to_mixed_case(value)
			

	else:
		streetname = ""

	if "STR_TYPE" in props:
		value = props["STR_TYPE"]
		if isinstance(value, str):
			str_type = expand_abbreviations(value)
			props["STR_TYPE"] = str_type
	else:
		str_type = ""

	if streetname != "":
		street_parts = [pre_dir, pre_type, streetname, str_type]
		full_street = " ".join(part for part in street_parts if part)
		props["addr:street"] = full_street

	if "UNIT" in props:
		unit = props["UNIT"]
		props["addr:unit"] = clean_string(unit)

	if "CITY" in props:
		value = props["CITY"]
		if isinstance(value, str):
			city = to_mixed_case(value)
			props["addr:city"] = city

	props["addr:state"] = "OH"

	if "ZIPCODE" in props:
		postcode = props["ZIPCODE"]
		if float(postcode) > 0:
			props["addr:postcode"] = postcode	
	props["addr:country"] = "US"

	for key in keys_to_remove:
		props.pop(key, None)	
	
# Save corrected GeoJSON
with open(args.output, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
