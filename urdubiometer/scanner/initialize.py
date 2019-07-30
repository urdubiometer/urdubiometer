# -*- coding: utf-8 -*-
"""Methods used in initialization of scanner."""

from collections import deque
from copy import deepcopy
from graphtransliterator import DirectedGraph


def _constrained_parsers_of(constraints, long_parser, short_parser):
    """
    Create a dict of parsers based on constraints.

    Prunes invalid productions from indicated parser.

    Returns
    -------
    dict

    """
    if not constraints:
        return None

    constrained_parsers = deepcopy(constraints)

    for prev_node_key, next_node in constrained_parsers.items():
        for next_node_key, prev_token in next_node.items():
            for prev_token_key, productions in prev_token.items():
                if next_node_key == '=':
                    parser = long_parser
                elif next_node_key == '_':
                    parser = short_parser
                elif next_node_key == '-':
                    parser = short_parser
                prev_token[prev_token_key] = parser.pruned_of(productions)
    return constrained_parsers


# ---------- regex to directed graph ----------


def _meters_graph_of(meters_list):
    """
    Convert a list of meter dict into a graph.

    Generates a graph for each meter as a subgraph, then adds to meters_graph.
    Parameters
    ----------
    meter_list : list of dict
        List of meters containing field "regex_pattern", and other info.
    Returns
    -------
    DirectedGraph
    """

    meters_list = deepcopy(meters_list)  # necessary for update
    meters_graph = DirectedGraph()

    # validate_meters_list(meters_list) already called in init so cut
    for i, meter in enumerate(meters_list):
        regex = meter['regex_pattern']
        subgraph = _minimized_graph_of_meter(regex)
        meter.update({'meter_key': i})
        meters_graph = _add_subgraph_to_graph(
            subgraph,
            meters_graph,
            meter)
    return meters_graph


def _regex_to_postfix(regex):
    """
    Convert infix regular expression into postfix w/ implicit concatenation.

    Parameters
    ----------
    regex : str
        Regular expression -- accepts only ( | ) * + ?

    Returns
    -------
    str

    Notes
    -----
    Translated from Russ Cox's C implementation of
    Ken Thompson's Regular Expression Search Algorithm:
    https://swtch.com/~rsc/regexp/dfa0.c.txt (MIT License)

    See also http://swtch.com/~rsc/regexp/ and
    Thompson, Ken.  Regular Expression Search Algorithm,
    Communications of the ACM 11(6) (June 1968), pp. 419-422.

    """
    nalt = 0
    natom = 0
    dst = []
    paren = []

    if not len(regex) > 0:  # pragma: no cover
        raise ValueError("Regular expression is empty.")

    for _ in regex:

        if _ == '(':
            if natom > 1:
                natom = natom - 1
                dst.append('.')
            paren.append((nalt, natom))
            nalt = 0
            natom = 0
        elif _ == '|':
            if natom == 0:  # pragma: no cover
                raise ValueError(
                    "Regex is missing an expression before |."
                )
            natom -= 1
            while natom > 0:
                dst.append('.')
                natom -= 1
            nalt += 1
        elif _ == ')':
            if not paren:
                raise ValueError(
                    "Regex parentheses do not match."
                )
            if natom == 0:  # pragma: no cover
                raise ValueError(
                    "Regex parentheses are missing an expression."
                )
            natom -= 1
            while natom > 0:
                dst.append('.')
                natom -= 1
            while nalt > 0:
                dst.append('|')
                nalt -= 1
            (nalt, natom) = paren.pop()
            natom += 1
        elif _ in ('*', '+', '?'):
            if natom == 0:  # pragma: no cover
                raise ValueError(
                    "Regex operator %s requires an expression." % _
                )
            dst.append(_)
        else:
            if natom > 1:
                natom -= 1
                dst.append('.')
            dst.append(_)
            natom += 1
    natom -= 1
    while natom > 0:
        dst.append('.')
        natom -= 1
    while nalt > 0:
        dst.append('|'*nalt)
        nalt -= 1
    return ''.join(dst)


