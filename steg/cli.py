import argparse
import sys

from .constants import DEFAULT_DECODE_OUTPUT
from .errors import StegError
from .pipeline import run_decode, run_encode


class StrictArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        raise StegError(f"Invalid arguments: {message}", exit_code=1)


def _encode_parser() -> argparse.ArgumentParser:
    parser = StrictArgumentParser(prog="steg-encode", add_help=True)
    parser.add_argument("-i", "--input", required=True, help="Input PNG path")
    parser.add_argument("-m", "--message", required=True, help="Message file path")
    parser.add_argument("-k", "--key", required=True, help="Passphrase")
    parser.add_argument("-o", "--output", required=True, help="Output stego PNG path")
    return parser


def _decode_parser() -> argparse.ArgumentParser:
    parser = StrictArgumentParser(prog="steg-decode", add_help=True)
    parser.add_argument("-i", "--input", required=True, help="Stego PNG path")
    parser.add_argument("-k", "--key", required=True, help="Passphrase")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_DECODE_OUTPUT,
        help=f"Decoded output path (default: {DEFAULT_DECODE_OUTPUT})",
    )
    return parser


def _main(fn, parser: argparse.ArgumentParser, argv: list[str] | None = None) -> int:
    try:
        args = parser.parse_args(argv)
        fn(args)
        return 0
    except StegError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        print(f"error: unexpected failure: {exc}", file=sys.stderr)
        return 1


def encode_main(argv: list[str] | None = None) -> int:
    parser = _encode_parser()

    def run(args):
        run_encode(args.input, args.message, args.key, args.output)

    return _main(run, parser, argv)


def decode_main(argv: list[str] | None = None) -> int:
    parser = _decode_parser()

    def run(args):
        run_decode(args.input, args.key, args.output)

    return _main(run, parser, argv)

