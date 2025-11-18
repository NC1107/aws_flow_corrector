import argparse
import json
import re


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

def replace_arns(contact_flow_json, verbose=False):
    
    for key, value in contact_flow_json.items():
        if isinstance(value,str):
            # this means we have a key value pair
            # where the value could be an arn, we will check for that here
            if re.match(aws_arn_regex, value):
                # we have found an arn, we will now extract the resource type and resource id
                arn_parts = value.split(":", 5)  # Split only first 5 colons to preserve resource part
                service = arn_parts[2]  # e.g., "lambda", "connect", "s3"
                resource_info = arn_parts[5]  # this is the part after the account id (everything remaining)
                
                # Resource can be in format: resource-type/resource-id, resource-type:resource-id, or just resource-id
                if "/" in resource_info:
                    # Format: resource-type/resource-id (e.g., instance/.../contact-flow/id)
                    parts = resource_info.split("/")
                    # For nested resources, use the last resource type and id
                    if len(parts) >= 3:
                        resource_id = parts[-1]
                    else:
                        resource_id = parts[-1]
                elif ":" in resource_info:
                    # Format: resource-type:resource-id (e.g., function:state-lookup)
                    # Use the resource-id as the identifier
                    resource_id = resource_info.split(":", 1)[1]
                else:
                    # Just a resource-id without type (e.g., some IAM resources)
                    resource_id = resource_info
                
                # now we will create the dynamic reference using service.resource_id
                dynamic_reference = f"${{{service.replace('-', '_')}.{resource_id.replace('-', '_')}}}"
                if verbose:
                    print(f"Replacing ARN: {value} with Dynamic Reference: {dynamic_reference}")
                contact_flow_json[key] = dynamic_reference

        if isinstance(value, dict):
            # recursively process nested dictionaries, as there could be arns deeper in the structure
            replace_arns(value, verbose)
        if isinstance(value, list):
            # recursively process lists, as there could be arns deeper in the structure
            for item in value:
                if isinstance(item, dict):
                    replace_arns(item, verbose)
    return contact_flow_json

    


if __name__ == "__main__":
    # args parsing and main logic here

    parser = argparse.ArgumentParser(description="convert static references in Amazon Connect Contact Flows to use dynamic references.")
    # if --dry-run or -d , we wont write an output file
    parser.add_argument("--dry-run", "-d", action="store_true", help="If set, do not write output file.")
    # the user must provide an input file
    parser.add_argument("--input-file", "-i", required=True, help="Path to the input Contact Flow JSON file.")
    # the user can override the default output file name, if this is not provided, we will use input file name with .out.json suffix
    parser.add_argument("--output-file", "-o", help="output file name. If not provided, will use input file name with .out.json suffix.")
    # --print-keys or -p will print all the arns and the keys we would use for dynamic references
    parser.add_argument("--print-keys", "-p", action="store_true", help="If set, print all ARNs and their corresponding dynamic reference keys.")
    # --verbose or -v will print more detailed information during processing
    parser.add_argument("--verbose", "-v", action="store_true", help="If set, print more detailed information during processing.")
    # --update-metadata or -m will also update ARNs in the Metadata section (by default only Actions are updated)
    parser.add_argument("--update-metadata", "-m", action="store_true", help="If set, also update ARNs in the Metadata section. By default, only the Actions section is updated.")

    args = parser.parse_args()

    # Load the input JSON file
    try:
        with open(args.input_file, 'r') as f:
            contact_flow_json = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.input_file}': {e}")
        exit(1)

    if args.verbose:
        print(f"Loaded contact flow from: {args.input_file}")

    # Process the contact flow - only process Actions by default, or both if --update-metadata is set
    if args.update_metadata:
        if args.verbose:
            print("Processing both Actions and Metadata sections...")
        result = replace_arns(contact_flow_json, verbose=args.verbose)
    else:
        if args.verbose:
            print("Processing only Actions section...")
        # Only process the Actions section
        if "Actions" in contact_flow_json:
            contact_flow_json["Actions"] = replace_arns({"Actions": contact_flow_json["Actions"]}, verbose=args.verbose)["Actions"]
        result = contact_flow_json

    # TODO: Handle the result, print keys if requested, write output file if not dry-run
