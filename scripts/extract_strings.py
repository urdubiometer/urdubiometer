#!/usr/bin/env python3
# -*- coding: utf-8 -*

"""
Script to make sure that all output strings are ready to be translated.
"""

from collections import defaultdict

# from datetime import datetime, timezone
import polib
import re
import yaml

# Read Long and Short Files


def get_rules(yml_filename):
    with open(yml_filename, "r") as f:
        data = yaml.safe_load(f)
    for rule_str, production in data["rules"].items():
        yield rule_str, production


productions = set()
rule_strs_by_production = defaultdict(list)

for filename in ("urdubiometer/settings/long.yml", "urdubiometer/settings/short.yml"):
    for rule_str, production in get_rules(filename):
        productions.add(production)
        rule_strs_by_production[production].append(rule_str)

# load source translation file

po = polib.pofile("translations/urdubiometer.messages/en.po")

# check that each tag has required "<tag>__SHORT_DESCRIPTION"

for _ in sorted(productions):
    for msgid in ("{}__SHORT_DESCRIPTION", "{}__WITH_VALUES_DESCRIPTION"):
        msgid = msgid.format(_)
        if not po.find(msgid):
            comment = " | ".join([r for r in rule_strs_by_production[_]])
        print("Adding", msgid)
        po.append(polib.POEntry(msgid=msgid, msgstr="", comment=comment))

for _ in po:
    msgid = _.msgid
    m = re.match("^(.+)(__SHORT_DESCRIPTION|__WITH_VALUES_DESCRIPTION)", msgid)
    if m:
        assert m.group(1) in productions, "Superfluous translation to be removed."

po.save("translations/urdubiometer.messages/en-new.po")
