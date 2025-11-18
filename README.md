# AWS Flow Corrector

A simple Python script that converts static Amazon Connect contact flows into templatable versions for use with Terraform's `templatefile` function.

## Overview

AWS Flow Corrector analyzes Amazon Connect contact flow JSON files and converts hardcoded values (like ARNs, phone numbers, queue IDs) into Terraform template variables, making it easy to deploy the same flow across different environments (dev, staging, production).

## Features

- Converts static contact flows to templatable format
- Automatically detects ARNs, phone numbers, and UUIDs
- Generates Terraform variable files
- Dry-run mode to preview changes
- Print detected template keys

## Requirements

- Python 3.8+

## Usage

### Basic conversion:
```bash
python main.py my_flow.json
```

### Preview what will be converted (dry-run):
```bash
python main.py my_flow.json --dry-run
```

### Show all detected template keys:
```bash
python main.py my_flow.json --print-keys
```

### Specify output directory:
```bash
python main.py my_flow.json --output ./templates
```

### Verbose mode:
```bash
python main.py my_flow.json --verbose
```

## Output

The script generates two files:
- `<filename>.tpl.json` - The templated flow with Terraform variables
- `<filename>.tfvars` - Variable definitions file

## Using with Terraform

```hcl
resource "aws_connect_contact_flow" "example" {
  instance_id = var.connect_instance_id
  name        = "My Flow"
  type        = "CONTACT_FLOW"
  
  content = templatefile("${path.module}/output/my_flow.tpl.json", {
    arn_1   = var.arn_1
    phone_1 = var.phone_1
    id_1    = var.id_1
  })
}
```

## License

MIT
