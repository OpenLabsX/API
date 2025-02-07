#!/usr/bin/env python
import os
import subprocess
import tempfile


from cdktf import App

from ....schemas.openlabs import OpenLabsRange
from .aws_stack import AWSStack


def deploy_infrastructure(dir: str) -> None:
    """Runs `terraform deploy --auto-approve` programmatically."""  # noqa: D401
    # Change directory to `cdktf.out`
    os.chdir(dir)
    print(os.getcwd())

    # Run Terraform commands
    print("Running terraform init...")
    subprocess.run(["terraform", "init"], check=True)

    print("Running terraform apply...")
    subprocess.run(["terraform", "apply", "--auto-approve"], check=True)

    print("Terraform apply complete!")


def create_aws_stack(cyber_range: OpenLabsRange) -> str:
    """Create and synthesize an AWS stack using the provided OpenLabsRange.

    Args:
    ----
        cyber_range (OpenLabsRange): OpenLabs compliant range object.
        
    Returns:
    -------
        str: Path to synthesized AWS stack.

    """
    # /tmp/.openlabs-XX/<range uuid>
    tmp_dir = tempfile.mkdtemp(prefix=".openlabs-")

    app = App()
    AWSStack(app, "aws", cyber_range)

    app.synth()

    return tmp_dir
