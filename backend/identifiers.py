USER_ID_PREFIX = "USR"
PREDICTION_ID_PREFIX = "PRED"


def format_user_id(internal_id):
    return f"{USER_ID_PREFIX}-{int(internal_id):06d}"


def format_prediction_id(internal_id):
    return f"{PREDICTION_ID_PREFIX}-{int(internal_id):06d}"


def parse_prediction_id(prediction_id):
    return parse_prefixed_id(prediction_id, PREDICTION_ID_PREFIX)


def parse_user_id(user_id):
    return parse_prefixed_id(user_id, USER_ID_PREFIX)


def parse_prefixed_id(raw_id, prefix):
    if isinstance(raw_id, int):
        return raw_id

    if raw_id.isdigit():
        return int(raw_id)

    expected_prefix = f"{prefix}-"
    if raw_id.startswith(expected_prefix):
        numeric_part = raw_id[len(expected_prefix) :]
        if numeric_part.isdigit():
            return int(numeric_part)

    raise ValueError(f"Invalid {prefix.lower()} ID format.")
