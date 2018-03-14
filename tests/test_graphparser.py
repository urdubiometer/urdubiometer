#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `graphparser` sub-level package."""

import pytest
import yaml

import urdubiometer
from urdubiometer import GraphParser
import urdubiometer.graphparser
from urdubiometer.graphparser import (validate, process, ParserRule,
                                      ParserOutput, OnMatchRule,
                                      Whitespace, DirectedGraph, initialize)

yaml_for_test = """
tokens:
  a: [token, class1]
  b: [token, class2]
  u: [token]
  ' ': [wb]
rules:
  a: A
  b: B
  <wb> u: \N{DEVANAGARI LETTER U}
onmatch_rules:
  -
    <class1> + <class2>: ","
  -
    <class1> + <token>: \N{DEVANAGARI SIGN VIRAMA}
whitespace:
  default: ' '
  token_class: 'wb'
  consolidate: true
"""


def test_fail():
    good_yaml = """
      tokens:
        a: [class1]
        ' ': [wb]
      rules:
        a: A
      whitespace:
        default: ' '
        consolidate: true
        token_class: wb
    """
    assert GraphParser.from_yaml(good_yaml)
    bad_yaml = """
      tokens:
        a: class1
        ' ': wb
      rules:
        a: A
      whitespace:
        default: ' '
        consolidate: true
        token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)

    bad_yaml = """
          rules:
            a: A
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)
    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)
    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          rules:
            a: A
    """
    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          rules:
            b: A
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)

    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          rules:
            (b) a: A
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)

    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          rules:
            a (b): A
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)

    bad_yaml = """
          tokens:
            a: [class1]
            ' ': [wb]
          rules:
            a <class_nonexisting>: A
          whitespace:
            default: ' '
            consolidate: true
            token_class: wb
    """
    with pytest.raises(ValueError):
        GraphParser.from_yaml(bad_yaml)


def test_graphparser_process():
    data = yaml.load(yaml_for_test)

    assert process._process_rules({'a': 'A'})[0]['tokens'] == ['a']
    assert process._process_rules({'a': 'A'})[0]['production'] == 'A'
    assert process._process_onmatch_rules(
        data['onmatch_rules'])[0]['prev_classes'][0] == 'class1'
    assert process._process_onmatch_rules(
        data['onmatch_rules'])[0]['next_classes'][0] == 'class2'


def test_graphparser_initialize():
    rule = {'prev_classes': None,
            'next_classes': None,
            'tokens': ['a']}
    assert initialize._cost_of(rule) == initialize._COST_OF_EXACT_TOKEN

    rule = {'prev_classes': None,
            'next_classes': None,
            'tokens': ['a', 'b']}

    assert initialize._cost_of(rule) == initialize._COST_OF_EXACT_TOKEN*2

    rule = {'prev_classes': ['prevclass'],
            'next_classes': None,
            'tokens': ['a', 'b']}

    assert initialize._cost_of(rule) == \
        initialize._COST_OF_EXACT_TOKEN * 2 + \
        initialize._COST_OF_TOKEN_CLASS

    rule = {'prev_classes': ['prevclass'],
            'next_classes': ['nextclass1', 'nextclass2'],
            'tokens': ['a', 'b']}

    assert initialize._cost_of(rule) == \
        initialize._COST_OF_EXACT_TOKEN * 2 + \
        initialize._COST_OF_TOKEN_CLASS * 3

    rule = {'prev_tokens': ['a'], 'tokens': ['b'], 'next_tokens': ['c']}

    gp = GraphParser.from_yaml(yaml_for_test)

    assert type(gp.rules[0]) == ParserRule
    assert gp.rules[0].cost <= gp.rules[1].cost
    # check length Also


def test_graphparser_tokenizer():
    tokens = {'a': ['class_a'], ' ': ['wb']}
    whitespace = {'default': ' ', 'token_class': 'wb', 'consolidate': True}
    rules = {'a': 'A', ' ': '_'}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}
    gp = GraphParser.from_dict(settings)
    assert gp.tokenize('a ') == [' ', 'a', ' ']
    assert gp.tokenize('a  ') == [' ', 'a', ' ']
    assert gp.tokenize('  a  ') == [' ', 'a', ' ']

    # Try not consolidating whitespace

    whitespace['consolidate'] = False
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}
    gp = GraphParser.from_dict(settings)

    assert gp.tokenize(' a ') == [' ', ' ', 'a', ' ', ' ']
    assert gp.tokenize(' a') == [' ', ' ', 'a', ' ']

    with pytest.raises(ValueError):
        gp.tokenize('Ba')
    with pytest.raises(ValueError):
        gp.tokenize('aB')
    with pytest.raises(ValueError):
        gp.tokenize('')


def test_graphparser_validate():
    validate._validate_raw_settings(yaml.load(yaml_for_test))


def test_graphparser_parse():
    tokens = {'a': ['class_a'],
              ' ': ['wb']}
    whitespace = {'default': ' ',
                  'token_class': 'wb',
                  'consolidate': True}
    rules = {'a': 'A',
             ' ': '_'}
    settings = {'tokens': tokens,
                'rules': rules,
                'whitespace': whitespace}

    gp = GraphParser.from_dict(settings)

    assert gp.tokenize('a') == [' ', 'a', ' ']
    assert gp.parse('a') == 'A'
    assert gp.tokenize('aa') == [' ', 'a', 'a', ' ']
    assert gp.parse('aa') == 'AA'

    # test prev_tokens

    rules = {'a': 'A', ' ': '_', '(a) a': 'a'}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}
    gp = GraphParser.from_dict(settings)

    assert gp.parse('aa') == 'Aa'
    assert gp.parse('aaa') == 'Aaa'

    # test next_token
    rules = {'a': 'A', ' ': '_', 'a (a)': 'a'}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}
    gp = GraphParser.from_dict(settings)

    assert gp.parse('aa') == 'aA'
    assert gp.parse('aaa') == 'aaA'

    # test prev_classes
    tokens = {'a': ['class_a'],
              'b': ['class_b'],
              ' ': ['wb']}
    rules = {'a': 'a',
             ' ': '_',
             '(<class_a> a) a': 'A',
             'b': 'b',
             '<class_b> b': 'B'}

    whitespace = {'default': ' ', 'token_class': 'wb', 'consolidate': True}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}

    gp = GraphParser.from_dict(settings)

    print(gp.rules)
    assert gp.parse('aaa') == 'aaA'
    assert gp.parse('aaaa') == 'aaAA'
    assert gp.parse('bb') == 'bB'

    # test next_classes

    tokens = {'a': ['class_a'],
              'b': ['class_b'],
              ' ': ['wb']}
    rules = {'a': 'a',
             ' ': '_',
             'a (a <class_a>)': 'A',
             'b': 'b',
             'b <class_b>': 'B'}
    whitespace = {'default': ' ', 'token_class': 'wb', 'consolidate': True}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}

    gp = GraphParser.from_dict(settings)

    print(gp.rules)
    assert gp.parse('aaa') == 'Aaa'
    assert gp.parse('aaaa') == 'AAaa'
    assert gp.parse('aaaa') == 'AAaa'
    assert gp.parse('bb') == 'Bb'

    # test onmatch

    # test onmatchrules
    YAML = """
    tokens:
      a: [class_a]
      b: [class_b]
      " ": [wb]
    rules:
      a: A
      b: B
    onmatch_rules:
      -
        <class_a> <class_b> + <class_a>: "!"
      -
        <class_a> + <class_b>: ","
      -
        <wb> + <class_a> <class_b> <class_a>: "$"
    whitespace:
      default: ' '
      consolidate: True
      token_class: wb
    """
    gp = urdubiometer.GraphParser.from_yaml(YAML)
    assert gp.parse('ab') == 'A,B'
    assert gp.parse('aba') == '$A,B!A'


def test_graphparser(tmpdir):

    yaml_str = """
    tokens:
      a: [token, class1]
      b: [token, class2]
      u: [token]
      ' ': [wb]
    rules:
      a: A
      b: B
      <wb> u: \N{DEVANAGARI LETTER U}
    onmatch_rules:
      -
        <class1> + <class2>: ","
      -
        <class1> + <token>: \N{DEVANAGARI SIGN VIRAMA}
    whitespace:
      default: ' '
      token_class: 'wb'
      consolidate: true
    """

    input_dict = yaml.load(yaml_str)

    assert 'a' in GraphParser.from_dict(input_dict).tokens.keys()
    assert GraphParser.from_dict(input_dict).onmatch_rules[0].production == ','
    gp = GraphParser.from_dict(input_dict)
    assert gp.tokens
    assert gp.rules
    assert gp.whitespace
    assert gp.whitespace.default
    assert gp.whitespace.token_class
    assert gp.whitespace.consolidate

    yaml_file = tmpdir.join("yaml_test.yaml")
    yaml_filename = str(yaml_file)
    yaml_file.write(yaml_str)

    assert yaml_file.read() == yaml_str

    assert GraphParser.from_yaml_file(yaml_filename)

    assert len(set(GraphParser.from_dict(input_dict).tokens)) == 4

    assert GraphParser.from_yaml(yaml_str).parse("ab") == 'A,B'
    assert GraphParser.from_yaml_file(yaml_filename).parse('ab') == 'A,B'
    assert GraphParser.from_dict(
        {'tokens': {'a': ['class_a'], 'b': ['class_b'], ' ': ['wb']},
         'onmatch_rules': [{'<class_a> + <class_b>': ','}],
         'whitespace': {'default': ' ',
                        'token_class': 'wb',
                        'consolidate': True},
         'rules': {'a': 'A', 'b': 'B'}
        },
        raw=True
    ).parse("ab") == 'A,B'


def test_graphparser_types():
    pr = ParserRule(production='A',
                    prev_classes=None,
                    prev_tokens=None,
                    tokens=['a'],
                    next_tokens=None,
                    next_classes=None,
                    cost=1)
    assert pr.cost == 1
    assert ParserOutput([pr], 'A').output == 'A'
    assert OnMatchRule(prev_classes=['class1'],
                       next_classes=['class2'],
                       production=',')
    assert Whitespace(default=' ',
                      token_class='wb',
                      consolidate=False)

    graph = DirectedGraph()

    assert len(graph.node) == 0
    assert len(graph.edge) == 0

    graph.add_node({"type": "test1"})
    graph.add_node({"type": "test2"})
    assert graph.node[0]['type'] == 'test1'
    assert graph.node[1]['type'] == 'test2'

    graph.add_edge(0, 1, {"type": "edge_test1"})
    assert graph.edge[0][1]['type'] == 'edge_test1'
    # add networkx export test?


def test_graphparser_graph():
    tokens = {'ab': ['class_ab'], ' ': ['wb']}
    whitespace = {'default': ' ', 'token_class': 'wb', 'consolidate': True}
    rules = {'ab': 'AB', ' ': '_'}
    settings = {'tokens': tokens, 'rules': rules, 'whitespace': whitespace}

    gp = urdubiometer.GraphParser.from_dict(settings)
    assert gp._graph
    assert gp._graph.node[0]['type'] == 'root'  # test for root
