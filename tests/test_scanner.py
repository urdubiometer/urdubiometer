# -*- coding: utf-8 -*-

"""Tests for `urdubiometer/scanner.py`."""

import pytest

import yaml
# from urdubiometer import GraphTransliterator
from urdubiometer.scanner import Scanner
from urdubiometer import DefaultScanner
from graphtransliterator import GraphTransliterator
# import urdubiometer.scanner.default
from urdubiometer.scanner.initialize import (
    _regex_to_postfix, _postfix_to_ndfa,
    _minimized_graph_of_meter
)


def test_minimized_graph_of_meter():
    minimized_graph = _minimized_graph_of_meter("===(-)")
    assert minimized_graph
    assert minimized_graph.node == \
        [{'type': '0'}, {'type': '='}, {'type': '='}, {'type': '='},
         {'type': '-'}, {'type': 'Accepting'}]
    assert _minimized_graph_of_meter('(-|=)==(=|-)')


def test_validator():
    """Test validator."""
    transcriptionYAML_ok = r"""
    whitespace:
        token_class: wb
        default: ' '
        consolidate: True
    tokens:
        a: [short_vowel]
        b: [consonant]
        aa: [long_vowel]
        ' ': [wb]
        '\t': [wb]
    rules:
        a: s
        b: c
        aa: l
        ' ': b
    """

    transcriptionYAML_bad = r"""
    whitespace:
        token_class: wb
        default: ' '
        consolidate: True
    tokens:
        a: [short_vowel]
        b: [consonant]
        aa: [long_vowel]
        ' ': [wb]
        '\t': [wb]
    rules:
        a: s
        b: c
        aa: X
    """

    shortYAML_ok = r"""
    whitespace:
        token_class: wb
        default: 'b'
        consolidate: True
    tokens:
        b: [wb]
        s: [short_vowel]
        c: [consonant]
        l: [long_vowel]
    rules:
        c: s<c>
        b c s: s<bcs>
        (l) c (b): s<(l)c(b)>
        (c) c (b): s<(c)c(b)>
        b c l (b): s<bcl(b)>
        c l (b): s<cl(b)>
    """

    shortYAML_bad = r"""
    whitespace:
        token_class: wb
        default: 'b'
        consolidate: True
    tokens:
        b: [wb]
        s: [short_vowel]
        c: [consonant]
        l: [long_vowel]
        X: [extra bad token]
    rules:
        b c s: s<bcs>
        (l) c (b): s<(l)c(b)>
        (c) c (b): s<(c)c(b)>
        b c l (b): s<bcl(b)>
        c l (b): s<cl(b)>
    """

    longYAML_ok = r"""
    whitespace:
        token_class: wb
        default: 'b'
        consolidate: True
    tokens:
        b: [wb]
        s: [short_vowel]
        c: [consonant]
        l: [long_vowel]
    rules:
        b c l: l<bcl>
        c l: l<cl>
    """

    longYAML_bad = r"""
    whitespace:
        token_class: wb
        default: 'b'
        consolidate: True
    tokens:
        b: [wb]
        s: [short_vowel]
        c: [consonant]
        l: [long_vowel]
        X: [extra bad token]
    rules:
        b c l: l<bcl>
        c l: l<cl>
    """
    constraints = None
    # yaml.safe_load("""
    #     "-":
    #         "-":
    #             "<bcss>": [s<c>]
    # """)

    constraints_bad = {'bad': 'constraints'}

    meters_list = yaml.safe_load("""
    -
      id : 1
      regex_pattern : ===(-)
      name : three longs and maybe a short
    -
      id : 2
      regex_pattern : (-|=)==(=|-)
      name : a long or short, two longs, and a long or short
    -
      id : 2
      regex_pattern : (=-=|===)+==(=|-)
      name : meter with cycles
    """)
    meters_list_bad = {"bad": "meters_list"}

    transcription_parser_ok = GraphTransliterator.from_yaml(
        transcriptionYAML_ok
    )
    long_parser_ok = GraphTransliterator.from_yaml(longYAML_ok)
    short_parser_ok = GraphTransliterator.from_yaml(shortYAML_ok)

    transcription_parser_bad = GraphTransliterator.from_yaml(
        transcriptionYAML_bad
    )
    long_parser_bad = GraphTransliterator.from_yaml(longYAML_bad)
    short_parser_bad = GraphTransliterator.from_yaml(shortYAML_bad)

    assert Scanner(transcription_parser_ok, long_parser_ok, short_parser_ok,
                   constraints, meters_list)

    with pytest.raises(ValueError):
        Scanner(transcription_parser_ok, long_parser_bad, short_parser_ok,
                constraints,
                meters_list)

    with pytest.raises(ValueError):
        Scanner(transcription_parser_ok, long_parser_ok, short_parser_bad,
                constraints,
                meters_list)

    with pytest.raises(ValueError):
        Scanner(transcription_parser_bad, long_parser_ok, short_parser_ok,
                constraints, meters_list)
    # test bad constraints
    with pytest.raises(ValueError):
        Scanner(transcription_parser_ok, long_parser_ok, short_parser_ok,
                constraints_bad, meters_list)
    # test bad meters_list
    with pytest.raises(ValueError):
        Scanner(transcription_parser_ok, long_parser_ok, short_parser_ok,
                constraints, meters_list_bad)


