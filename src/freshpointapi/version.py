from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    API_VERSION = _pkg_version("freshpointapi")
except PackageNotFoundError:  # running from source without an installed dist
    API_VERSION = "0.0.0"
