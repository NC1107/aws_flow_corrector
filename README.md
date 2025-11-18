# AWS Flow Corrector

Convert static Amazon Connect contact flows to Terraform templates by replacing hardcoded ARNs with dynamic references.

## Usage

**Single file:**
```bash
python3 main.py -i example_flow.json
```

**Batch process directory:**
```bash
python3 main.py --input-dir example_flows --output-dir output_flows
```

**Preview changes:**
```bash
python3 main.py -i example_flow.json --dry-run -v
```

## What it does

Converts ARNs like:
```
arn:aws:lambda:us-east-1:123456789:function:state-lookup
```

To dynamic references:
```
${function.state_lookup}
```

## Options

**Input/Output:**
- `-i, --input-file` - Single input JSON file
- `--input-dir` - Process all `.json` files in directory
- `-o, --output-file` - Output file (default: `{input}.out.json`)
- `--output-dir` - Output directory for batch processing

**Behavior:**
- `-d, --dry-run` - Preview without writing files
- `-m, --update-metadata` - Update Metadata section (default: Actions only)
- `-p, --print-keys` - Show ARN mappings and exit
- `-v, --verbose` - Detailed output

## Requirements

Python 3.8+ (no external dependencies)
