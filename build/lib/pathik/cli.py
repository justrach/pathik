import os
import sys
from subprocess import run

def main():
    bin_path = os.path.join(os.path.dirname(__file__), 'bin', 'pathik_crawler')
    result = run([bin_path] + sys.argv[1:], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main() 