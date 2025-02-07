#!/usr/bin/env python
import os
import subprocess
import tempfile
import shutil
from time import sleep
from pathlib import Path


from cdktf import App

from ....schemas.openlabs import OpenLabsRange
from .aws_stack import AWSStack


def deploy_infrastructure(dir: str, stack_name: str) -> str:
    """Runs `terraform deploy --auto-approve` programmatically.
    
    Args:
    ----
        dir (str): Output directory.
        
    Returns:
    -------
        str: Content of the terraform state file.

    """
    inital_dir = os.getcwd()
    
    # Change to directory with `cdk.tf.json`
    synth_output_dir = Path(f"{dir}/stacks/{stack_name}")
    os.chdir(synth_output_dir)
    state_file = synth_output_dir / Path(f"terraform.{stack_name}.tfstate")

    # Run Terraform commands
    print("Running terraform init...")
    subprocess.run(["terraform", "init"], check=True)

    print("Running terraform apply...")
    subprocess.run(["terraform", "apply", "--auto-approve"], check=True)
    print("Terraform apply complete!")

    # Read state file into string
    content = ""
    with open(state_file, "r", encoding="utf-8") as file:
        content = file.read()

    # Remove terraform build files
    os.chdir(inital_dir)
    shutil.rmtree(dir)
    return content

# def destroy_infrastructure(cyber_range: OpenLabsRange, state: str) -> bool: # TODO: 
#     """Destroy terraform infrastructure.
#    
#     Args:
#     ----
#       cyber_range (OpenLabsRange): Range to delete.
#       state (str): State file content.
# 
#     Returns:
#     -------
#       bool: True if successfully destroyed. False otherwise.       
# 
#     """
#     subprocess.run(["terraform", "destroy", "--auto-approve", f"-state={str(state_file_path)}"], check=True)

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

    app = App(outdir=tmp_dir)
    AWSStack(app, cyber_range.name, cyber_range, tmp_dir)

    app.synth()

    return tmp_dir
