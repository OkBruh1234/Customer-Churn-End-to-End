import re


MAX_USER_NAME_LENGTH = 60
MAX_SINGLE_WORD_NAME_LENGTH = 24
NAME_ALLOWED_PATTERN = re.compile(r"^[A-Z][A-Za-z]*(?:[ '-][A-Z][A-Za-z]*)*$")


def normalize_user_name(name):
    return " ".join(name.strip().split())


def validate_user_name(name):
    cleaned_name = normalize_user_name(name)

    if not cleaned_name:
        raise ValueError("Name cannot be empty.")

    if len(cleaned_name) < 2:
        raise ValueError("Name must be at least 2 characters long.")

    if len(cleaned_name) > MAX_USER_NAME_LENGTH:
        raise ValueError(f"Name cannot be longer than {MAX_USER_NAME_LENGTH} characters.")

    if any(character.isdigit() for character in cleaned_name):
        raise ValueError("Name cannot contain numbers.")

    if cleaned_name[0] != cleaned_name[0].upper():
        raise ValueError("Name must start with a capital letter.")

    if " " not in cleaned_name and len(cleaned_name) > MAX_SINGLE_WORD_NAME_LENGTH:
        raise ValueError(
            "Single-word names cannot be longer than "
            f"{MAX_SINGLE_WORD_NAME_LENGTH} characters."
        )

    if not NAME_ALLOWED_PATTERN.fullmatch(cleaned_name):
        raise ValueError(
            "Use only letters, spaces, apostrophes, or hyphens, and start each name part with a capital letter."
        )

    return cleaned_name
