# -*- coding: utf-8 -*-
"""
Base class for metrical scanner.

    Base class for metrical scanner that is extended to support different
    metrical paradigms.

    Notes
    -----
    Scanner uses a best-first search. Nodes are
    of type start/root ("Start"), metrical unit ("=" for long, "-" for short,
     and "_" for an optional, uncounted short followed by a wordbreak), or
    accepting ("Accepting").

"""
# add specific examples
import itertools
from collections import deque

# import logging
# logging.basicConfig(level=logging.CRITICAL)
# logger = logging.getLogger(__name__)

from .types import NodeMatch, ScanIteration, ScanResult, UnitMatch
from .validate import validate_parsers, validate_meters_list, validate_constraints
from .initialize import _meters_graph_of, _constrained_parsers_of


class Scanner:
    """
    Scanner class.

    Parameters
    ----------
    transcription_parser : graphtransliterator.GraphTransliterator
        Transcription parser.
    long_parser : graphtransliterator.GraphTransliterator
        Long metrical unit parser.
    short_parser : graphtransliterator.GraphTransliterator
        Short metrical unit parser.
    constraints : dict(str, dict(str, dict(str,list[str])))
        Nested dict of constraints, organized by previous node, next node,
        previous production and finally a list of next productions,  e.g.
        ``{'-':{'-': 's_bs':['s_c']}}``.
    meters_list : list[dict]
        A list of dictionaries of meters, containing a meter regex and details.
    find_feet : function
        Method to add metrical feet to a scan
    post_scan_filter : function
        Filter to be applied after scan, used to narrow results.

    """

    def __init__(
        self,
        transcription_parser,
        long_parser,
        short_parser,
        constraints,
        meters_list,
        find_feet=None,
        post_scan_filter=None,
    ):

        validate_parsers(transcription_parser, long_parser, short_parser)

        validate_constraints(
            constraints, long_parser.productions, short_parser.productions
        )

        validate_meters_list(meters_list)

        self._transcription_parser = transcription_parser
        self._long_parser = long_parser
        self._short_parser = short_parser
        self._find_feet = find_feet
        self._post_scan_filter = post_scan_filter
        self._constraints = constraints
        self._constrained_parsers = _constrained_parsers_of(
            constraints, long_parser, short_parser
        )

        self._translation_graph = _meters_graph_of(meters_list)
        self._meters_list = meters_list

    def transcribe(self, input):
        """Transcribe input using transcription parser.

        Parameters
        ----------
        input: str
            Input string

        Returns
        -------
            str
                Transcription of input string
        """

        return self._transcription_parser.transliterate(input)

    def scan(self, input, first_only=False, graph_details=False, show_feet=False):
        """
        Scan input.

        Parameters
        ----------
        input: str
            Input string
        first_only: bool
            Return the first scan only
        graph_details: bool
            Return the graph details (list of :class:`NodeMatch`)
        show_feet: bool
            Show metrical feet in scan. Default is `False`.

        Returns
        -------
        list or None
            if graph_details is False, a list of UnitMatch.
            if graph_details is True, a list of NodeMatch.
            None if no complete scans are found.
        """

        def special_parser():
            """Determine if there is a constrained parser to be used."""

            if not self._constrained_parsers or len(matches) == 0:
                return None
            parent_type = graph.node[parent_key]["type"]
            try:
                if parent_type == "_" and node_type == "=":
                    parser = self._constrained_parsers[parent_type][node_type]["*"]
                else:
                    parser = self._constrained_parsers[parent_type][node_type][
                        matches[-1].rule_found
                    ]
                return parser
            except KeyError:
                return None

        graph = self._translation_graph
        assert graph is not None
        parse = self._transcription_parser.transliterate(input)
        # find original tokens, and add whitespace.
        transcription_tokens = (
            [[self._transcription_parser._whitespace.default]]
            + self._transcription_parser.last_matched_rule_tokens
            + [[self._transcription_parser._whitespace.default]]
        )

        # logger.debug("Parse for input %s is: %s" % (input, parse))
        tokens = self._long_parser.tokenize(parse)

        # logger.debug("Tokens for input %s are: %s" % (input, tokens))
        completed_scans = []
        stack = deque()
        for _ in graph.edge[0]:  # <--- could add weights here
            stack.appendleft(
                ScanIteration(
                    node_key=_, parent_key=0, token_i=0, matches=[], matched_so_far=""
                )
            )
        continue_processing = True
        while continue_processing and len(stack) > 0:
            iteration = stack.popleft()
            (node_key, parent_key, token_i, matches, matched_so_far) = iteration
            node = graph.node[node_key]
            node_type = node["type"]
            # logger.debug(iteration)
            # ---- check if accepting ----
            if _is_accepting(node):

                if token_i == len(tokens) - 1:  # at final whitespace

                    # add feet to scan
                    if show_feet:
                        # this will raise an error if find_feet is
                        # not set for the Scanner.
                        matched_so_far = self._find_feet(matched_so_far)
                    scan_result = ScanResult(
                        scan=matched_so_far,
                        matches=matches,
                        meter_key=node.get("meter_key"),
                    )
                    completed_scans.append(scan_result)
                    # logger.debug('completed scan: %s' % str(scan_result))
                    if first_only:
                        continue_processing = False
                continue
            # ---- otherwise, check that node matches here ----
            if node_type == "=":
                parser = special_parser() or self._long_parser
            elif node_type == "-" or node_type == "_":
                parser = special_parser() or self._short_parser

            assert parser

            rules_matched = parser.match_at(token_i, tokens, match_all=True)
            if not rules_matched:
                continue
            # tokens have been matched for this node, so process its
            # children.
            # logger.debug(
            #    'Rules # %s of parser rule matched ' % rules_matched +
            #    'at node %s of type %s ' % (node_key, node_type)
            # )
            children = graph.edge[node_key]
            for rule_key in reversed(rules_matched):
                rule = parser.rules[rule_key]
                for child_key in children:
                    # store data about current match for this node
                    # This includes the original tokens matched by the
                    # transcription parser.

                    # Retrieve and flatten original tokens.
                    orig_tokens = list(
                        itertools.chain.from_iterable(
                            [
                                transcription_tokens[i]
                                for i in range(token_i, token_i + len(rule.tokens))
                            ]
                        )
                    )

                    if graph_details:
                        match_data = NodeMatch(
                            type=node_type,
                            matched_tokens=rule.tokens,
                            parent_key=parent_key,
                            node_key=node_key,
                            orig_tokens=orig_tokens,
                            rule_found=rule.production,
                            # rule_key=rule_key,
                            token_i=token_i,
                        )
                    else:

                        match_data = UnitMatch(
                            type=node_type,
                            rule_found=rule.production,
                            orig_tokens=orig_tokens,
                        )

                    # add new scan iterations

                    stack.appendleft(
                        ScanIteration(
                            node_key=child_key,
                            parent_key=node_key,
                            token_i=token_i + len(rule.tokens),
                            matches=matches + [match_data],
                            matched_so_far=matched_so_far + node_type,
                        )
                    )
        if len(completed_scans) > 0 and self._post_scan_filter:
            completed_scans = self._post_scan_filter(completed_scans)

        return completed_scans

    @property
    def meters_list(self):
        """:obj:`list` of :obj:`dict`:: Meters list."""
        return self._meters_list

    @property
    def translation_graph(self):
        """:obj:`urdubiometer.DirectedGraph`:: Translation graph."""
        return self._translation_graph


# ---------- methods ----------


def _is_accepting(node):
    """Check if node is accepting."""
    return node.get("type") == "Accepting"
