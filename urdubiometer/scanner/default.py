# -*- coding: utf-8 -*-
"""
Default metrical scanner, for Urdu ghazal.

Loads from urdubiometer/settings.
"""

from collections import defaultdict
from copy import deepcopy
import pkg_resources
import yaml

from urdubiometer.scanner import Scanner
from graphtransliterator import GraphTransliterator


transcription_filename = pkg_resources.resource_filename(
    "urdubiometer", "settings/transcription.yml"
)
long_parser_filename = pkg_resources.resource_filename(
    "urdubiometer", "settings/long.yml"
)
short_parser_filename = pkg_resources.resource_filename(
    "urdubiometer", "settings/short.yml"
)

constraints_filename = pkg_resources.resource_filename(
    "urdubiometer", "settings/constraints.yml"
)
meters_filename = pkg_resources.resource_filename(
    "urdubiometer", "settings/ghazal_meters.yml"
)


def _load_yaml(yaml_filename):
    with open(yaml_filename, "r") as f:
        return yaml.safe_load(f.read())


_COST_OF = {"-": 20, "=": 10, "_": 20}


def filter_scans(scans):
    """Remove worst of scans mapping to same meter."""

    def cost_of(x):
        cost = 0
        for _ in scans[x].scan:
            cost += _COST_OF[_]
        return cost

    if not scans or len(scans) < 2:
        return scans

    meters_found = defaultdict(list)
    for scan_key, _ in enumerate(scans):
        meters_found[_.meter_key].append(scan_key)

    scans = deepcopy(scans)

    for meter_key, scan_keys in meters_found.items():
        if len(scan_keys) < 2:
            continue
        else:
            _, min_idx = min((cost_of(val), idx) for (idx, val) in enumerate(scan_keys))
        for _ in scan_keys:
            if _ != min_idx:
                scans[_] = None

    scans = [_ for _ in scans if _ is not None]
    return scans


def _gen_possible_feet(meters_list):
    """Generate possible feet from a meters list."""

    withfeet = [_["fp7pattern"].replace(" ", "") for _ in meters_list]
    poss_feet = []
    for _ in withfeet:
        if "*" in _:
            poss_feet.append("=" + _[2:])
            poss_feet.append("=" + _[2:] + "_")
            poss_feet.append("-" + _[2:] + "_")
            assert "//" not in _
        elif "//" in _:
            loc = _.index("//")
            poss_feet.append(_)
            poss_feet.append(_ + "_")
            poss_feet.append(_[0:loc] + "_" + _[loc:])
        else:
            poss_feet.append(_)
            poss_feet.append(_ + "_")
    scans_with_feet = {_.replace("/", ""): _ for _ in poss_feet}
    return scans_with_feet


class DefaultScanner(Scanner):
    """Default scanner for Urdu ghazal (without Mir's meter).

    Loads meters list from Pritchett.

    Parameters
    ----------
    meters_list: : dict or None
    meters_filter : :class:`function` or None
        filter returning subsection of scanner's meter list
    """

    def find_feet(self, scan):
        """str: Finds feet based on a scan."""
        return self._scans_with_feet[scan]

    def __init__(self, meters_list=None, find_feet=None, meters_filter=None):
        if not meters_list:
            meters_list = _load_yaml(meters_filename)
            self._scans_with_feet = _gen_possible_feet(meters_list)
            find_feet = self.find_feet
        if meters_filter:
            meters_list = meters_filter(meters_list)
        Scanner.__init__(
            self,
            GraphTransliterator.from_yaml_file(transcription_filename),
            GraphTransliterator.from_yaml_file(long_parser_filename),
            GraphTransliterator.from_yaml_file(short_parser_filename),
            _load_yaml(constraints_filename),
            meters_list,
            find_feet=find_feet,
            post_scan_filter=filter_scans,
        )
