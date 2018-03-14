# -*- coding: utf-8 -*-
"""
Methods to check parameters passed to GraphParser.

"""
import yaml
from cerberus import Validator
from .process import RULE_RE, ONMATCH_RE

# ---------- validate raw settings ----------

RAW_SETTINGS_SCHEMA = yaml.load(
    '''
    rules:
        type: dict
        required: True
        keyschema:
            type: string
            regex: {rule_regex}
        valueschema:
            type: string
    onmatch_rules:
        type: list
        required: False
        schema:
            type: dict
            minlength: 1
            maxlength: 1
            keyschema:
                type: string
                regex: {onmatch_regex}
            valueschema:
                type: string
    tokens:
        type: dict
        required: True
        keyschema:
            type: string
        valueschema:
            type: list
            schema:
                type: string
    whitespace:
        type: dict
        required: True
        schema:
            default:
                required: True
                type: string
            token_class:
                required: True
                type: string
            consolidate:
                required: True
                type: boolean
    '''.format(rule_regex=RULE_RE.pattern,
               onmatch_regex=ONMATCH_RE.pattern)
)


def _validate_raw_settings(data):
    """ Checks general structure of passed dictionary.

    Raises
    ------
    ValueError
        If there are errors in the raw settings inputed to `GraphParser`
    """

    validator = Validator()
    validator.validate(data, RAW_SETTINGS_SCHEMA)
    if validator.errors:
        raise ValueError("Errors in GraphParser input: \n %s" %
                         validator.errors)

# ---------- validate settings ----------


def _validate_settings(tokens, rules, onmatch_rules, whitespace):
    """ Validates settings for GraphParser.

    This method first checks the tokens, then uses the tokens and token
    classes to validate the rules, onmatch rules, and whitespace settings,
    all of which need the information from the tokens.

    Raises
    ------
    ValueError
        If there are errors in the settings of the current `GraphParser`, such
        as missing parameters or invalid token classes.
    """

    validator = Validator()

    tokens_schema = yaml.load("""
        tokens:
            type: dict
            keyschema:
                type: string
            valueschema:
                type: list
                schema:
                    type: string
    """)

    validator.validate({'tokens': tokens}, tokens_schema)

    if validator.errors:
        raise ValueError(
            "GraphParser `tokens` contains invalid entries:\n %s" %
            validator.errors)

    token_keys = list(tokens.keys())
    token_classes = list(set().union(*tokens.values()))

    rules_schema = {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'tokens': {
                    'required': True,
                    'type': 'list',
                    'allowed': token_keys,
                },
                'prev_classes': {
                    'required': False,
                    'type': 'list',
                    'allowed': token_classes,
                },
                'prev_tokens': {
                    'required': False,
                    'type': 'list',
                    'allowed': token_keys,
                },
                'next_tokens': {
                    'required': False,
                    'type': 'list',
                    'allowed': token_keys,
                },
                'next_classes': {
                    'required': False,
                    'type': 'list',
                    'allowed': token_classes,
                },
                'production': {
                    'required': True,
                    'type': 'string',
                },
            }
        }
    }

    onmatch_rules_schema = {
        'type': 'list',
        'required': False,
        'schema': {
            'type': 'dict',
            'schema': {
                'prev_classes':  {
                    'type': 'list',
                    'schema': {
                        'allowed': token_classes
                    }
                },
                'production': {
                    'type': 'string',
                },
                'next_classes': {
                    'type': 'list',
                    'schema': {
                        'allowed': token_classes
                    }
                }
            }
        }
    }

    whitespace_schema = {
        'type': 'dict',
        'required': True,
        'schema': {
            'default': {
                'type': 'string',
                'allowed': token_keys
            },
            'token_class': {
                'type': 'string',
                'allowed': token_classes
            },
            'consolidate': {
                'type': 'boolean'
            }
        }
    }

    schemas = {'whitespace': whitespace_schema,
               'onmatch_rules': onmatch_rules_schema,
               'rules': rules_schema}

    document = {'whitespace': whitespace,
                'rules': rules,
                'onmatch_rules': onmatch_rules}  # Cerberus needs a dict

    validator.validate(document, schemas)

    if validator.errors:
        raise ValueError("GraphParser settings contain invalid entries:\n%s" %
                         validator.errors)
