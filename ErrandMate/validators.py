import re


def check_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Email format is wrong. Example: name@email.com"
    return True, ""


def check_phone(phone):
    cleaned = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not cleaned.isdigit():
        return False, "Phone number should only contain digits, spaces or dashes"
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Phone number should be between 10 and 15 digits"
    return True, ""


def check_password(pw):
    if len(pw) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in pw):
        return False, "Password must have at least one uppercase letter"
    if not any(c.isdigit() for c in pw):
        return False, "Password must contain at least one number"
    return True, ""


def check_name(name):
    if len(name.strip()) < 2:
        return False, "Name is too short"
    if any(char.isdigit() for char in name):
        return False, "Name should not contain numbers"
    return True, ""
