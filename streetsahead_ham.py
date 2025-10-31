import json
import re
import argparse

# Map of common abbreviations to full names
ABBREVIATIONS = {
	"ALY": "Alley",
	"AVE": "Avenue",
	"AV": "Avenue",
	"BLF": "Bluff",
	"BLVD": "Boulevard",
	"CIR": "Circle",
	"CT": "Court",
	"CV": "Cove",
	"CRSC": "Crescent",
	"CLSE": "Close",
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
	"WY": "Way",
	"XING": "Crossing",
	"N": "North",
	"S": "South",
	"E": "East",
	"W": "West",
	"NB": "North",
	"SB": "South",
	"EB": "East",
	"WB": "West",
	"Nb": "North",
	"Sb": "South",
	"Eb": "East",
	"Wb": "West",
	"SR": "State Route",
	"US": "US",
	"I": "Interstate",
	"EXWY": "Expressway",
	"<Null>": ""
}

# Keys to remove after transform
# keys_to_remove = ["ABSSIDE", "ALSN", "ALTNAME", "COMM", "COMMENT", "COUNTY","DATEMODIFI","FEATUREID","FIPSCODE", "FLOOR", "HNUM","LHN","LSN","MPVAL", "MUNI", "NLFIDNEW","PT_LEN","ROADNUMBER","ROADTYPE","SEGID","SIDE","SOURCE","ST_NAME","ST_PREFIX", "ST_SUFFIX", "ST_TYPE","STATE","STRUC_TYPE","TSSEGID","UNITNUM","USPS_CITY","X","Y","ZIPCODE"]
keys_to_remove = ["HNUM", "CAGDIR", "CAGSTRNAME", "CAGSFX", "STATE", "ZIPCODE", "COUNTYCODE", "LATITUDE", "LONGITUDE", "X_COORD", "Y_COORD", "ADDRWCITY", "ADDRESS", "JURISPPLUS", "JURISABBRV", "FULLMAILADR", "GLOBALID", "GRPPCLID", "NEARXST", "OBJECTID", "PARCELID", "PARITY", "POSTED", "SEGGEOCODX", "SEGGEOCODY", "SIDEOFSTR", "STATUS", "TANASSETID", "TANCURB_X", "TANCURB_Y", "X_SEGTAN", "Y_SEGTAN", "ORPHANFLG", "HNUMSFX", "UNIT", "LOT"]

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
 
	if "OBJECTID" in props:
		value = props.get("OBJECTID", "")
		count = len([v for v in value.split(";") if v.strip()])
		if count > 1:
			print(count)

	if "HNUM" in props:
		value = props["HNUM"]
		if isinstance(value, str):
			if ";" in value:
				props["addr:housenumber"] = value.replace(";", ",")
				props["notes"] = "Multiple " + str(count)
			else:          			
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

	if "CAGSTRNAME" in props:
		value = props["CAGSTRNAME"]
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
				
	if "CAGDIR" in props:
		value = props["CAGDIR"]
		if isinstance(value, str):
			post_dir = expand_abbreviations(value)
			props["CAGDIR"] = post_dir
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
	
	if "CAGSFX" in props:
		value = props["CAGSFX"]
		if isinstance(value, str):
			str_type = expand_abbreviations(value)
			props["CAGSFX"] = str_type
	else:
		str_type = ""

	if streetname != "":
		street_parts = [pre_dir, pre_type, streetname, post_dir, str_type]
		full_street = " ".join(part for part in street_parts if part)
		props["addr:street"] = full_street

	if "HNUMSFX" in props:
		in_unit = props["HNUMSFX"]
		unit = clean_string(in_unit).replace("#", "")
		try:
			if float(unit) > 0:
				props["addr:unit"] = unit
		except ValueError:
		    props["addr:unit"] = unit
		 
		
	if "UNIT" in props:
		in_unit = props["UNIT"]
		unit = clean_string(in_unit).replace("-", "")
		try:
			if float(unit) > 0:
				props["addr:unit"] = unit
		except ValueError:
		    props["addr:unit"] = unit
		 
	if "FULLMAILADR" in props and "ADDRESS" in props:
		full = props.get("FULLMAILADR", "").strip()
		if ";" in full:
			parts = [p.strip() for p in full.split(";", 1)]
			full = parts[1] if len(parts) > 1 else parts[0]
		address = props.get("ADDRESS", "").strip()
		if ";" in address:
			parts = [p.strip() for p in address.split(";", 1)]
			address = parts[0] if len(parts) > 1 else parts[1]
		# Remove ADDRESS part and clean up
		remaining = full.replace(address, "", 1).strip()
		if ";" in remaining:
			print(remaining)
		# Split on comma
		parts = [p.strip() for p in remaining.split(",")]

		# First part = city/township, second part = state and zip
		city_part = parts[0] if len(parts) > 0 else ""
		statezip = parts[1] if len(parts) > 1 else ""

		# Split state and zip if possible
		statezip_parts = statezip.split()
		state = statezip_parts[0] if len(statezip_parts) > 0 else ""
		zipcode = statezip_parts[1] if len(statezip_parts) > 1 else ""

		# Format and store
		if city_part:
			cleaned = " ".join(word for word in city_part.split() if not word.startswith("#"))
			props["addr:city"] = to_mixed_case(cleaned)
		if state:
			props["addr:state"] = state
		if zipcode:
			props["addr:postcode"] = zipcode
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