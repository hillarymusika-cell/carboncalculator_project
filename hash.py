"""
Dev utility: print a password hash for manually seeding the database.

The original hardcoded a real-looking password ("mypassword123") right
in source control. Use it as a CLI tool instead so nothing sensitive
gets committed:

    python hash.py "MyS3cret!Pass"
"""
import sys
import getpass

from werkzeug.security import generate_password_hash


def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Password to hash: ")

    if not password:
        print("No password provided.", file=sys.stderr)
        sys.exit(1)

    print(generate_password_hash(password))


if __name__ == "__main__":
    main()
