import os
from aqt import mw


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail

addon_path = os.path.dirname(__file__)
addonfoldername = os.path.basename(addon_path)
