# -*- coding: utf-8 -*-
"""Internal classes used by GraphParser.

"""


from collections import namedtuple


# ---------- parser rule ----------


class ParserRule(namedtuple('ParserRule', ['production',
                                           'prev_classes',
                                           'prev_tokens',
                                           'tokens',
                                           'next_tokens',
                                           'next_classes',
                                           'cost'])):
    """
    Class for GraphParser rule

    Contains both the production (output) and the specific conditions that
    must be matched.

    Parameters and Attributes
    -------------------------
    production: str
        Output from the `ParserRule`
    prev_classes: list of str
        List of previous token classes to be matched before `tokens` or,
        if they exist, `prev_tokens`
    prev_tokens: list of str
        List of tokens to be matched before `tokens`
    tokens: list of str
        list of tokens to match
    next_tokens: list of str
        list of tokens to match after `tokens`
    next_classes: list of str
        List of tokens to match after `tokens` or, if they exist, `next_tokens`
    cost: int
        Cost of the rule, where less specific rules are more costly.
    """

    __slots__ = ()


# ---------- parser output ----------


class ParserOutput(namedtuple('ParserOutput', ['matches',
                                               'output'])):

    """ Class for GraphParser output

    Contains both the specific matches and the final output

    Parameters and Attributes
    -------------------------
    matches: list of ParserRule
        List of the parser rule matches
    output: str
        Final output of the parser
    """
    __slots__ = ()


# ---------- on match rule ----------


class OnMatchRule(namedtuple('OnMatchRule', ['prev_classes',
                                             'next_classes',
                                             'production'])):

    """ Class for rules about adding text between certain combinations.

    The `production` of an `OnMatchRule` is added before the `production`
    of a particular `ParserRule`, if the classes of the previous and following
    tokens in the output string match `prev_class` and `next_class`.

    Parameters and Attributes
    -------------------------
    prev_classes: list of str
        List of previous token classes
    next_classes: list of str
        List of next token classes
    production: str
        Text to add before a match between prev_classes and next_classes
    """
    __slots__ = ()


# ---------- whitespace ----------


class Whitespace(namedtuple('Whitespace', ['default',
                                           'token_class',
                                           'consolidate'])):
    """ Class for whitespace settings of parser.

    Whitespace should often be ignored by a metrical parser, and these settings
    allow that to happen. As many rules depend on preceding or following
    whitespace characters, the default whitespace is appended to the start and
    end of input to `GraphParser`, if a whitespace character is not already
    present.

    Parameters and Attributes
    -------------------------
    default: str
        Default whitespace token
    token_class: str
        Whitespace token class. (Can be extended to punctuation, spaces, etc.)
    consolidate: boolean
        Consecutive whitespace characters are consolidated and rendered as
        the whitespace `default`
    """
    __slots__ = ()


# ---------- directed graph ----------


class DirectedGraph:
    """
    A very basic dictionary-based directed graph.

    Notes
    -----
    I have aspirations of automatically converting this code to Javascript,
    hence the use of dict.

    Attributes
    ----------
    node : dict
        Dictionary for node attributes. Nodes are integers and zero-indexed.
    edge : dict of dict
        Mapping from start to end nodes, which hold a dict of values
    edge_list : list of tuple of int
        Start followed by end node of each edge
"""

    __slots__ = 'edge', 'node', 'edge_list'

    def __init__(self):

        self.edge = {}
        self.node = {}
        self.edge_list = []

    def add_edge(self, start, end, edge_data={}):
        """ Returns dict """

        assert type(edge_data) == dict, "Edge data must be a dict."
        assert start in self.node, "Start node not in graph."
        assert end in self.node, "End node not in graph."

        if start not in self.edge:
            self.edge[start] = {}

        self.edge[start][end] = edge_data
        self.edge_list.append(tuple([start, end]))

        return self.edge[start][end]

    def add_node(self, node_data={}):
        """ Creates node and returns (int, dict) of node key and object."""

        assert type(node_data) == dict, "Node data must be a dict."

        node_key = len(self.node)
        self.node[node_key] = node_data
        return node_key, self.node[node_key]
