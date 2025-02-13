import os
import shutil
import subprocess
import uuid
from pathlib import Path

from cdktf import App

from ....schemas.openlabs_range_schema import OpenLabsRangeSchema
from .aws_stack import AWSStack


def deploy_infrastructure(
    stack_dir: str, stack_name: str
) -> (
    None
):  # work on possibly returning something in the future for caching purposes (state file)
    """Run `terraform deploy --auto-approve` programmatically.

    Args:
    ----
        stack_dir (str): Output directory.
        stack_name (str): Name of stack used to deploy the range (format: <range name>-<range id>).

    Returns:
    -------
        None

    """
    inital_dir = os.getcwd()

    # Change to directory with `cdk.tf.json`
    synth_output_dir = Path(f"{stack_dir}/stacks/{stack_name}")
    os.chdir(synth_output_dir)
    # state_file = synth_output_dir / Path(f"terraform.{stack_name}.tfstate")

    # Run Terraform commands
    print("Running terraform init...")
    subprocess.run(["terraform", "init"], check=True)

    print("Running terraform apply...")
    subprocess.run(["terraform", "apply", "--auto-approve"], check=True)
    print("Terraform apply complete!")

    # # Read state file into string
    # content = ""
    # with open(state_file, "r", encoding="utf-8") as file:
    #     content = file.read()

    # # Remove terraform build files
    os.chdir(
        inital_dir
    )  # do not delete for now, jsut return to working directory in repo root
    # shutil.rmtree(stack_dir)
    # return content


def destroy_infrastructure(
    stack_dir: str, stack_name: str
) -> None:  # For caching purposes, load in state file possibly from db
    """Destroy terraform infrastructure.

    Args:
    ----
      stack_dir (str): Output directory.
      stack_name (str): Name of stack used to deploy the range (format: <range name>-<range id>) to tear down the range.

    Returns:
    -------
      None

    """
    inital_dir = os.getcwd()
    # Change to directory with `cdk.tf.json` and terraform state file
    synth_output_dir = Path(f"{stack_dir}/stacks/{stack_name}")
    os.chdir(synth_output_dir)

    # Run Terraform commands
    print("Tearing down selected range")
    subprocess.run(["terraform", "destroy", "--auto-approve"], check=True)

    # os.chdir(synth_output_dir.)

    os.chdir(inital_dir)


def create_aws_stack(cyber_range: OpenLabsRangeSchema, tmp_dir: str) -> str:
    """Create and synthesize an AWS stack using the provided OpenLabsRange.

    Args:
    ----
        cyber_range (OpenLabsRange): OpenLabs compliant range object.
        tmp_dir (str): Temporary directory to store CDKTF files.

    Returns:
    -------
        str: Stack name.

    """
    stack_name = cyber_range.name + "-" + str(cyber_range.id)
    app = App(outdir=tmp_dir)
    AWSStack(app, stack_name, cyber_range, tmp_dir)

    app.synth()

    return stack_name
