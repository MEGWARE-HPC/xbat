from setuptools import setup, Command
import subprocess
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop


class GenerateProtoCommand(Command):
    """Custom command to generate Python code from .proto files."""
    description = "generate gRPC code from .proto files"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        directory = "./shared/grpc"
        proto_files = ["xbat.proto"]
        for proto_file in proto_files:
            command = [
                "python",
                "-m",
                "grpc_tools.protoc",
                f"-I{directory}",  # Path where proto files are located
                f"--python_out={directory}",
                f"--grpc_python_out={directory}",
                f"{directory}/{proto_file}",
            ]
            self.announce(f"Running command: {' '.join(command)}", level=3)
            subprocess.check_call(command)

            # Fix the import in the generated xbat_pb2_grpc.py file
            grpc_file = f"{directory}/{proto_file.replace('.proto', '')}_pb2_grpc.py"
            with open(grpc_file, "r") as file:
                content = file.read()
            content = content.replace("import xbat_pb2", "from . import xbat_pb2")
            with open(grpc_file, "w") as file:
                file.write(content)


# Override build_py and develop to include proto code generation
class CustomBuild(build_py):

    def run(self):
        self.run_command(
            "build_proto")  # Run proto generation before the build
        build_py.run(self)  # Proceed with the normal build process


class CustomDevelop(develop):

    def run(self):
        self.run_command(
            "build_proto")  # Run proto generation before the develop install
        develop.run(self)  # Proceed with the normal develop process


setup(
    name="xbat",
    version="1.0.0",
    packages=["xbatctld", "backend", "shared"],
    cmdclass={
        "build_proto": GenerateProtoCommand,
        "build_py": CustomBuild,
        "develop": CustomDevelop,
    },
    install_requires=[
        "grpcio",
        "grpcio-tools",
    ],
)
