#!/usr/bin/env python3
"""
AWS Flow Corrector
Converts Amazon Connect contact flows to templatable versions for Terraform.
"""

import argparse
import json
import sys
from pathlib import Path


def load_flow(file_path):
    """Load Amazon Connect flow JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)


def extract_template_keys(flow_data):
    """
    Extract all potential template keys from the flow.
    Looks for ARNs, phone numbers, queue IDs, etc.
    """
    keys = set()
    
    def traverse(obj, path=""):
        """Recursively traverse the flow structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                # Identify fields that should be templated
                if isinstance(value, str):
                    # Check for ARNs
                    if value.startswith("arn:aws:"):
                        keys.add(new_path)
                    # Check for phone numbers (E.164 format)
                    elif value.startswith("+") and len(value) > 10:
                        keys.add(new_path)
                    # Check for UUIDs (common in Connect)
                    elif len(value) == 36 and value.count("-") == 4:
                        keys.add(new_path)
                
                traverse(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{path}[{i}]")
    
    traverse(flow_data)
    return sorted(keys)


def convert_to_template(flow_data, dry_run=False):
    """
    Convert static values to template placeholders.
    Returns the templated flow and a dict of variables.
    """
    variables = {}
    counter = {}
    
    def get_var_name(field_type):
        """Generate a unique variable name."""
        if field_type not in counter:
            counter[field_type] = 1
        else:
            counter[field_type] += 1
        return f"{field_type}_{counter[field_type]}"
    
    def replace_values(obj):
        """Recursively replace static values with template variables."""
        if isinstance(obj, dict):
            return {key: replace_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [replace_values(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ARNs
            if obj.startswith("arn:aws:"):
                var_name = get_var_name("arn")
                variables[var_name] = obj
                return f"${{var.{var_name}}}" if not dry_run else obj
            # Replace phone numbers
            elif obj.startswith("+") and len(obj) > 10:
                var_name = get_var_name("phone")
                variables[var_name] = obj
                return f"${{var.{var_name}}}" if not dry_run else obj
            # Replace UUIDs
            elif len(obj) == 36 and obj.count("-") == 4:
                var_name = get_var_name("id")
                variables[var_name] = obj
                return f"${{var.{var_name}}}" if not dry_run else obj
        return obj
    
    templated_flow = replace_values(flow_data)
    return templated_flow, variables


def save_output(templated_flow, variables, output_path, input_filename):
    """Save the templated flow and variables file."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save templated flow
    flow_file = output_dir / f"{input_filename}.tpl.json"
    with open(flow_file, 'w') as f:
        json.dump(templated_flow, f, indent=2)
    
    # Save variables as Terraform tfvars format
    vars_file = output_dir / f"{input_filename}.tfvars"
    with open(vars_file, 'w') as f:
        for var_name, value in variables.items():
            f.write(f'{var_name} = "{value}"\n')
    
    return flow_file, vars_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert Amazon Connect flows to Terraform templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py my_flow.json
  python main.py my_flow.json --dry-run
  python main.py my_flow.json --print-keys
  python main.py my_flow.json --output ./templates
        """
    )
    
    parser.add_argument(
        "file",
        help="Path to the Amazon Connect flow JSON file"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for template files (default: output)"
    )
    
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Show what would be converted without creating files"
    )
    
    parser.add_argument(
        "-k", "--print-keys",
        action="store_true",
        help="Print all detected template keys and exit"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Load the flow
    if args.verbose:
        print(f"Loading flow from: {args.file}")
    
    flow_data = load_flow(args.file)
    input_filename = Path(args.file).stem
    
    # Print keys mode
    if args.print_keys:
        keys = extract_template_keys(flow_data)
        print("\nDetected template keys:")
        print("-" * 50)
        for key in keys:
            print(f"  {key}")
        print(f"\nTotal: {len(keys)} keys found")
        return 0
    
    # Convert to template
    if args.verbose:
        print("Converting flow to template...")
    
    templated_flow, variables = convert_to_template(flow_data, dry_run=args.dry_run)
    
    # Dry run mode
    if args.dry_run:
        print("\n🔍 DRY RUN - No files will be created")
        print("\nVariables that would be extracted:")
        print("-" * 50)
        for var_name, value in variables.items():
            print(f"  {var_name} = {value}")
        print(f"\nTotal: {len(variables)} variables found")
        return 0
    
    # Save output
    flow_file, vars_file = save_output(templated_flow, variables, args.output, input_filename)
    
    print(f"\n✅ Conversion complete!")
    print(f"\nTemplate file: {flow_file}")
    print(f"Variables file: {vars_file}")
    print(f"\nFound {len(variables)} variables")
    
    if args.verbose:
        print("\nVariables:")
        for var_name, value in variables.items():
            print(f"  {var_name} = {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
