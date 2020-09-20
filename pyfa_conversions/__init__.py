"""
This module contains a list of item conversions that need to be done for pyfa,
see https://github.com/pyfa-org/Pyfa

Q.Industrialist uses the conversion in the same way.

Python files were copied unchanged.
Do not change Python files!
Follow the updates of Python files in the Pyfa repository.

Each file in this module must contain a dictionary named CONVERSIONS in the
format of convertFrom: convertTo, with both key and value being a string of the
item's name. The name of the file is usually arbitrary unless it's used in logic
elsewhere (in which case can be accessed with packs[name])
"""


from .pyinst_support import iterNamespace


# init parent dict
all = {}
# init container to store the separate conversion packs in case we need them
# packs = {}

for modName in iterNamespace(__name__, __path__):
    # skip utility module from outhere
    modname_tail = modName.rsplit('.', 1)[-1]
    if modname_tail == "pyinst_support":
        continue
    conversionPack = __import__(modName, fromlist="dummy")
    all.update(conversionPack.CONVERSIONS)
    #packs[modname_tail] = conversionPack.CONVERSIONS
