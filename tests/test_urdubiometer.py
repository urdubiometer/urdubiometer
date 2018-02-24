#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `urdubiometer` package."""

import pytest

from click.testing import CliRunner

import urdubiometer
#from urdubiometer import urdubiometer
from urdubiometer import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'urdubiometer.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output

def test_graph_parser_parse():
    """Tests graph-based parser parse function."""
    assert 'parse' in urdubiometer.GraphParser().__dir__()

def test_graph_parser():
    """Tests graph-based parser."""
    assert urdubiometer.GraphParser()


def test_scanner():
    """Tests metrical scanner."""
    assert urdubiometer.Scanner()

def test_scanner_scan():
    """Tests metrical scanner scan function."""
    assert 'scan' in urdubiometer.Scanner().__dir__()
