# -*- coding: utf-8 -*-

"""GraphParser main module.

GraphParser converts an input string into a new str based on a set of rules.

Internally, it uses patterns of tokens, each of which can be a member of a
series of classes. The Parser can be constructed directly, through a `dict`,
or from a YAML file. The rules match tokens, previous
and following tokens, and also previous or next classes (before
previous/following tokens, if available). The parser returns the most exact
match, with classes considered less valued than tokens. Whitespace must be
carefully labeled by a class, and can be consolidated, e.g. ", " as " ".
"""
import re
import unicodedata
from collections import deque
import yaml

from .validate import _validate_raw_settings, _validate_settings
from .process import _process_settings
from .initialize import (
    _tokens_of, _parser_rule_of, _whitespace_of, _onmatch_rule_of,
    _onmatch_rules_lookup, _tokenizer_from, _graph_from
)


class GraphParser:
    """
    A graph-based parser that converts a string into a new string based on
    patterns of tokens, each of which can be a member of a series of classes.
    The rules can also specify previous tokens, following tokens, and previous
    or next classes (before the previous/following tokens, if specified). The
    parser returns the most exact match, with classes considered less valued
    than tokens. It allows for the insertion of particular strings between
    combinations of specified classes of tokens. It is used throughout Urdu
    BioMeter and can also be used independently.

    Parameters
    ----------
    tokens : dict
        Mappings of tokens to a list or tuple of classes, as str.
    rules : list or tuple of ParserRule
        An ordered list of parser rules as `ParserRule`.
    onmatch_rules: list of OnmatchRule
        An ordered list of onmatch rules as `OnMatchRule`.
    whitespace : dict,
        Settings for whitespace,
        Separator used for word breaks treated as first and last token of
        input string (the default is ' ').
    whitespace_class : str
        Class for whitespace characters, which could include punctuation, e.g.
        "wb" for word break
    consolidate_whitespace: bool
        Should whitespace characters be treated as one character? Useful for
        metrical parsing. If so, they will be replaced by a single instance of
        the whitespace character

    Examples
    --------

    See also
    --------
    GraphParser.from_dict : constructor from a dict
    GraphParser.from_yaml_file : constructor from a yaml file
    GraphParser.from_yaml : constructor from a yaml str
    """

    def __init__(self, tokens, rules, onmatch_rules, whitespace, **kwargs):

        _validate_settings(tokens, rules, onmatch_rules, whitespace)
        self._tokens = _tokens_of(tokens)
        self._rules = sorted([_parser_rule_of(rule) for rule in rules],
                             key=lambda parser_rule: parser_rule.cost)
        self._onmatch_rules = [_onmatch_rule_of(_) for _ in onmatch_rules]
        self._onmatch_rules_lookup = \
            _onmatch_rules_lookup(tokens, self._onmatch_rules)
        self._whitespace = _whitespace_of(whitespace)
        self.__init_parameters__ = {     # used during development
            'tokens': tokens,
            'rules': rules,
            'onmatch_rules': onmatch_rules,
            'whitespace': whitespace,
            'kwargs': kwargs
        }
        self._tokenizer = _tokenizer_from(list(tokens.keys()))
        self._graph = _graph_from(self.rules)

        self._input_tokens = None

    def _match_constraints(self, target_edge, token_i):
        """Match edge constraints.

        Called as a token is consumed. `token_i` is location right
        after a token.
        """

        constraints = target_edge.get('constraints')

        if not constraints:
            return True

        for c_type, c_value in constraints.items():
            if c_type == 'prev_tokens':
                # presume for rule (a) a, with input "aa"
                # ' ', a, a, ' '  start (token_i=3)
                #             ^
                #         ^       -1 subtract token
                #      ^          - len(c_value)
                start_at = token_i
                start_at -= 1
                start_at -= len(c_value)
                if not self._match_tokens(start_at, c_value,
                                         check_prev=True, check_next=False,
                                         by_class=False):
                    return False
            elif c_type == 'next_tokens':
                # presume for rule a (a), with input "aa"
                # ' ', a, a, ' '  start (token_i=2)
                #         ^
                start_at = token_i
                if not self._match_tokens(start_at, c_value,
                                         check_prev=False, check_next=True,
                                         by_class=False):
                    return False

            elif c_type == 'prev_classes':
                # presume for rule (a <class_a>) a, with input "aaa"
                # ' ', a, a, a, ' '
                #                ^     start (token_i=4)
                #            ^         -1
                #         ^            -len(prev_tokens)
                #  ^                   -len(prev_classes)
                start_at = token_i
                start_at -= 1
                prev_tokens = constraints.get('prev_tokens')
                if prev_tokens:
                    start_at -= len(prev_tokens)
                start_at -= len(c_value)
                if not self._match_tokens(start_at, c_value,
                                         check_prev=True, check_next=False,
                                         by_class=True):
                    return False

            elif c_type == 'next_classes':
                # presume for rule a (a <class_a>), with input "aaa"
                # ' ', a, a, a, ' '
                #         ^          start (token_i=2)
                #            ^       + len of next_tokens (a)
                start_at = token_i
                next_tokens = constraints.get('next_tokens')
                if next_tokens:
                    start_at += len(next_tokens)
                if not self._match_tokens(start_at, c_value,
                                          check_prev=False, check_next=True,
                                          by_class=True):
                    return False
        return True

    def _match_at(self, start_token_i):
        """
        Match best parser rule at `start_token_i`.

        Notes
        -----
        Expects and requires whitespace token at beginning and end of tokens.
        Utilizes a stack to which are passed a start node index.

        Returns
        -------
        int
            Rule index
        """

        tokens = self._input_tokens

        assert start_token_i > 0, "Rules expect whitespace, so must be >1."
        graph = self._graph

        stack = deque()
        start_node_key = 0
        stack.append((start_node_key, start_token_i))

        while stack:  # LIFO
            node_key, token_i = stack.pop()

            assert token_i < len(tokens), "past boundary"

            if token_i == len(tokens):  # stop at final whitespace
                target_token = None
            else:
                target_token = tokens[token_i]

            curr_node = graph.node[node_key]
            assert not curr_node.get('accepting')

            target_edges = curr_node['ordered_children'].get(target_token)
            if target_edges is None:
                target_edges = curr_node['ordered_children'].get('__rules__')
            for dest_key in target_edges:
                target_edge = graph.edge[node_key].get(dest_key)
                if dest_key:
                    if self._match_constraints(target_edge, token_i):
                        if target_edge.get('token'):
                            stack.append((dest_key, token_i+1))
                        else:  # rule node matched.
                            rule_node = graph.node[dest_key]
                            assert rule_node['accepting']
                            return rule_node['rule_key']
        raise ValueError(
            "Could not match token \"%s\" at pos %s in %s" %
            (tokens[token_i], token_i, tokens)
        )

    def _match_tokens(self, start_i, c_value, check_prev=True,
                      check_next=True, by_class=False):
        """ Matches tokens, does boundary checks. """

        tokens = self._input_tokens

        if check_prev and start_i < 0:
            return False
        if check_next and start_i + len(c_value) > len(tokens):
            return False
        for i in range(0, len(c_value)):
            if by_class:
                if not c_value[i] in self._tokens[tokens[start_i+i]]:
                    return False
            elif tokens[start_i+i] != c_value[i]:
                return False
        return True

    def parse(self, input):
        """
        Parse an input str into an output str.

        Parameters
        ----------
        input : str
            String to parse

        Returns
        -------
        str

        Raises
        ------
        ValueError
            Cannot parse input
        """

        tokens = self.tokenize(input)  # adds initial+final whitespace
        self._input_tokens = tokens
        output = ""
        token_i = 1  # adjust for initial whitespace

        while token_i < len(tokens)-1:  # adjust for final whitespace
            rule_key = self._match_at(token_i)
            rule = self.rules[rule_key]
            assert rule, "Rule missing!"
            tokens_matched = rule.tokens
            if self._onmatch_rules:
                prev_t = tokens[token_i-1]
                curr_t = tokens[token_i]
                curr_match_rules = self._onmatch_rules_lookup[curr_t][prev_t]

                for onmatch in curr_match_rules:
                    # <class_a> <class_a> + <class_b>
                    # a a b
                    #     ^
                    # ^      - len(onmatch.prev_rules)
                    if self._match_tokens(
                        token_i-len(onmatch.prev_classes),
                        onmatch.prev_classes,  # double checks last value
                        check_prev=True, check_next=False, by_class=True
                    ) and self._match_tokens(
                        token_i,
                        onmatch.next_classes,  # double checks first value
                        check_prev=False, check_next=True, by_class=True
                    ):
                        output += onmatch.production
                        break  # only match best onmatch rule

            output += rule.production

            token_i += len(tokens_matched)
        return output

    def tokenize(self, input):
        """
        Tokenizes an input string.

        Adds initial and trailing whitespace, and consolidates if requested.

        Parameters
        ----------
        input : str
            String to tokenize

        Returns
        -------
        list or None

        Raises
        ------
        ValueError
            Unrecognizable input, such as a character that is not in a token

        Examples
        --------
        >>> import urdubiometer
        >>> t = {'ab': ['class_ab'], ' ': ['wb']}
        >>> w = {'default': ' ', 'token_class': 'wb', 'consolidate': True}
        >>> r = {'ab': 'AB', ' ': '_'}
        >>> settings = {'tokens': t, 'rules': r, 'whitespace': w}
        >>> gp = urdubiometer.GraphParser.from_dict(settings)
        >>> gp.tokenize('ab ')
        ['ab', ' ']
        """

        def is_whitespace(token):
            """Checks if token is whitespace."""

            return self.whitespace.token_class in self.tokens[token]

        def match_generator():
            """Generate matches."""

            match = self._tokenizer.match(input, 0)
            while match:
                yield match
                match = self._tokenizer.match(input, match.end())

        tokens = []

        tokens.append(self.whitespace.default)

        matches = match_generator()
        prev_whitespace = True

        for match in matches:
            token = match.group(0)
