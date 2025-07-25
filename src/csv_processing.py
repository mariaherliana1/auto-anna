from typing import Optional

import pandas as pd

from src.CallDetail import CallDetail
from src.utils import parse_jakarta_datetime, convert_to_jakarta_time_iso, parse_phone_number, call_hash, set_if_empty, parse_iso_datetime
import math


def process_dashboard_csv(
    file_path: str, carrier: str, call_details: Optional[dict[str, CallDetail]] = None, client: str = ""
) -> dict[str, CallDetail]:
    if call_details is None:
        call_details = {}

    print(f"- Reading dashboard file {file_path}...")
    df1 = pd.read_csv(file_path, low_memory=False).astype(str)
    for index, row in df1.iterrows():
        call_detail = CallDetail(
            client=client,
            sequence_id=row["Sequence ID"],
            user_name=row["User name"],
            call_from=parse_phone_number(row["Call from"]),
            call_to=parse_phone_number(row["Call to"]),
            call_type=row["Call type"],
            dial_start_at=row["Dial begin time"],
            dial_answered_at=row["Call begin time"],
            dial_end_at=row["Call end time"],
            ringing_time=row["Ringing time"],
            call_duration=row["Call duration"],
            call_memo=row["Call memo"],
            call_charge="0",
            carrier=carrier,
        )
        key = call_detail.final_key  # ✅ use final_key
        if key in call_details:
            existing_call_detail = call_details[key]
            existing_call_detail.user_name = row["User name"]
            existing_call_detail.call_memo = row["Call memo"]
            # ✅ Dashboard is fallback only for call_to
            existing_call_detail.call_to = set_if_empty(existing_call_detail.call_to, call_detail.call_to)
        else:
            call_details[key] = call_detail
    return call_details

def process_console_csv(
    file_path: str, carrier: str, call_details: dict[str, CallDetail], client: str = ""
) -> dict[str, CallDetail]:
    df2 = pd.read_csv(file_path, low_memory=False).astype(str)

    call_type_mapping = {
        "OUTGOING_CALL": "Outbound call",
        "OUTGOING_CALL_ABSENCE": "Outbound call (Missed)",
    }

    for index, row in df2.iterrows():
        normalized_call_from = parse_phone_number(row["used_number"])
        normalized_call_to = parse_phone_number(row["number"])

        # Use call_hash as fallback only for key if no IDs
        temp_call = CallDetail(
            client=client,
            sequence_id=row["call_id"],
            user_name="-",
            call_from=normalized_call_from,
            call_to=normalized_call_to,
            call_type=call_type_mapping.get(row["call_type"], row["call_type"]),
            dial_start_at=parse_jakarta_datetime(row["dial_starts_at"], row["pbx_region"]),
            dial_answered_at=parse_jakarta_datetime(row["dial_answered_at"], row["pbx_region"]),
            dial_end_at=parse_jakarta_datetime(row["dial_ends_at"], row["pbx_region"]),
            ringing_time=row["all_duration_of_call_sec_str"],
            call_duration=row["duration_of_call_sec_str"],
            call_memo="",
            call_charge=row["discount"],
            carrier=carrier,
            number_type=row["number_type"],
        )
        key = temp_call.final_key  # ✅ CORRECT variable

        if key in call_details:
            call_detail = call_details[key]

            if temp_call.call_to:
                call_detail.call_to = temp_call.call_to

            call_detail.call_type = temp_call.call_type
            call_detail.dial_answered_at = temp_call.dial_answered_at
            call_detail.dial_end_at = temp_call.dial_end_at
            call_detail.ringing_time = temp_call.ringing_time
            call_detail.call_duration = temp_call.call_duration
            call_detail.call_charge = temp_call.call_charge
            call_detail.number_type = temp_call.number_type
        else:
            call_details[key] = temp_call

    return call_details

def process_merged_csv(
    file_path: str, call_details: dict[str, CallDetail], carrier: str
) -> dict[str, CallDetail]:
    print(f"- Reading {file_path} file...")
    df3 = pd.read_csv(file_path, low_memory=False).astype(str)
    print("- Processing merged CSV file...")

    for index, row in df3.iterrows():
        merged_call = CallDetail(
            sequence_id=row.get("call_id") or row.get("Sequence ID"),
            user_name=row["User name"],
            call_from=parse_phone_number(row["Call from"]),
            call_to=parse_phone_number(row["Call to"]),
            call_type=row["Call type"],
            dial_start_at=parse_iso_datetime(row["Dial starts at"]),
            dial_answered_at=parse_iso_datetime(row["Dial answered at"]),
            dial_end_at=parse_iso_datetime(row["Dial ends at"]),
            ringing_time=row["Ringing time"],
            call_duration=row["Call duration"],
            call_memo=row["Call memo"],
            call_charge=row["Call charge"],
            carrier=carrier,
            number_type="",
            client=""
        )
        key = merged_call.final_key

        if key in call_details:
            call_detail = call_details[key]

            # ✅ Merged is fallback only for call_to
            call_detail.call_to = set_if_empty(call_detail.call_to, merged_call.call_to)

            # ✅ Other fields: always overwrite with merged version
            call_detail.user_name = merged_call.user_name
            call_detail.call_from = merged_call.call_from  # optional: fallback if you prefer
            call_detail.call_type = merged_call.call_type
            call_detail.dial_start_at = merged_call.dial_start_at
            call_detail.dial_answered_at = merged_call.dial_answered_at
            call_detail.dial_end_at = merged_call.dial_end_at
            call_detail.ringing_time = merged_call.ringing_time
            call_detail.call_duration = merged_call.call_duration
            if merged_call.call_memo.strip():
                call_detail.call_memo = merged_call.call_memo
            call_detail.call_charge = merged_call.call_charge

        else:
            call_details[key] = merged_call

    return call_details

def round_up_duration(call_duration: str) -> int:
    try:
        #print(f"Processing call duration: {call_duration}")
        
        if ':' in call_duration:
            h, m, s = map(int, call_duration.split(':'))
            total_minutes = h * 60 + m + math.ceil(s / 60)
        else:
            total_minutes = math.ceil(int(call_duration) / 60)  # Assume it's in seconds
        
        return total_minutes
    except Exception as e:
        print(f"Error parsing call duration: {call_duration}, Error: {e}")
        return 0


def save_merged_csv(call_details: dict[str, CallDetail], output_path: str) -> None:
    print("- Saving merged CSV file...")
    call_details_list = []

    for value in call_details.values():
        call_dict = value.to_dict()
        call_dict["Round up duration"] = round_up_duration(call_dict["Call duration"])
        call_details_list.append(call_dict)

    df = pd.DataFrame(call_details_list)
    df.to_csv(output_path, index=False)
    print(f"- Merged CSV saved to {output_path}")