"""Command-line interface for AWS Flow Corrector."""

import argparse
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Convert Amazon Connect flows to Terraform templates"
    )
    parser.add_argument(
        "input",
        help="Path to the input Amazon Connect flow JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path for the template file",
        default="output"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"Processing flow: {args.input}")
        print(f"Output directory: {args.output}")

    print("AWS Flow Corrector - Coming soon!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
