import sys
import getpass
import secrets

from werkzeug.security import generate_password_hash


def main():
    """
    Securely hash a password. Accepts password via getpass or environment
    to prevent command-line argument exposure in process lists.
    """
    if len(sys.argv) > 1:
        # Security: Log warning if password passed via argument
        print(
            "WARNING: Passing passwords as command-line arguments is insecure "
            "and may expose them in process lists.",
            file=sys.stderr,
        )
        password = sys.argv[1]
    else:
        password = getpass.getpass("Password to hash: ")

    if not password:
        print("No password provided.", file=sys.stderr)
        sys.exit(1)

    # Validate password is a string
    if not isinstance(password, str):
        print("Invalid password type.", file=sys.stderr)
        sys.exit(1)

    print(generate_password_hash(password, method="pbkdf2:sha256"))


if __name__ == "__main__":
    main()
