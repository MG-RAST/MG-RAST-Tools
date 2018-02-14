import os
auth_file = os.path.join(os.path.expanduser('~'), ".mgrast_auth")
VERSION = '1'
API_URL = "https://api.mg-rast.org/"+VERSION
SHOCK_URL = "http://shock.metagenomics.anl.gov"
AUTH_LIST = "Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke"
SEARCH_FIELDS = ["function", "organism", "md5", "name", "metadata", "biome", "feature", "material", "country", "location", "longitude", "latitude", "created", "env_package_type", "project_id", "project_name", "PI_firstname", "PI_lastname", "sequence_type", "seq_method", "collection_date"]

