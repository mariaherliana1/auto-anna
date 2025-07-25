from datetime import datetime, timedelta, timezone
from typing import Optional
from dateutil.parser import parse
import pytz

from src.idn_area_codes import EMERGENCY_NUMBERS, PHONE_PREFIXES, INTERNATIONAL_PHONE_PREFIXES

SPECIAL_PREFIXES = [211500, 211400, 21150, 21140, 1500, 1400, 800, 84, 31, 21, 8]

def call_hash(call_from: str, call_to: str, dial_start_at) -> str:
    # Accept str or datetime
    if isinstance(dial_start_at, str):
        dt = parse(dial_start_at)
    elif isinstance(dial_start_at, datetime):
        dt = dial_start_at
    else:
        raise ValueError(f"Unsupported type for dial_start_at: {type(dial_start_at)}")

    # Normalize to UTC + remove microseconds + round to seconds
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    dt = dt.astimezone(pytz.UTC)
    dt = dt.replace(microsecond=0)

    normalized_iso = dt.isoformat()
    return f"{call_from}|{call_to}|{normalized_iso}"

def convert_to_jakarta_time_iso(original_date_str: str, region: str) -> datetime:
    if region != "jkt":
        raise Exception(
            "Timezone not supported. Only Jakarta time is supported for now."
        )

    # Parse the original date string in UTC time
    original_date = datetime.strptime(original_date_str, "%Y-%m-%d %H:%M:%S")
    utc_timezone = timezone.utc
    original_date_utc = original_date.replace(tzinfo=utc_timezone)

    # Add 7 hours to the original date to convert it to Jakarta time
    jakarta_offset = timedelta(hours=7)
    jakarta_date = original_date_utc + jakarta_offset
    jakarta_date = jakarta_date.replace(tzinfo=timezone(timedelta(hours=7)))
    return jakarta_date

import phonenumbers

def parse_phone_number(phone_number: int | str) -> int | str:
    if isinstance(phone_number, int):
        return phone_number

    if phone_number == "scancall":
        return "scancall"

    # Remove unwanted chars
    cleaned_number = (
        phone_number.replace("+", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace(" ", "")
    )

    # Remove country code 62 if present
    if cleaned_number.startswith("62"):
        normalized = cleaned_number[2:]
    # Remove leading 0 if present
    elif cleaned_number.startswith("0"):
        normalized = cleaned_number[1:]
    else:
        normalized = cleaned_number

    try:
        return int(normalized)
    except ValueError:
        return normalized

def classify_number(phone_number: int, call_type: str, call_from: str, call_to: str, console_number_type: str = "") -> str:
    phone_number_str = str(phone_number)

    # Classify based on call type
    if call_type in ["Internal Call", "EXTENSION"]:
        return "Internal Call"
    if call_type == "Internal Call (No answer)":
        return "Internal Call (No answer)"
    if call_type == "AUTOMATIC_RECORD":
        return "Voicemail"
    if call_type == "AUTOMATIC_TRANSFER":
        return "Automatic Transfer"
    if call_type == "Monitoring":
        return "Monitoring"
    if call_from == "scancall":
        return "scancall"
    if call_type == "Call transfer" and len(str(call_from)) == 3 and str(call_from).isdigit():
        return "Internal Call"

    # Console number type decides international vs local
    if console_number_type.upper() == "OVERSEAS":
        for prefix, country in INTERNATIONAL_PHONE_PREFIXES.items():
            if phone_number_str.startswith(str(prefix).replace("+", "")):
                return f"International - {country}"
        return "International - Unknown"

    # Local: emergency number
    if len(phone_number_str) in [3, 4, 5]:
        classification = EMERGENCY_NUMBERS.get(phone_number)
        if classification:
            return classification

    # Local: phone prefixes
    sorted_prefixes = sorted(map(str, PHONE_PREFIXES.keys()), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if phone_number_str.startswith(prefix):
            return PHONE_PREFIXES.get(int(prefix))

    # Local: special prefixes
    for prefix in SPECIAL_PREFIXES:
        if phone_number_str.startswith(str(prefix)):
            return PHONE_PREFIXES.get(prefix)

    # If all else fails, assume it's a valid fixed/mobile number
    if len(phone_number_str) >= 8:  # simple check: long enough to be a real number
        return "Fixed/Mobile"
    return "Unknown number type"

def format_datetime_as_human_readable(datetime_object: Optional[datetime]) -> str:
    return datetime_object.strftime("%Y-%m-%d %H:%M:%S") if datetime_object else "-"

def format_datetime_as_iso(datetime_object: datetime) -> str: 
    return str(datetime_object).replace(" ", "T")

def format_timedelta(time_duration: timedelta) -> str:
    time_duration_str = str(time_duration)
    time_parts = time_duration_str.split(", ")
    time_str = time_parts[-1]
    return time_str

def format_username(user_name: str) -> str:
    return user_name if user_name else "-"

def parse_call_memo(memo: str) -> str:
    if memo == "" or memo == "nan":
        return "-"
    return memo

def parse_iso_datetime(datetime_input: str | datetime | None) -> datetime | None:
    if datetime_input is None or datetime_input == "-":
        return None
    if isinstance(datetime_input, datetime):
        return datetime_input
    return datetime.fromisoformat(datetime_input)

def parse_jakarta_datetime(datetime_str: str, region: str) -> Optional[datetime]:
    if datetime_str == "nan":
        return None
    return convert_to_jakarta_time_iso(datetime_str, region)

def parse_time_duration(time_duration_string: str) -> timedelta:
    hours, minutes, seconds = time_duration_string.split(":")
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))

def set_if_empty(current_value, new_value):
    """Return new_value if current_value is empty or None, else keep current_value."""
    return new_value if not current_value and new_value else current_value