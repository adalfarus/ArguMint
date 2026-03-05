# ArguMint
 A fresh new way to handle cli. 
 
This package is just maintained (EOL) as I have rewritten large parts of the package (2k new LOC) and plan to release them under the new name autocli. This could take a 1-2 months though as the old owner of the name seems unresponsive.

I have also updated it with the latest code from aplustools.package.autocli and applied a few patches and quality of life enhancements.

The latest release 2.0.0 brings with it a totally new and more refined interface for managing the cli. These enhancements are from the new 'autocli' package.

This is done so that an MVP of autocli exists, that can always be used in cases where using autocli may not be preferable. For example, in a minimal project the argumint.py file can easily be included while using the entire autocli directory could be more cumbersome.

Another reason is so that projects using argumint can slowly transition to autocli, while we wait for the name to be possibly available.

## How to use it

```python
from argumint import Interface, ArgumentParsingError
from typing import Literal


def build_file(path: Literal["./main.py", "./file.py"] = "./main.py", num: int = 0) -> None:
    """
    build_file
    :param path: The path to the file that should be built.
    :param num:
    :return None:
    """
    print(f"Building file {path} ..., {num}")


def print_program_help() -> None:
    print("This is the CLI for aps, and it does ... and ... .")


from chronix import FlexTimer

timer = FlexTimer()

# Initialization
parser = Interface("aps", path_seperator="::")

# Add endpoints / paths
parser.path("build::file", build_file)
parser.path("build::dir::main")
parser.path("build::dir::all")
parser.path("help", print_program_help)

# Testing
try:
    print("---- 1 ----")
    parser.parse_cli(["main.py", "help"])  # Displays program help
    print(timer.lap().to_readable())
    print("---- 2 ----")
    parser.parse_cli(["main.py", "build", "file", "./file.py", "--num", "19"])
    print(timer.lap().to_readable())
    print("---- 3 ----")
    parser.parse_cli()  # Displays cli help
    print(timer.lap().to_readable())
    print("---- 4 ----")  # Warning about native_light mode and error
    parser.parse_cli(["main.py", "build", "file", "./file.py", "--num", "=", "19"], "native_light")
    print(timer.lap().to_readable())
except ArgumentParsingError as e:
    print(f"There was an error while parsing '{e}'.")
timer.end()
```
