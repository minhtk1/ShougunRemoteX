from importlib import import_module as _im
_m = _im('third_party.xpra_client.client.base.fileprint')
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith('_')})

