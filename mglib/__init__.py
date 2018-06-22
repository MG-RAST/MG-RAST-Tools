import os
__all__ = ["mglib"]
try:
    from .mglib.mglib import *
except ImportError:
    from .mglib import *
auth_file = os.path.join(os.path.expanduser('~'), ".mgrast_auth")
VERSION = 1
API_URL = "https://api.mg-rast.org/"
SHOCK_URL = "https://shock.mg-rast.org/"
AUTH_LIST = "Jared Bischof, Travis Harrison, Folker Meyer, Tobias Paczian, Andreas Wilke"
SEARCH_FIELDS = ["name", "investigation_type", "biome", "feature", "material", "continent", "country", "location", "longitude", "latitude", "created_on", "env_package", "project_id", "project_name", "PI_firstname", "PI_lastname", "sequence_type", "seq_meth", "collection_date", "bp_count_raw", "sequence_count_raw", "average_length_raw"]
