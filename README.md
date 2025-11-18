# AWS Flow Corrector

Convert static Amazon Connect contact flows to Terraform templates by replacing hardcoded ARNs with dynamic references.

## Usage

```bash
# Basic conversion
python3 main.py -i example_flow.json

# Dry run (preview changes)
python3 main.py -i example_flow.json --dry-run

# Also update Metadata section
python3 main.py -i example_flow.json --update-metadata

# Custom output file
python3 main.py -i example_flow.json -o output.json
```

## What it does

Converts ARNs like:
```
arn:aws:lambda:us-east-1:123456789:function:state-lookup
```

To dynamic references:
```
${lambda.state_lookup}
```

## Options

- `-i, --input-file` - Input contact flow JSON file (required)
- `-o, --output-file` - Output file name (default: input with `.out.json` suffix)
- `-d, --dry-run` - Preview changes without writing files
- `-m, --update-metadata` - Also update ARNs in Metadata section (default: Actions only)
- `-p, --print-keys` - Print all ARNs and their dynamic reference keys
- `-v, --verbose` - Detailed output

## Requirements

Python 3.8+ (no external dependencies)

## License

MIT
