# A helper to get a list of available modules
# Probably need to encapsulate this into measurements/__init__.py

import measurements
import inspect

available_workers = [obj for name, obj in inspect.getmembers(measurements) if inspect.isclass(obj)]

