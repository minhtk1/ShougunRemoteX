# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-minhtk/xpra/util/pysystem.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

from importlib import import_module as _im
_m = _im('third_party.xpra_client.util.pysystem')
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith('_')})

