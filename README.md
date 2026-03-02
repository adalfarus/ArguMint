# ArguMint
 A fresh new way to handle cli. 
 
This package is just maintained (EOL) as I have rewritten large parts of the package (2k new LOC) and plan to release them under the new name autocli. This could take a 1-2 months though as the old owner of the name seems unresponsive.

I have also updated it with the latest code from aplustools.package.autocli and applied a few patches for common errors for now.

## How to use it
```python
from argumint import ArgStruct, ArguMint
from typing import Literal
import sys

def sorry(*args, **kwargs):
    print("Not implemented yet, sorry!")

def help_text():
    print("Build -> dir/file or help.")

def build_file(path: Literal["./main.py", "./file.py"] = "./main.py", num: int = 0):
    """
    build_file
    :param path: The path to the file that should be built.
    :param num:
    :return None:
    """
    print(f"Building file {path} ..., {num}")

from aplustools.package import timid

timer = timid.TimidTimer()

arg_struct = {'apt': {'build': {'file': {}, 'dir': {'main': {}, 'all': {}}}, 'help': {}}}

# Example usage
builder = ArgStruct()
builder.add_command("apt")
builder.add_nested_command("apt", "build", "file")

builder.add_nested_command("apt.build", "dir", {'main': {}, 'all': {}})
# builder.add_subcommand("apt.build", "dir")
# builder.add_nested_command("apt.build.dir", "main")
# builder.add_nested_command("apt.build.dir", "all")

builder.add_command("apt.help")
# builder.add_nested_command("apt", "help")

print(builder.get_structure())  # Best to cache this for better times (by ~15 microseconds)

parser = ArguMint(default_endpoint=sorry, arg_struct=arg_struct)
parser.add_endpoint("apt.help", help_text)

parser.add_endpoint("apt.build.file", build_file)

sys.argv[0] = "apt"

# Testing
# sys.argv = ["apt", "help"]
# sys.argv = ["apt", "build", "file", "./file.py", "--num=19"]
parser.parse_cli(sys, "native_light")
print(timer.end())
```
