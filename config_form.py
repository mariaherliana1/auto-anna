import streamlit as st
import os
import shutil
import tempfile
from pathlib import Path
import re

CONFIG_PY_PATH = "config.py"
UPLOAD_DIR = "uploaded_files"

os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file, subdir):
    path = os.path.join(UPLOAD_DIR, subdir, uploaded_file.name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def generate_config_entry(data):
    return f"""    Files(
        client="{data['client']}",
        dashboard="{data['dashboard']}",
        console="{data['console']}",
        output="{data['output']}",
        carrier="{data['carrier']}",
        number1={repr(data['number1'])},
        number1_rate={data['number1_rate']},
        number1_rate_type="{data['number1_rate_type']}",
        number1_chargeable_call_types={data['number1_chargeable_call_types']},
        number2={repr(data['number2'])},
        number2_rate={data['number2_rate']},
        number2_rate_type="{data['number2_rate_type']}",
        number2_chargeable_call_types={data['number2_chargeable_call_types']},
        rate={data['rate']},
        rate_type="{data['rate_type']}",
        s2c="{data['s2c']}",
        s2c_rate={data['s2c_rate']},
        s2c_rate_type="{data['s2c_rate_type']}",
        chargeable_call_types={data['chargeable_call_types']},
        custom_logic={repr(data['custom_logic'])}
    ),"""

def insert_entry_to_config(entry_text):
    with open(CONFIG_PY_PATH, "r") as f:
        content = f.read()

    new_content = re.sub(r"(CONFIG\s*=\s*\[\n)", r"\1" + entry_text + "\n", content, count=1)

    with open(CONFIG_PY_PATH, "w") as f:
        f.write(new_content)

st.title("🛠 Config.py Editor with File Uploads")

with st.form("config_form"):
    dashboard_file = st.file_uploader("Upload Dashboard CSV", type=["csv"])
    console_file = st.file_uploader("Upload Console CSV", type=["csv"])
    month_folder = st.text_input("Folder prefix (e.g., 202505)")

    if dashboard_file:
        client_name = dashboard_file.name.replace(".csv", "")

    if dashboard_file and console_file and month_folder:
        output_path_preview = f"{month_folder}/Merge/{client_name}.csv"
        st.markdown(f"📁 **Output path will be:** `{output_path_preview}`")

    # Other fields...
    carrier = st.text_input("Carrier", "Atlasat")
    rate = st.number_input("Rate", value=720.0)
    rate_type = st.selectbox("Rate Type", ["per_minute", "per_second"])
    s2c = st.text_input("S2C number (optional)")
    s2c_rate = st.number_input("S2C Rate", value=0.0)
    s2c_rate_type = st.selectbox("S2C Rate Type", ["per_minute", "per_second"])
    chargeable_call_types = st.text_input("Chargeable Call Types (comma separated)", "outgoing call, incoming call")
    custom_logic = st.text_input("Custom Logic (optional)")

    # New fields: number1
    number1 = st.text_input("Number 1 (optional)")
    number1_rate = st.number_input("Number 1 Rate", value=0.0)
    number1_rate_type = st.selectbox("Number 1 Rate Type", ["per_minute", "per_second"], key="number1_rate_type")
    number1_chargeable_call_types_str = st.text_input("Number 1 Chargeable Call Types (comma separated)", "")
    number1_chargeable_call_types = [ct.strip() for ct in number1_chargeable_call_types_str.split(",") if ct.strip()]

    # New fields: number2
    number2 = st.text_input("Number 2 (optional)")
    number2_rate = st.number_input("Number 2 Rate", value=0.0)
    number2_rate_type = st.selectbox("Number 2 Rate Type", ["per_minute", "per_second"], key="number2_rate_type")
    number2_chargeable_call_types_str = st.text_input("Number 2 Chargeable Call Types (comma separated)", "")
    number2_chargeable_call_types = [ct.strip() for ct in number2_chargeable_call_types_str.split(",") if ct.strip()]

    # ✅ Actual Submit Button
    submitted = st.form_submit_button("➕ Add to Config")

    if submitted:
        dashboard_filename = dashboard_file.name
        console_filename = console_file.name
        client_name = dashboard_filename.replace(".csv", "")

        dashboard_path = f"{month_folder}/DB/{dashboard_filename}"
        console_path = f"{month_folder}/Console/{console_filename}"
        output_path = f"{month_folder}/Merge/{client_name}.csv"

        data = {
            "client": client_name,
            "dashboard": dashboard_path,
            "console": console_path,
            "output": output_path,
            "carrier": carrier,
            "number1": number1 or None,
            "number1_rate": number1_rate,
            "number1_rate_type": number1_rate_type,
            "number1_chargeable_call_types": number1_chargeable_call_types,
            "number2": number2 or None,
            "number2_rate": number2_rate,
            "number2_rate_type": number2_rate_type,
            "number2_chargeable_call_types": number2_chargeable_call_types,
            "rate": rate,
            "rate_type": rate_type,
            "s2c": s2c,
            "s2c_rate": s2c_rate,
            "s2c_rate_type": s2c_rate_type,
            "chargeable_call_types": [ct.strip() for ct in chargeable_call_types.split(",") if ct.strip()],
            "custom_logic": custom_logic or None,
        }

        new_entry = generate_config_entry(data)
        insert_entry_to_config(new_entry)

        st.success("✔ Config added successfully!")
        st.code(f"""
Dashboard: {dashboard_path}
Console:   {console_path}
Output:    {output_path}
""", language="text")