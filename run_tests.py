import os
import sys
from subprocess import run


def main():
    # Set the PYTHONPATH to the src directory
    os.environ["PYTHONPATH"] = "src"

    # Run pytest with the remaining command-line arguments
    result = run(["pytest"] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
