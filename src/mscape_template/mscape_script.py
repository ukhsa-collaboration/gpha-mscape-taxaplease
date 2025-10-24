#!/usr/bin/env python3

"""
Example main script that pulls in functions from module(s) and runs the code. Suggested layout
and example helper functions provided below. These can be amended as required.
"""

# Imports - ordered (can use ruff to do this automatically)
import argparse
import logging
import sys

import mscape_template.mscape_functions as mf  # noqa: F401


# Arg parse setup
def get_args():
    """Get command line arguments. Arguments can be added or removed as
    required. It is however recommended to keep the arguments below as
    a minimum for development purposes."""
    parser = argparse.ArgumentParser(
        prog="mscape script",
        description="""Example script layout
        for code that will be integrated into mscape. This can be used
        as a template and amended as required.
        """,
    )
    parser.add_argument("--input", "-i", type=str, required=True, help="Sample ID")
    parser.add_argument("--output", "-o", type=str, required=True, help="Folder to save results to")
    parser.add_argument(
        "--server",
        "-s",
        type=str,
        required=True,
        choices=["mscape", "synthscape"],
        help="Specify server code is being run on - helpful if developing on synthscape and running on mscape",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        required=False,
        action="store_true",
        help="Use this option if code includes a step that writes to onyx so that it can be tested",
    )

    return parser.parse_args()


# Logger set up
def set_up_logger(stdout_file):
    """Example logger set up which can be amended as required. In this example,
    all logging messages go to a stdout log file, and error messages also go to
    stderr log. If the component runs correctly, stderr is empty. The logger is
    set to append mode so logs from older runs are not overwritten.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

    out_handler = logging.FileHandler(stdout_file, mode="a")
    out_handler.setFormatter(formatter)
    logger.addHandler(out_handler)

    return logger


# Main function
def main():
    "Main function description here"

    # Retrieve command line arguments:
    args = get_args()  # noqa: F841

    # Set up log file:
    log_file = "path/to/logfile/mscape-template_logfile.txt"
    set_up_logger(log_file)

    # Add in rest of code including logging messages:
    logging.info(
        "mscape template code beginning"
    )  # Example only - add more informative logging messages

    # Additional code in here

    # Write to logs if component finished successfully (or not):
    logging.info("mscape template code successfully completed")

    return


# Run
if __name__ == "__main__":
    sys.exit(main())
