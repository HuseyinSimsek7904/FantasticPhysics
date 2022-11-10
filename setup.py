import cx_Freeze

executables = [cx_Freeze.Executable("main.py", base=None)]

packages = ["pygame", "math", "typing", "random"]
options = {
    'build_exe': {
        'packages': packages,
    },
}

cx_Freeze.setup(
    name="Fantastic Physics",
    options=options,
    version="1.0",
    description="",
    executables=executables,
)
