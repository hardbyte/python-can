"""
Convert a log file from one format to another.
"""

import sys
import argparse
import errno

from can import LogReader, Logger, SizedRotatingLogger


def main():
    parser = argparse.ArgumentParser(
        "python -m can.logconvert",
        description="Convert a log file from one format to another.",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="""Output filename, type dependent on suffix see can.LogReader.""",
        default=None,
        required=True,
    )

    parser.add_argument(
        "-s",
        "--file_size",
        dest="file_size",
        type=int,
        help="Maximum file size in bytes. Rotate log file when size threshold is reached.",
        default=None,
    )

    parser.add_argument(
        "infile",
        metavar="input-file",
        type=str,
        help="Log file to convert from. For supported types see can.LogReader.",
    )

    # print help message when no arguments were given
    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        raise SystemExit(errno.EINVAL)

    results = parser.parse_args()

    reader = LogReader(results.infile)

    if results.file_size:
        logger = SizedRotatingLogger(
            base_filename=results.output, max_bytes=results.file_size
        )
    else:
        logger = Logger(filename=results.output)

    try:
        for m in reader:  # pylint: disable=not-an-iterable
            logger(m)
    except KeyboardInterrupt:
        pass
    finally:
        logger.stop()


if __name__ == "__main__":
    main()