#           Could save match loc here:
#           matched_at = match.span(0)[0]
            if is_whitespace(token):
                if prev_whitespace and self.whitespace.consolidate:
                    continue
            else:
                prev_whitespace = False
            tokens.append(match.group(0))

        if self.whitespace.consolidate:
            while is_whitespace(tokens[-1]):
                tokens.pop()

        tokens.append(self.whitespace.default)

        assert len(tokens) >= 2  # two whitespaces, at least

        if len(tokens) == 2:
            raise ValueError(
                "Unrecognizable input at pos 0: %s" % input
            )
        elif match.end() != len(input):
            raise ValueError(
                "Unrecognizable input at pos %s: %s" % (match.endpos, input)
            )
        else:
            return tokens

    @property
    def tokens(self):
        """ dict of list of str: Mappings of tokens to a list of classes."""
        return self._tokens

    @property
    def rules(self):
        """ list of ParserRule: Parser rules sorted by cost."""
        return self._rules

    @property
    def onmatch_rules(self):
        """ list of OnMatchRules: On match rules, ordered as at input."""
        return self._onmatch_rules

    @property
    def whitespace(self):
        """ WhiteSpace:  Whitespace rules for this parser."""
        return self._whitespace

    @classmethod
    def from_dict(cls, data, raw=True, **kwargs):
        """
        Construct GraphParser from a raw dict of tokens, rules, (optionally)
        onmatch_rules, and whitespace settings.

        This method is used to process YAML and other serialized forms. It
        converts each rule into a `ParserRule`, sorted by weight, and
        each `onmatch_rule`

        TODO: Fix

        Parameters
        ----------
        data : dict
            Dictionary containing `tokens`, `rules`, `onmatch_rules`
            (optional), and `whitespace` settings
        raw : boolean
            The dictionary needs to be processed from easy-reading format (the
            default is True)

        Returns
        -------
        GraphParser
        """

        if raw:
            _validate_raw_settings(data)
            data = _process_settings(data)

        return GraphParser(data['tokens'],
                           data['rules'],
                           data['onmatch_rules'],
                           data['whitespace'], **kwargs)

    @classmethod
    def from_yaml(cls, yaml_str, charnames_escaped=True, **kwargs):
        """
        Construct GraphParser from a YAML str

        Calls `from_dict`.

        Parameters
        ----------
        yaml_str : str
            YAML mappings of tokens, rules, and (optionally) onmatch_rules
        charnames_escaped : boolean
            Unescape Unicode during YAML read (default True)

        Returns
        -------
        GraphParser

        See Also
        --------
        GraphParser.from_yaml_file()
        GraphParser.from_dict()
        """

        if charnames_escaped:
            yaml_str = _unescape_charnames(yaml_str)

        data = yaml.load(yaml_str)

        return cls.from_dict(data, **kwargs)

    @classmethod
    def from_yaml_file(cls, yaml_filename, **kwargs):
        """
        Construct GraphParser from YAML file yaml_filename

        Calls `from_yaml`.

        Parameters
        ----------
        yaml_filename : str
            Name of YAML file, containing tokens, rules, and (optionally)
            onmatch_rules

        Returns
        -------
        GraphParser

        See Also
        --------
        urdubiometer.graphparser.from_yaml
        urdubiometer.graphparser.from_dict
        """

        with open(yaml_filename, 'r') as f:
            yaml_string = f.read()

        return cls.from_yaml(yaml_string, **kwargs)


# ---------- methods ----------


def _unescape_charnames(input_str):
    """
    Takes a string using \\N{Unicode charname} to escape unicode characters,
    and turns it into a Unicode string.

    This is useful for specifying exact character names, and a default
    escape feature in Python that needs a function to be used for reading
    from files.

    Parameters
    ----------
    input_str : str
        The unescaped string, with \\N{Unicode charname} converted to
        the corresponding Unicode characters.

    Examples
    --------

    >>> from urdubiometer import graphparser
    >>> graphparser.unescape_charnames(r"H\N{LATIN SMALL LETTER I}")
    'Hi'
    """

    def get_unicode_char(matchobj):
        """ Gets Unicode character value from escaped character sequences."""

        charname = matchobj.group(0)
        match = re.match(r'\\N{([A-Z ]+)}', charname)
        char = unicodedata.lookup(match.group(1))  # raises KeyError if invalid
        return char

    return re.sub(r'\\N{[A-Z ]+}', get_unicode_char, input_str)
