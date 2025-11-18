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

Converts hardcoded ARNs in your flow JSON to template variables, allowing you to use them with Terraform's `templatefile()` function.

**Before:**
```json
{
  "LambdaFunctionARN": "arn:aws:lambda:us-east-1:123456789:function:state-lookup",
  "ContactFlowId": "arn:aws:connect:us-east-1:123456789:instance/abc/contact-flow/xyz"
}
```

**After:**
```json
{
  "LambdaFunctionARN": "${function_state_lookup}",
  "ContactFlowId": "${contact_flow_sample_flow}"
}
```

**Use in Terraform:**
```hcl
resource "aws_connect_contact_flow" "my_flow" {
  instance_id = aws_connect_instance.main.id
  name        = "My Flow"
  type        = "CONTACT_FLOW"
  
  content = templatefile("${path.module}/flow.out.json", {
    function_state_lookup            = aws_lambda_function.state_lookup.arn
    contact_flow_sample_flow         = aws_connect_contact_flow.sample.arn
  })
}
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
