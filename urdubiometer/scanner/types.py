# -*- coding: utf-8 -*-
"""Internal classes used by Scanner."""


from collections import namedtuple


ScanIteration = namedtuple(
    'ScanIteration',
    ["node_key",
     "parent_key",
     "token_i",
     "matches",
     "matched_so_far"])


NodeMatch = namedtuple(
    'NodeMatch',
    ["type",       # =, -, or _
     "matched_tokens",  # tokens matched
     "node_key",        # id of node in graph
     "orig_tokens",     # original tokens that were matched
     "rule_found",      # name of rule found (production of parser)
     "token_i",         # used for matches at nodes in graph
     "parent_key"]     # key of parent node in graph
)


class UnitMatch(namedtuple('UnitMatch',
                           ["type",
                            "rule_found",
                            "orig_tokens"])):
    """
    Class for metrical unit match of Scanner.

    Contains both the type of metrical unit (= for long, - for short, _ for
    optional, uncounted short); the name of the rule found, and the original
    tokens matched.

    Parameters and Attributes
    -------------------------
    type: str
        Type of unit found; = for long, - for short, and _ for uncounted short
    rule_found: str
        Name of rule found
    orig_tokens: list of str
        Original tokens matching this metrical unit
    """
    __slots__ = ()


class ScanResult(namedtuple('ScanResult',
                            ["scan",
                             "matches",
                             "meter_key"])):
    """
    Class for scan results of Scanner

    Contains the scan as a string, the list of matches (usually NodeMatch),
    and the meter key.

    Parameters and Attributes
    -------------------------
    scan: str
        String representation of the meter found, e.g. =-===-===-=
    matches: list of NodeMatch (or UnitMatch)
        List of individual metrical units found, either as NodeMatch or
        the more detailed NodeMatch
    meter_key: int
        Key to the meter identified

    # TODO: Check if meter_key is in fact an int
    """
    __slots__ = ()


Constraint = namedtuple(
    'Constraint',
    ["prev_node",
     "next_node",
     "prev_token",
     "next_token"]
)
