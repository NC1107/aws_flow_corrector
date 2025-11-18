import argparse
import json
import re


# AWS ARN Structure:
# arn:partition:service:region:account-id:resource-id
# arn:partition:service:region:account-id:resource-type/resource-id
# arn:partition:service:region:account-id:resource-type:resource-id
#
# - partition: aws, aws-cn, aws-us-gov (typically "aws")
# - service: service namespace (e.g., connect, lambda, s3, iam)
# - region: region code (e.g., us-east-1) or empty for global services
# - account-id: 12-digit account number or empty for some services
# - resource: can be resource-id, resource-type/resource-id, or resource-type:resource-id
#
# Reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html
aws_arn_regex = r"^arn:aws[a-z\-]*:[a-zA-Z0-9\-]+:[a-zA-Z0-9\-]*:[0-9]*:.+$"
uuid_regex = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def build_metadata_displayname_map(metadata):
    """Extract displayNames from metadata for correlation with ARNs."""
    display_map = {}
    
    if not metadata or "ActionMetadata" not in metadata:
        return display_map
    
    action_metadata = metadata["ActionMetadata"]
    
    for action_id, action_data in action_metadata.items():
        if "parameters" in action_data:
            params = action_data["parameters"]
            for param_key, param_value in params.items():
                if isinstance(param_value, dict) and "displayName" in param_value:
                    # Store the displayName indexed by the parameter key (e.g., "ContactFlowId")
                    display_name = param_value["displayName"]
                    # Check if displayName is actually an ARN (shouldn't be but just in case)
                    if not re.match(aws_arn_regex, display_name):
                        # Store by action_id and param_key for later matching
                        display_map[f"{action_id}.{param_key}"] = display_name
    
    return display_map


def collect_arns(obj, metadata_map, arn_list=None, path="", action_id=None):
    """Recursively collect all ARNs from the flow structure."""
    if arn_list is None:
        arn_list = []
    
    if isinstance(obj, dict):
        # Check if we're at an Action level (has Identifier field)
        if "Identifier" in obj:
            action_id = obj["Identifier"]
        
        for key, value in obj.items():
            if isinstance(value, str) and re.match(aws_arn_regex, value):
                # Try to find displayName from metadata
                display_name = None
                if action_id:
                    metadata_key = f"{action_id}.{key}"
                    display_name = metadata_map.get(metadata_key)
                
                arn_list.append({
                    "arn": value,
                    "display_name": display_name,
                    "path": f"{path}.{key}" if path else key
                })
            collect_arns(value, metadata_map, arn_list, f"{path}.{key}" if path else key, action_id)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            collect_arns(item, metadata_map, arn_list, f"{path}[{i}]", action_id)
    
    return arn_list


def build_arn_to_variable_map(arn_list, verbose=False):
    """Build a map of ARNs to their Terraform variable references."""
    arn_map = {}
    resource_counters = {}
    
    for arn_info in arn_list:
        arn = arn_info["arn"]
        display_name = arn_info["display_name"]
        
        # Skip if already processed
        if arn in arn_map:
            continue
        
        # Parse the ARN
        arn_parts = arn.split(":", 5)
        service = arn_parts[2]
        resource_info = arn_parts[5]
        
        resource_type = None
        resource_id = None
        
        # Extract resource type and ID
        if "/" in resource_info:
            parts = resource_info.split("/")
            if len(parts) >= 3:
                resource_type = parts[-2]
                resource_id = parts[-1]
            else:
                resource_type = parts[0]
                resource_id = parts[-1]
        elif ":" in resource_info:
            parts = resource_info.split(":", 1)
            resource_type = parts[0]
            resource_id = parts[1]
        else:
            resource_type = service
            resource_id = resource_info
        
        # Generate variable name
        if re.match(uuid_regex, resource_id):
            # UUID - use displayName if available, otherwise counter
            if display_name:
                var_name = display_name.lower()
                var_name = re.sub(r'[^a-z0-9_]+', '_', var_name)
                var_name = re.sub(r'_+', '_', var_name)
                var_name = var_name.strip('_')
            else:
                counter_key = resource_type.replace("-", "_")
                resource_counters[counter_key] = resource_counters.get(counter_key, 0) + 1
                var_name = f"{counter_key}_{resource_counters[counter_key]}"
        else:
            var_name = resource_id.replace('-', '_')
        
        # Create dynamic reference
        dynamic_ref = f"${{{resource_type.replace('-', '_')}_{var_name}}}"
        arn_map[arn] = dynamic_ref
        
        if verbose:
            # Truncate ARN if too long to keep output on one line
            arn_display = f"...{arn[-80:]}" if len(arn) > 80 else arn
            display_info = f" ({display_name})" if display_name else ""
            print(f"{arn_display}{display_info} -> {dynamic_ref}")
    
    return arn_map