def test_regex_to_postfix():
    """Test regex to postfix conversion (with concatenation)."""
    assert _regex_to_postfix('abc') == "ab.c."
    assert _regex_to_postfix("ab|c") == "ab.c|"
    assert _regex_to_postfix("ab+c") == "ab+.c."
    assert _regex_to_postfix("a(bb)+c") == "abb.+.c."
    assert _regex_to_postfix("a(bb)*c") == "abb.*.c."
    with pytest.raises(ValueError):
        _regex_to_postfix("")
    with pytest.raises(ValueError):
        _regex_to_postfix("|a")
    with pytest.raises(ValueError):
        _regex_to_postfix(")a(")


def test_postfix_to_ndfa():
    """Test postfix to ndfa (with concatenation)."""
    for regex in ('abc', 'ab|c', 'ab+c', 'a(bb)+c', 'a(bb)*c'):
        postfix = _regex_to_postfix(regex)
        assert _postfix_to_ndfa(postfix)


# def test_regex_to_ndfa():
#     """Test conversion of regex into NDFA."""
#     postfix = _regex_to_postfix('0(a|b)')
#     assert postfix == '0ab|.'
#     ndfa = _postfix_to_ndfa(postfix)
#     assert ndfa.node ==  \
#         {0: {'type': '0'},
#          1: {'type': 'a'},
#          2: {'type': 'b'},
#          3: {'type': 'Split'},
#          4: {'type': 'Accepting'}}
#     assert ndfa.edge == \
#         {0: {3: {}}, 1: {4: {}}, 2: {4: {}}, 3: {1: {}, 2: {}}}

#
# def test_minimize_ndfa():
#     """Test minimization of NDFA into directed graph."""
#     postfix = _regex_to_postfix('0(a|b|c)')
#     assert postfix == '0abc||.'
#     ndfa = _postfix_to_ndfa(postfix)
#     assert ndfa.node ==  \
#         {0: {'type': '0'},
#          1: {'type': 'a'},
#          2: {'type': 'b'},
#          3: {'type': 'c'},
#          4: {'type': 'Split'},
#          5: {'type': 'Split'},
#          6: {'type': 'Accepting'}}
#     assert ndfa.edge == \
#         {0: {5: {}},
#          1: {6: {}},
#          2: {6: {}},
#          3: {6: {}},
#          4: {2: {}, 3: {}},
#          5: {1: {}, 4: {}}}
#     minimized = _minimize_ndfa(ndfa)
#     assert minimized.node == \
#         {0: {'type': '0'},
#          1: {'type': 'a'},
#          2: {'type': 'b'},
#          3: {'type': 'c'},
#          4: {'type': 'Accepting'}}
#     assert minimized.edge == \
#         {0: {1: {}, 2: {}, 3: {}}, 1: {4: {}}, 2: {4: {}}, 3: {4: {}}}


def test_constraints():
    """Test constraints."""
    transcription_parser = GraphTransliterator.from_yaml(
        """
            whitespace:
                token_class: wb
                default: ' '
                consolidate: True
            tokens:
                A: []
                ' ': [wb]
            rules:
                A: "a"
                ' ': "b"
        """
    )
    short_parser = GraphTransliterator.from_yaml(
        """
        whitespace:
            token_class: wb
            default: 'b'
            consolidate: True
        tokens:
            a: []
            b: [wb]
        rules:
            b a: s<ba>
            a: s<a>
        """
    )
    long_parser = GraphTransliterator.from_yaml(
        """
        whitespace:
            token_class: wb
            default: 'b'
            consolidate: True
        tokens:
            a: []
            b: [wb]
        rules:
            b a a: "l<baa>"
            a a: "l<aa>"
        """
    )
    constraints = yaml.safe_load(
        """
        '-':
            '-':
                's<a>': [s<ba>, s<a>]
        """  # cannot have s<ba> s<a>; it must be long
    )
    meters_list = yaml.safe_load(
        """
        -
          id: 1
          name: long long
          regex_pattern: "=="
        -
          id: 2
          name: short short long
          notes: should not be possible due to constraints
          regex_pattern: "--="
        """
    )

    scanner = Scanner(transcription_parser,
                      long_parser,
                      short_parser,
                      constraints,
                      meters_list)

    assert scanner._constrained_parsers['-']['-']['s<a>']._graph.node[0] == \
        {'ordered_children': {}, 'type': 'Start'}


def test_scanner():
    """Test scanner."""
    scanner = DefaultScanner()
    assert scanner.scan("naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa")
    # test first_only
    scanner._post_scan_filter = None  # remove filter
    assert len(scanner.scan('ja;zbah-e be-i;xtiyaar-e shauq dekhaa chaahiye',
                            show_feet=True, first_only=True)) == 1
    # test graph_details
    _scan = scanner.scan('ja;zbah-e be-i;xtiyaar-e shauq dekhaa chaahiye',
                         graph_details=True)
    assert _scan[0].matches[0].node_key >= 0
    assert _scan[0].matches[0].parent_key >= 0
    # test show_feet
    assert scanner.scan("naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa",
                        show_feet=True)[0].scan == '=-==/=-==/=-==/=-='
    assert scanner.translation_graph


def test_transcribe():
    """Test transcribe."""
    scanner = DefaultScanner()
    assert scanner.transcribe('shaa') == 'cv'


def test_default_scanner_filter_scans():
    """Test scanner.default.filter_scans()."""

    scanner = DefaultScanner()
    scanner.scan("buu-e gul naalah-e dil duud-e chiraa;g-e ma;hfil")
    # scanner._post_scan_filter = None # turn off filters
    # scans = scanner.scan('buu-e gul naalah-e dil duud-e chiraa;g-e ma;hfil')
    # assert len(scans) == 2
    # assert scans[0].meter_key == scans[1].meter_key
    # assert len(urdubiometer.scanner.default.filter_scans(scans)) == 1
