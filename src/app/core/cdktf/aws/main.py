#!/usr/bin/env python
import os
import subprocess

from cdktf import App

from ....schemas.openlabs import OpenLabsRange
from .aws_stack import AWSStack


def deploy_infrastructure() -> None:
    """Runs `terraform deploy --auto-approve` programmatically."""  # noqa: D401
    # Change directory to `cdktf.out`
    os.chdir("cdktf.out")

    # Run Terraform commands
    print("unning terraform init...")
    subprocess.run(["terraform", "init"], check=True)

    print("Running terraform apply...")
    subprocess.run(["terraform", "apply", "--auto-approve"], check=True)

    print("Terraform apply complete!")


def create_aws_stack(cyber_range: OpenLabsRange) -> None:
    """Create and synthesize an AWS stack using the provided OpenLabsRange.

    Args:
    ----
        cyber_range (OpenLabsRange): OpenLabs compliant range object.

    """
    app = App()
    AWSStack(app, "aws", cyber_range)

    app.synth()
    # Call the function to deploy the terraform
    deploy_infrastructure()
