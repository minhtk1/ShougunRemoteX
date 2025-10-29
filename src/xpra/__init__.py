# Wrapper package mapping `xpra` to vendored `third_party.xpra_client`.
from importlib import import_module as _im

_base = _im('third_party.xpra_client')
globals().update({k: getattr(_base, k) for k in dir(_base)})
