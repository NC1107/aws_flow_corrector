# AWS Flow Corrector

A tool for converting static Amazon Connect contact flows into templatable versions that can use Terraform's `templatefile` function for multi-environment deployments.

## Overview

AWS Flow Corrector analyzes Amazon Connect contact flow JSON files and converts hardcoded values (like ARNs, phone numbers, queue IDs) into template variables, making it easy to deploy the same flow across different environments (dev, staging, production) using Terraform.

## Features

- Converts static contact flows to templatable format
- Supports Terraform `templatefile` function
- Identifies and extracts environment-specific values
- Generates variable definition files

## Installation

```bash
# Installation instructions coming soon
```

## Usage

```bash
# Usage instructions coming soon
```

## Requirements

- Python 3.8+
- Amazon Connect flow JSON files
- Terraform (for deployment)

## License

MIT
