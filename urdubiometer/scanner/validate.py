# -*- coding: utf-8 -*-
"""Methods to check parameters passed to Scanner."""


import yaml
from cerberus import Validator


# ---------- constraints ----------


CONSTRAINTS_SCHEMA_STR = """
    constraints:
        type: dict
        schema:
            "_":
                type: dict
                schema:
                    "=":
                        type: dict
                        keysrules:
                            type: string
                            allowed: ["*"]
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {long_productions}
            "-":
                type: dict
                schema:
                    "-":
                        type: dict
                        keysrules:
                            type: string
                            allowed: {short_productions}
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {short_productions}
                    "=":
                        type: dict
                        keysrules:
                            type: string
                            allowed: {short_productions}
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {long_productions}
            "=":
                type: dict
                schema:
                    "_":
                        type: dict
                        keysrules:
                            type: string
                            allowed: {long_productions}
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {short_productions}
                    "-":
                        type: dict
                        keysrules:
                            type: string
                            allowed: {long_productions}
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {short_productions}
                    "=":
                        type: dict
                        keysrules:
                            type: string
                            allowed: {long_productions}
                        valuesrules:
                            type: list
                            schema:
                                type: string
                                allowed: {long_productions}
    """


def validate_constraints(constraints, long_productions, short_productions):
    """
    Validate constraints.

    Parameters
    ----------
    constraints : dict
        invalid combinations
    short_productions : list
        list of short productions
    long_productions : list
        list of long productions

    """
    if not constraints:
        return
    schema_str = CONSTRAINTS_SCHEMA_STR.format(
        short_productions=short_productions,
        long_productions=long_productions
    )
    schema = yaml.safe_load(schema_str)
    validator = Validator()
    if not validator.validate({'constraints': constraints}, schema):
        raise ValueError("Errors in constraints:\n%s" % validator.errors)


# ---------- meters list ----------


def validate_meters_list(meters_list):
    """Validate meters list."""
    METERS_LIST_SCHEMA = yaml.safe_load(
        """
        meters_list:
            type: list
            required: true
            schema:
                type: dict
                schema:
                    id:
                        type: number
                    name:
                        type: string
                    notes:
                        type: string
                        required: False
                    fp7tag:
                        type: string
                        required: False
                    fp7pattern:
                        type: string
                        required: False
                    regex_pattern:
                        type: string # add pattern here
                        required: True
                    genre:
                        type: string
                        required: False
        """
    )
    validator = Validator()
    validator.validate({'meters_list': meters_list},
                       METERS_LIST_SCHEMA)
    if validator.errors:
        raise ValueError("Errors in meters list input: \n %s" %
                         validator.errors)


# ---------- validate parsers -----------


def validate_parsers(transcription_parser, long_parser, short_parser):
    """
    Check to make sure all tokens are accounted for.

    First checks that tokens of long and short parsers are the same,
    then checks productions of transcription with those of the long parser.

    Parameters
    ----------
    transcription_parser: urdubiometer.GraphParser
    long_parser: urdubiometer.GraphParser
    short_parser: urdubiometer.GraphParser

    """
    if set(long_parser.tokens.keys()) != set(short_parser.tokens.keys()):
        not_in_short = \
            set(long_parser.tokens.keys()) - set(short_parser.tokens.keys())
        not_in_long = \
            set(short_parser.tokens.keys()) - set(long_parser.tokens.keys())

        raise ValueError(
            "Long and short parser tokens do not match: \n" +
            "  Missing from long: %s\n" % not_in_long +
            "  Missing from short: %s\n" % not_in_short
        )

    production_tokens = [_.production for _ in transcription_parser.rules
                         if _.production != '']

    if set(production_tokens) != set(long_parser.tokens):
        not_in_transcription = \
            set(long_parser.tokens) - set(production_tokens)
        not_in_longshort = \
            set(production_tokens) - set(long_parser.tokens)
        raise ValueError(
            "Transcription and long/short tokens do not match: \n" +
            "  Missing from transcription: %s\n" % not_in_transcription +
            "  Missing from long/short: %s\n" % not_in_longshort
        )
