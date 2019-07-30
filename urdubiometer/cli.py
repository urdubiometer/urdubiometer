# -*- coding: utf-8 -*-
"""Console script for urdubiometer."""

import click
import os
import pickle
import urdubiometer


def _load_scanner(scanner_file):
    """
    Load scanner from a pickle, otherwise return DefaultScanner.

    Raises
    ------
    ValueError

    """
    if not scanner_file:
        scanner = urdubiometer.DefaultScanner()
    else:
        with open(scanner_file, "rb") as f:
            scanner = pickle.load(f)
            if not isinstance(scanner, urdubiometer.Scanner):
                raise ValueError(
                    "%s is not a pickle of a Scanner" % scanner_file
                )
    return scanner


def _echo_results(output_format, results):
    """Echo results in desired output format."""
    if output_format == "python":
        click.echo(results)
    elif output_format == "yaml":
        import yaml
        click.echo(yaml.dump(results))
    elif output_format == "json":
        import json
        click.echo(json.dumps(results))


def _get_version():
    """Get urdubiometer version."""
    from urdubiometer import __version__ as version
    return version


@click.group()
@click.version_option(version=_get_version())
def main(args=None):
    """Console script for urdubiometer."""
    return 0


# ---------- info ----------


@click.command("info", help="Report UrduBioMeter version and module path.")
def info():
    """Show UrduBioMeter version."""
    from urdubiometer import __version__
    click.echo("UrduBioMeter version %s" % __version__)
    click.echo("- loaded from path: %s" % os.path.dirname(__file__))


# ---------- meters_list ----------


@click.command("meters_list", help="Get a list of a scanner's meters.")
@click.option("--output_format", "-of",
              type=click.Choice(["yaml", "json", "python"]),
              default="python",
              envvar="URDUBIOMETER_OUTPUT_FORMAT",
              help="Output format for meters.")
@click.option('--scanner_file', '-sf',
              envvar='URDUBIOMETER_SCANNER_FILE',
              type=click.Path(exists=True),
              help="Pickle file of scanner. (DefaultScanner otherwise).")
def meters_list(output_format, scanner_file):
    """Echo meters list."""
    scanner = _load_scanner(scanner_file)
    _echo_results(output_format, scanner.meters_list)


# --------- scan ----------


@click.command("scan", help="Scan verse(s).")
@click.option("--scanner_file", "-s",
              envvar='URDUBIOMETER_SCANNER_FILE',
              type=click.Path(exists=True),
              help="Pickle file of scanner. (DefaultScanner otherwise).")
@click.option("--output_format", "-of",
              type=click.Choice(["yaml", "json", "python"]),
              default="python",
              envvar="URDUBIOMETER_OUTPUT_FORMAT",
              help="Output format for scan.")
# @click.option("--output_file", "-o",
#               type=click.Path(),
#               envvar="URDUBIOMETER.OUTPUT_FILE",
#               help="Output file for scan(s) (optional).")
@click.option('--first_only', '-fo', is_flag=True,
              envvar="URDUBIOMETER_FIRST_ONLY",
              help="Return the first scan only.")
@click.option('-sf', '--show_feet', default=False, is_flag=True,
              envvar="URDUBIOMETER_SHOW_FEET",
              help="Indicate the metrical feet in the returned scans.")
# @click.option('--graph_details', '-gd', is_flag=True,
#               envvar="URDUBIOMETER_GRAPH_DETAILS",
#               help="Teturn  graph details (NodeMatch instead of UnitMatch).")
@click.argument('input')
def scan(scanner_file,
         output_format,
         first_only,
         show_feet,
         input):
    """
    Scan verses(s) with UrduBioMeter.

    Raises
    ------
    ValueError
        scanner_file is not a pickle of an urdubiometer.Scanner.

    """
    scanner = _load_scanner(scanner_file)

    results = scanner.scan(input, first_only=first_only, show_feet=show_feet)
#                           graph_details=graph_details)
    _echo_results(output_format, results)


main.add_command(info)
main.add_command(meters_list)
main.add_command(scan)
if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
