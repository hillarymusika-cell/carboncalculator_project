SPECIAL_CHARS = set("`-=/.;!@#$%^&*():><?+_\"'~£¢€¥√π§∆{}°®©✓[|•÷™]")


def v_password(password: str) -> tuple[bool, str]:
    if not isinstance(password, str) or not password:
        return False, "Password is required."

    if len(password) < 8:
        return False, "Password must be at least eight characters."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one numeric character."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one upper case character."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lower case character."
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter."
    if not any(c in SPECIAL_CHARS for c in password):
        return False, "Password must contain at least one special character."

    return True, "OK"
