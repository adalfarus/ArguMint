# ArguMint
 A fresh new way to handle cli
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

arg_struct = {'build': {'file': {}, 'dir': {'main': {}, 'all': {}}}, 'help': {}}

# Example usage
builder = ArgStruct()
builder.add_command("build")
builder.add_subcommand("build", "file")

builder.add_nested_command("build", "dir", {'main': {}, 'all': {}})
# builder.add_subcommand("build", "dir")
# builder.add_nested_command("build.dir", "main")
# builder.add_nested_command("build.dir", "all")

builder.add_command("help")

print(builder.get_structure())  # Best to cache this for better times (by ~15 microseconds)

parser = ArguMint(default_endpoint=sorry, arg_struct=arg_struct)
parser.add_endpoint("help", help_text)

parser.add_endpoint("build.file", build_file)

# If it's a script, the first argument is the script location, but if it's a command it's not in the list
sys.argv = ["build", "file", "./file.py", "--num=19"]  # sys.argv[1:]  # To fix it not being a command yet
parser.parse_cli(sys, "native_light")
print(timer.end())
```