def _postfix_to_ndfa(postfix):
    """
    Convert postfix regular expression to NDFA as directed graph.

    This function coverts a postfix regular expression to a
    nondeterministic finite automaton, represented by a directed graph.
    The resulting graph will have nodes with "type" labeled as "Split",
    "Accepting," or text of individual tokens, e.g. "a".


    Parameters
    ----------
    postfix : str
        Postfix format of a regular expression.

    Returns
    -------
    DirectedGraph


    Notes
    -----
    The code translates from Russ Cox's C implementation of
    Ken Thompson's Regular Expression Search Algorithm:
    https://swtch.com/~rsc/regexp/dfa0.c.txt (MIT License)

    See also http://swtch.com/~rsc/regexp/ and
    Thompson, Ken.  Regular Expression Search Algorithm,
    Communications of the ACM 11(6) (June 1968), pp. 419-422.
    """
    graph = DirectedGraph()

    def state(node_type, out, out1):
        """
        Create a state node and connect it to following nodes.

        Parameters
        ----------
        node_type : str
            Type of Node ("Accepting", "Split", or text)
        out: int or None
            target node
        out1: int or None
            second target node

        Returns
        -------
        int

        """
        assert out is None or type(out) == int
        assert out1 is None or type(out) == int

        _node_data = {"type": node_type}

        node_key, node = graph.add_node(
            node_data=_node_data
        )

        for _ in out, out1:
            if _:
                graph.add_edge(node_key, _)

        return node_key

    class frag:
        def __init__(self, start, out):
            self.start = start
            self.out = out
            # out is a list of states with dangling arrows.

    def patch(l, s):
        # patch list of states at out to point to start

        for _ in l:
            graph.add_edge(_, s)

    def push(x):
        stackp.append(x)

    def pop():
        return stackp.pop()

    stackp = []

    for _ in postfix:
        if _ == '.':    # concatenate
            e2 = pop()
            e1 = pop()
            patch(e1.out, e2.start)
            push(frag(e1.start, e2.out))
        elif _ == '|':  # alternate
            e2 = pop()
            e1 = pop()
            s = state('Split', e1.start, e2.start)
            push(frag(s, e1.out + e2.out))
        elif _ == '?':  # zero or one
            e = pop()
            s = state('Split', e.start, None)
            push(frag(s, e.out + [s]))

        elif _ == '*':  # zero or more
            e = pop()
            s = state('Split', e.start, None)
            patch(e.out, s)
            push(frag(s, [s]))

        elif _ == '+':  # one or more
            e = pop()
            s = state('Split', e.start, None)
            patch(e.out, s)
            push(frag(e.start, [s]))

        else:
            s = state(_, None, None)
            push(frag(s, [s]))

    e = pop()

    matchstate = state('Accepting', None, None)

    patch(e.out, matchstate)

    return graph


def _minimize_ndfa(ndfa):
    """
    Remove "split" nodes from NDFA by determining reachable nodes.

    First, creates a new graph from the NDFA without "Split" nodes and
    maps the original nodes to these new ones. Then performs a depth-first
    search on each original node if it is not a "Split" node. Then creates
    a new depth-first search to non-"Split" nodes of children.
    Add edges from mapped new node to mapped new node of each child.

    Parameters
    ----------
    ndfa : DirectedGraph
        NDFA as directed graph.

    Notes
    -----
    Currently, root node is type "0", split node is type "Split", and
    Accepting node is type "Accepting."

    Checks for already existing edges and does not add if present.

    Returns
    -------
    DirectedGraph
        Directed graph with split nodes removed and nodes renumbered.
    """

    def children_of(node_key):
        # could move to graphtransliterator.DirectedGraph
        return [_[1] for _ in ndfa.edge_list if _[0] == node_key]

    def gen_new_graph_and_mappings():
        """
        Generate a new graph from NDFA without split nodes with mappings
        from original NDFA node keys to new graph keys.

        Returns
        -------
        (DirectedGraph, dict of int:int)
            New graph and a mapping from NDFA with split nodes to new graph
        """
        new_graph = DirectedGraph()
        node_mappings = {}  # old to new node key
        # reachable_from = defaultdict(list)
        # children_of = lambda node_key: \
        #     [_[1] for _ in ndfa.edge_list if _[0] == node_key] # noqa
        # node_type_of = lambda node_key: ndfa.node[node_key]['type']
        # node_of = lambda node_key: ndfa.node[node_key]

        # create new graph, map previous to new nodes, skipping "Split" nodes.
        for node_key, node_data in enumerate(ndfa.node):
            if node_data.get('type') == 'Split':
                continue
            new_key, new_node = new_graph.add_node(node_data=node_data)
            node_mappings[node_key] = new_key
        return new_graph, node_mappings

    new_graph, node_mappings = gen_new_graph_and_mappings()

    # iterate through original nodes—a list of node attributes
    for node_key, node_data in enumerate(ndfa.node):
        # skip "Split" nodes
        if node_data.get('type') == 'Split':
            continue
        # Do a depth-first search to non-"Split" nodes of children.
        stack = deque(children_of(node_key))
        while stack:
            child_key = stack.popleft()
            # Add children of split node to stack
            if ndfa.node[child_key].get('type') == 'Split':
                # reversed to maintain original order
                stack.extendleft(reversed(children_of(child_key)))
            else:
                # Add edges from mapped new node to reachable child.
                if (node_mappings[node_key],
                   node_mappings[child_key]) not in new_graph.edge_list:
                    new_graph.add_edge(node_mappings[node_key],
                                       node_mappings[child_key])
    return new_graph


def _ndfa_graph_of_meter(regex):
    """
    Generate non-deterministic finite-state automaton graph of meter regex.

    Prepends a node of type "0" to serve as start node.

    Parameters
    ----------
    regex : str
        Regular expression for meter

    Returns
    -------
    DirectedGraph
        Directed-graph representation of NDFA

    """
    postfix = _regex_to_postfix('0('+regex+')')
    ndfa = _postfix_to_ndfa(postfix)
    return ndfa


