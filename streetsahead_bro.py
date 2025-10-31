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
	"RTE": "Route",
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
# keys_to_remove = ["ADDRESS", "ZONE_", "EDITS", "ADDR_NO", "STREETNAME", "ZIPCODE", "X", "Y", "CITY", "ADDR_ID", "ROAD_ID", "WATER_ID", "SEWER_ID", "ESN", "LSN", "FIRE_ID", "POLICE_ID", "GlobalID", "UNIT", "STR_DIR", "PRE_DIR", "PRE_TYPE", "STR_TYPE"]
keys_to_remove = ["ABSSIDE", "ALSN", "ALTNAME", "COMM", "COMMENT", "COUNTY","DATEMODIFI","FEATUREID","FIPSCODE", "FLOOR", "HOUSENUM","LHN","LSN","MPVAL", "MUNI", "NLFIDNEW","PT_LEN","ROADNUMBER","ROADTYPE","SEGID","SIDE","SOURCE","ST_NAME","ST_PREFIX", "ST_SUFFIX", "ST_TYPE","STATE","STRUC_TYPE","TSSEGID","UNITNUM","USPS_CITY","X","Y","ZIPCODE"]

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
	if "HOUSENUM" in props:
		value = props["HOUSENUM"]
		if isinstance(value, str):
			housenumber = round(float(value))
			if housenumber > 0:
				props["addr:housenumber"] = housenumber

	if "ST_PREFIX" in props:
		value = props["ST_PREFIX"]
		if isinstance(value, str):
			pre_dir = expand_abbreviations(value)
			props["ST_PREFIX"] = pre_dir
	else:
		pre_dir = ""

	if "PRE_TYPE" in props:
		value = props["PRE_TYPE"]
		if isinstance(value, str):
			pre_type = expand_abbreviations(value)
			props["PRE_TYPE"] = pre_type
	else:
		pre_type = ""

	if "ST_NAME" in props:
		value = props["ST_NAME"]
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
				
	if "ST_SUFFIX" in props:
		value = props["ST_SUFFIX"]
		if isinstance(value, str):
			post_dir = expand_abbreviations(value)
			props["ST_SUFFIX"] = post_dir
	else:
		post_dir = ""
			
	if "FLOOR" in props:
		floor = str(props["FLOOR"]).strip().upper()

		mapping = {
			"1": 0,
			"2": 1,
			"2ND": 1
		}
		if floor in mapping:
			props["level"] = mapping[floor]
	else:
		floor = ""		
	
	if "ST_TYPE" in props:
		value = props["ST_TYPE"]
		if isinstance(value, str):
			str_type = expand_abbreviations(value)
			props["ST_TYPE"] = str_type
	else:
		str_type = ""

	if streetname != "":
		street_parts = [pre_dir, pre_type, streetname, post_dir, str_type]
		full_street = " ".join(part for part in street_parts if part)
		props["addr:street"] = full_street

	if "UNITNUM" in props:
		unit = props["UNITNUM"]
		props["addr:unit"] = clean_string(unit)

	if "USPS_CITY" in props:
		value = props["USPS_CITY"]
		if isinstance(value, str):
			city = to_mixed_case(value)
			props["addr:city"] = city
	else:
		city = ""
		
		
	if "COMMENT" in props:
		value = props["COMMENT"]
		props["name"] = to_mixed_case(value)

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