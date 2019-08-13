Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a
Changelog <http://keepachangelog.com/en/1.0.0/>`__, and this project
adheres to `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`__.

[Unrelease-Maybe]
-----------------

*  convert tokens to numbers inside ParserRules to improve performance
*  convert rules to number in , or add detailed result option
*  allow toggle of validation to decrease load speed
*  add minimum tokens to match to graphparser edge constraints
*  add coverage badge
*  rename GhazalScanner to GhazalScanner
*  variable rules for modern vs. classical language
*  adjust code to move long and short unit markers to constants
*  change rule_found to rule_id

[Unreleased-TODO]
-----------------

*  adjust license to support any additional software (if necessary)
*  confirm settings/transcription.yml is compatible with new UTMO
   standard
*  decide on parser/transliterator terminology
*  remove visited from \_add_subgraph_to_graph if cycle check means it’s
   no longer necessary (?)
*  add visualizations and check if \_add_subgraph_to_graph() is broken
*  add documentation
*  fix contributors
*  add requirements.txt
*  fix project description (markdown import) on pypi
*  fix code documentation and proofread
*  add black to contributing
*  raise warning/error in constraints if nothing matched or multiple
   matches
*  add feet to mir meters

X.X.X - XXXX-XX-XX
------------------

* removed  Markdown due to pypi errors, converted to RST
* fixes to CHANGELOG.rst due to bad conversion

0.2.8 - 2019-08-13
------------------

*  renamed DefaultScanner to GhazalScanner
*  added basic Mir meters in settings/mir_meters.yml
*  changed show_feet for missing Mir feet
*  added with_mir parameter to GhazalScanner
*  renamed default.py to ghazal.py
*  rewrote constrained_parsers_of to allow for regular expressions in
   constraints and to reuse already generated parsers
*  added translations/urdubiometer/messages
*  adjusted settings/constraints.yml
*  modified scanner/validate.py due to regex use in constraints
*  preliminary tie in with Transifex
*  added scripts/extract_strings.py, scripts/import_po.py,
   scripts/README.md
*  adjusted .travis.yml
*  added short long vowels to transcription.yml

0.2.7 - 2019-08-03
------------------

*  fixed setup.cfg, setup.py, to correct bumpversion problem with single
   quotes

0.2.6 - 2019-08-03
------------------

*  added black code formatting

0.2.5 - 2019-08-02
------------------

*  change to .travis.yml repo name
*  added python 3.7 to setup.py

0.2.4 - 2019-08-02
------------------

*  adjusted urdubiometer/\ **init**.py to fix **all** and import
*  changed “id” in meters_list to string and fixed tests in
   scanner/validate.py, settings/ghazal_meters.yml, test_scanner.py,
   test_urdubiometer.py
*  modification to doc structure (following earlier docs, needs
   adjustment) #### Added
*  added api.rst to docs (in progress)

0.2.3 - 2019-07-30
------------------

*  added to PyPI
*  added pyup
*  added pypi, pyup badges to readme.md
*  added notebooks/
*  adjust docs/index and added docs/api.rst

0.2.2 - 2019-07-30
------------------

*  added settings/\*
*  added urdubiometer/cli.py,
*  added tests/test_scanner.py
*  added scanner/\*
*  use of graphtransliterator using nodes as list rather than dict
   required rewrite of \_minimize_ndfa()
*  adjusted setup.py for markdown
*  modified urdubiometer.py (minor)
*  removed scanner.py

0.2.1 - 2019-07-28
------------------

*  removed tests/test_graphparser.py
*  removed urdubiometer/graphparser/\* to replace with
   graphtransliterator
*  removed graphparser from init.py
*  adusted .travis.yml tags

0.2.0 - 2018-03-14
------------------

*  added graphparser._types.py module with ParserRule, ParserOutput,
   OnMatchRule, WhiteSpace, and DirectedGraph classes
*  added tests/test_graphparser.py
*  added graphparser init and constructors: from_yaml_file, from_yaml,
   from_dict. They are cascaded: from_yaml_file calls from_yaml, which
   calls from_dict. Added a “raw” parameter, to from_dict as to whether
   or the dict needs to be processed from easy-reading format (default
   is True)
*  added \_unescape_charnames to graphparser module to unescape
   \\N{CHARNAME} strings (from files, especially)
*  added graphparser/validate.py to handle validation of raw and
   processed settings, using ``Cerberus``
*  created graphparser/initialize.py to convert rules, onmatch rules,
   and whitespace to internal types Rules, OnMatchRules, and Whitespace;
   and, to generate the parser’s internal DirectedGraph
*  added GraphParser.parse() method
*  modified tests to fail
*  updated contributing.md

0.1.2 - 2018-02-22
------------------

*  initialized scanner.py and graphparser submodule
*  added tests to check loading

0.1.1 - 2018-02-22
------------------

*  fixed badges in README.md

0.1.0 - 2018-02-22
------------------

*  added AUTHORS.md, CONTRIBUTING.md (from cookiecutter, converted to md
   from rst)
*  added docs, adjusting for markdown and sphinx_rtd_theme; enabled Napo
*  added requirements_dev.txt, the dev requirements for a virtualenv;
   included m2r, sphinx_rtd_theme, and
*  added Makefile (generated by cookiecutter)
*  added MANIFEST.in, with some changes for md
*  added setup.cfg, setup.py (customized for markdown), and tox.ini
*  added urdubiometer directory with cli.py, \__init__.py, and
   urdubiometer.py (cookiecutter)
*  added tests/test_urdubiometer.py (cookiecutter)
*  generated module documentation using Sphinx
*  updated README.md based off cookiecutter
*  updated .gitignore
*  adjusted .travis.yml (may need some work)

0.0.1 - 2018-02-21
------------------

*  Added This CHANGELOG.md file to record changes.
*  Added CODEOFCONDUCT.md contains guidelines for participation.
*  README.md created. It links to readthedocs.org, which I have
   initialized, and travis-ci.
*  added LICENSE.md file, which is BSD and (c) Michigan State University
*  added .travis.yml file for travis-ci