def _minimized_graph_of_meter(regex):
    """
    Generate a minimized graph from a meter regex.

    Parameters
    ----------
    regex : string
        Regular expression for meter

    Returns
    -------
    Directed Graph
        Minimized graph, removing "split" nodes of NDFA

    """
    ndfa = _ndfa_graph_of_meter(regex)
    graph = _minimize_ndfa(ndfa)
    return graph


def _add_subgraph_to_graph(graph, new_graph, accepting_attr):
    """
    Add subgraph to new graph.

    Does a depth-first search through the subgraph. If there are not
    nodes of the type in the new graph, adds them. It does not match
    nodes that contain cycles.

    If a subgraph node contains a cycle, it creates a new branch.

    Points all accepting nodes to the same node.


    Parameters
    ----------
    graph : DirectedGraph
        Subgraph to add
    new_graph : DirectedGraph
        Graph to which subgraph will be added
    accepting_attr : dict
        Attributes to be added to accepting nodes (e.g. meter details)
    """
    def children_of(graph, node_key):
        """Find children of node in DirectedGraph."""
        # could move to DirectedGraph
        return [target for source, target in graph.edge_list
                if source == node_key]

    def parents_of(graph, node_key):
        """Find marks of node in DirectedGraph."""
        return [source for source, target in graph.edge_list
                if target == node_key]

    def child_of_type(graph, node_key, child_type):
        """Find children of particular 'type' in DirectedGraph.

        Ignores children that contain cycles."""
        children = children_of(graph, node_key)
        level = levels_of(graph)
        for child_key in children:
            if graph.node[child_key].get('type') == child_type and \
               contains_cycle(child_key, graph=graph, level=level) is False:
                return child_key
        return None

    def levels_of(graph):
        """Returns level of each node in a DirectedGraph."""
        marked = {}
        root_key = 0
        queue = deque([root_key])
        level = {root_key: 0}
        marked[root_key] = True

        while queue:
            node_key = queue.popleft()
            for child_key in graph.edge.get(node_key, []):
                if not marked.get(child_key):
                    queue.append(child_key)
                    level[child_key] = level[node_key] + 1
                    marked[child_key] = True
        return level

    level = levels_of(graph)

    def contains_cycle(node_key, graph=graph, level=level):
        for parent_key in parents_of(graph, node_key):
            if level[parent_key] >= level[node_key]:  # should it be >= ?
                return True
        return False

    if len(new_graph.node) == 0:
        new_graph.add_node(node_data={'type': "0"})

    queue = deque()
    visited = set()
    queue.append((0, 0, visited))
    node_mappings = {0: 0}
    accepting_node_key = -1  # if accepting, point to same node.
    while queue:
        (node_key, new_node_key, visited) = queue.popleft()
        # print("node_key", node_key)
        # print("new_node_key", new_node_key)
        # print("stack", stack)
        # print("new_graph", new_graph.node, new_graph.edge)
        # print("graph.node[node_key]", graph.node[node_key])
        # print("new_graph.node[new_node_key]", graph.node[new_node_key])
        # import urdubiometer.visualizer
        # urdubiometer.visualizer.translation_graphviz(new_graph).view()

        # print(new_graph.node, new_graph.edge)

        # (node_key, new_node_key, visited) = stack.popleft()

        # if node_key in visited:  # pragma: no cover
        #     continue
        # else:
        #     visited.add(node_key
        assert node_key not in visited
        visited = deepcopy(visited)
        visited.add(node_key)
        children = children_of(graph, node_key)

        for child_key in children:
            child_node = graph.node[child_key]
            child_type = child_node.get('type')

            # branch out on nodes receiving cycles

            if contains_cycle(child_key):  # branch on all cyclical nodes
                equivalent = node_mappings.get(child_key)
                if equivalent:  # heading up tree
                    new_graph.add_edge(new_node_key, equivalent)
                    continue
                matching_child_key = None
            else:
                matching_child_key = node_mappings.get(child_key)
                if not matching_child_key:
                    matching_child_key = child_of_type(
                        new_graph, new_node_key, child_type
                    )

            if not matching_child_key:
                if child_type == 'Accepting' and accepting_node_key >= 0:
                    matching_child_key = accepting_node_key
                else:
                    matching_child_key, matching_child = new_graph.add_node(
                        node_data=child_node.copy()
                    )
                    if child_type == 'Accepting':
                        if accepting_attr:
                            matching_child.update(accepting_attr)
                        accepting_node_key = matching_child_key
                    node_mappings[child_key] = matching_child_key
            if (new_node_key, matching_child_key) in new_graph.edge_list:
                pass
            else:
                new_graph.add_edge(new_node_key, matching_child_key)
            queue.append((child_key, matching_child_key, visited))
    return new_graph