def replace_arns_in_flow(obj, arn_map):
    """Replace all ARNs in the flow with their variable references."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value in arn_map:
                obj[key] = arn_map[value]
            else:
                replace_arns_in_flow(value, arn_map)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and item in arn_map:
                obj[i] = arn_map[item]
            else:
                replace_arns_in_flow(item, arn_map)


if __name__ == "__main__":
    # args parsing and main logic here

    parser = argparse.ArgumentParser(description="convert static references in Amazon Connect Contact Flows to use dynamic references.")
    # if --dry-run or -d , we wont write an output file
    parser.add_argument("--dry-run", "-d", action="store_true", help="If set, do not write output file.")
    # the user must provide an input file or directory
    parser.add_argument("--input-file", "-i", help="Path to the input Contact Flow JSON file.")
    # process an entire directory of flow files
    parser.add_argument("--input-dir", help="Path to directory containing Contact Flow JSON files. Will process all .json files.")
    # the user can override the default output file name, if this is not provided, we will use input file name with .out.json suffix
    parser.add_argument("--output-file", "-o", help="output file name. If not provided, will use input file name with .out.json suffix.")
    # output directory for batch processing
    parser.add_argument("--output-dir", help="Output directory for processed files (used with --input-dir). Default: same as input directory.")
    # --print-keys or -p will print all the arns and the keys we would use for dynamic references
    parser.add_argument("--print-keys", "-p", action="store_true", help="If set, print all ARNs and their corresponding dynamic reference keys.")
    # --verbose or -v will print more detailed information during processing
    parser.add_argument("--verbose", "-v", action="store_true", help="If set, print more detailed information during processing.")
    # --update-metadata or -m will also update ARNs in the Metadata section (by default only Actions are updated)
    parser.add_argument("--update-metadata", "-m", action="store_true", help="If set, also update ARNs in the Metadata section. By default, only the Actions section is updated.")

    args = parser.parse_args()

    # Validate input arguments
    if not args.input_file and not args.input_dir:
        parser.error("Either --input-file or --input-dir must be specified")
    if args.input_file and args.input_dir:
        parser.error("Cannot specify both --input-file and --input-dir")
    if args.output_file and args.input_dir:
        parser.error("Cannot use --output-file with --input-dir. Use --output-dir instead.")

    # Get list of files to process
    import os
    from pathlib import Path
    
    if args.input_dir:
        input_path = Path(args.input_dir)
        if not input_path.is_dir():
            print(f"Error: Directory '{args.input_dir}' not found.")
            exit(1)
        
        # Find all JSON files, excluding .out.json files
        json_files = [f for f in input_path.glob("*.json") if not f.name.endswith('.out.json')]
        if not json_files:
            print(f"Error: No .json files found in '{args.input_dir}'")
            exit(1)
        
        files_to_process = [(str(f), None) for f in json_files]
        output_dir = Path(args.output_dir) if args.output_dir else input_path
        
        if args.verbose:
            print(f"Found {len(files_to_process)} JSON file(s) in {args.input_dir}")
    else:
        # Single file mode
        if not Path(args.input_file).exists():
            print(f"Error: Input file '{args.input_file}' not found.")
            exit(1)
        files_to_process = [(args.input_file, args.output_file)]
        output_dir = None

    # Process each file
    for input_file, output_file in files_to_process:
        if len(files_to_process) > 1:
            print(f"\n{'='*80}")
            print(f"Processing: {Path(input_file).name}")
            print('='*80)
        
        # Load the input JSON file
        try:
            with open(input_file, 'r') as f:
                contact_flow_json = json.load(f)
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found.")
            continue
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{input_file}': {e}")
            continue

        if args.verbose:
            print(f"Loaded contact flow from: {input_file}")

        # Step 1: Build metadata displayName map
        if args.verbose:
            print("\nStep 1: Extracting metadata...")
        metadata_map = build_metadata_displayname_map(contact_flow_json.get("Metadata", {}))
        
        # Step 2: Collect all ARNs from the flow
        if args.verbose:
            print("Step 2: Collecting ARNs...")
        
        if args.update_metadata:
            if args.verbose:
                print("Scanning both Actions and Metadata sections...")
            arn_list = collect_arns(contact_flow_json, metadata_map)
        else:
            if args.verbose:
                print("Scanning only Actions section...")
            arn_list = collect_arns(contact_flow_json.get("Actions", []), metadata_map)
        
        if args.verbose:
            print(f"Found {len(arn_list)} ARN(s)\n")
        
        # Step 3: Build ARN to variable mapping
        if args.verbose:
            print("Step 3: Building variable mappings...")
        arn_map = build_arn_to_variable_map(arn_list, verbose=args.verbose)
        
        if args.print_keys:
            print("\nARN to Variable Mappings:")
            print("-" * 80)
            for arn, var_ref in arn_map.items():
                arn_display = f"...{arn[-80:]}" if len(arn) > 80 else arn
                print(f"{arn_display}\n  -> {var_ref}\n")
            if len(files_to_process) == 1:
                exit(0)
            continue
        
        # Step 4: Replace ARNs with variable references
        if args.verbose:
            print("\nStep 4: Replacing ARNs in flow...")
        
        if args.update_metadata:
            replace_arns_in_flow(contact_flow_json, arn_map)
        else:
            if "Actions" in contact_flow_json:
                replace_arns_in_flow(contact_flow_json["Actions"], arn_map)
        
        # Step 5: Write output
        if not args.dry_run:
            # Determine output file path
            if output_file:
                # Single file mode with explicit output
                output_path = output_file
            elif args.input_dir:
                # Directory mode - generate output filename
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filename = Path(input_file).name.replace('.json', '.out.json')
                output_path = str(output_dir / output_filename)
            else:
                # Single file mode without explicit output
                output_path = input_file.replace('.json', '.out.json')
            
            with open(output_path, 'w') as f:
                json.dump(contact_flow_json, f, indent=2)
            print(f"\nOutput written to: {output_path}")
        else:
            print("\nDRY RUN - No files written")
