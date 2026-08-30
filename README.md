# AWS Flow Corrector

<!-- social-badges:start -->
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://discord.gg/jUMuSxGf6q)
[![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)](https://github.com/NC1107)
[![Patreon](https://img.shields.io/badge/Patreon-F96854?logo=patreon&logoColor=white)](https://patreon.com/NPC1107)
<!-- social-badges:end -->

Converts hardcoded ARNs in Amazon Connect contact flows to Terraform template variables. This enables deploying multiple isolated environments (dev, staging, prod) or per-developer flow replicas without ARN conflicts.

**Use case:** Deploy individual dev environments where each developer has their own isolated copy of flows (e.g., `dev_a_flow_4`, `dev_b_flow_4`) that reference their own resources, all managed through Terraform with a single template.

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

## License

[PolyForm Noncommercial 1.0.0](LICENSE).

Free for noncommercial use: personal, hobby, educational, research, nonprofit, and all that.
You can fork it, change it and redistribute it, you just can't sell it or use it commercially without asking first.
If you want to use it commercially, open an issue and ask.

Contributions are welcome. By submitting a pull request you agree that your changes are released under this same license.
