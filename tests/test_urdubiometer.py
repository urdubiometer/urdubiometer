#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `urdubiometer` package."""

from click.testing import CliRunner
import urdubiometer
from urdubiometer import cli
import pickle

# @pytest.fixture
# def response():
#     """Sample pytest fixture.
#
#     See more at: http://doc.pytest.org/en/latest/fixture.html
#     """
#     # import requests
#     #return requests.get('https://github.com/audreyr/cookiecutter-pypackage')

# def test_content(response):
#     """Sample pytest test function with the pytest fixture as an argument."""
#     # from bs4 import BeautifulSoup
#     # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_default_scanner():

    z = urdubiometer.DefaultScanner(
        meters_filter=lambda x: [_ for _ in x if _['id'] == 1]
    )
    assert len(z.meters_list) == 1


def test_command_line_interface(tmpdir):
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'urdubiometer' in result.output
    # test help
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output
    # test info
    info_result = runner.invoke(cli.main, ['info'])
    assert info_result.exit_code == 0
    assert "UrduBioMeter version" in info_result.output
    # test scan (note this verse has multiple scans so runs post_scan_filter)
    _sample_verse = "ja;zbah-e be-i;xtiyaar-e shauq dekhaa chaahiye"
    scan_result = runner.invoke(cli.main, ['scan', _sample_verse])
    assert scan_result.exit_code == 0
    # test scan (bad tokens)
    assert "scan='=-===-===-===-='" in scan_result.output
    # test meters_of
    meters_list_result = runner.invoke(cli.main, ['meters_list'])
    assert meters_list_result.exit_code == 0
    assert "hazaj musaddas a;xram ashtar" in meters_list_result.output
    # test meters_of with load_scanner
    _scanner = urdubiometer.DefaultScanner()
    # import pdb; pdb.set_trace()
    # _tmp_file is a py._path.local.LocalPath
    _tmp_file = tmpdir.mkdir('test_cli').join('scanner.pickle')
    with _tmp_file.open('wb') as f:
        pickle.dump(_scanner, f)
    meters_list_sf_result = runner.invoke(
        cli.main, ['meters_list', '-sf', str(_tmp_file)])
    assert meters_list_sf_result.exit_code == 0
    # test meters_of with load_scanner of bad pickle
    with _tmp_file.open('wb') as f:
        pickle.dump('["bad"]', f)
    meters_list_bad_result = runner.invoke(
        cli.main, ['meters_list', '-sf', str(_tmp_file)]
    )
    assert meters_list_bad_result.exit_code != 0
    # test yaml output
    meters_list_yaml_result = runner.invoke(
        cli.main, ['meters_list', '-of=yaml'])
    assert "name: hazaj" in meters_list_yaml_result.output
    # test json output
    meters_list_json_result = runner.invoke(
        cli.main, ['meters_list', '-of=json'])
    assert '"name": "hazaj' in meters_list_json_result.output
