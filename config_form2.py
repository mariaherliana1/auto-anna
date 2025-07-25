import streamlit as st
import json
from config import CONFIG

# ------------------------------
# ✅ Helper Functions
# ------------------------------
def generate_config_entry(data: dict) -> str:
    def quote(value):
        return f'"{value}"' if isinstance(value, str) else str(value)

    return f"""    Files(
        client={quote(data["client"])},
        dashboard={quote(data["dashboard"])},
        console={quote(data["console"])},
        output={quote(data["output"])},
        carrier={quote(data["carrier"])},
        number1={quote(data["number1"]) if data["number1"] else "None"},
        number1_rate={data["number1_rate"]},
        number1_rate_type={quote(data["number1_rate_type"])},
        number1_chargeable_call_types={data["number1_chargeable_call_types"]},
        number2={quote(data["number2"]) if data["number2"] else "None"},
        number2_rate={data["number2_rate"]},
        number2_rate_type={quote(data["number2_rate_type"])},
        number2_chargeable_call_types={data["number2_chargeable_call_types"]},
        rate={data["rate"]},
        rate_type={quote(data["rate_type"])},
        s2c={quote(data["s2c"]) if data["s2c"] else "None"},
        s2c_rate={data["s2c_rate"]},
        s2c_rate_type={quote(data["s2c_rate_type"])},
        chargeable_call_types={json.dumps(data["chargeable_call_types"])},
    ),"""

def insert_entry_to_config(new_entry: str, client: str, config_path: str = "config.py"):
    with open(config_path, "r") as f:
        config_lines = f.readlines()

    start_index = end_index = None
    inside_block = False

    for i, line in enumerate(config_lines):
        # ✅ Detect the start of the Files block for this client
        if f'client="{client}"' in line or f"client='{client}'" in line:
            # Find the nearest "Files(" going upward (start of the block)
            for j in range(i, -1, -1):
                if "Files(" in config_lines[j]:
                    start_index = j
                    inside_block = True
                    break

        if inside_block and line.strip().endswith("),"):
            end_index = i
            break

    # ✅ Remove the entire Files(...) block if found
    if start_index is not None and end_index is not None:
        del config_lines[start_index:end_index + 1]

    # ✅ Insert the new entry after CONFIG = [ line
    for j, line in enumerate(config_lines):
        if line.strip().startswith("CONFIG") and "[" in line:
            config_lines.insert(j + 1, new_entry + "\n")
            break

    with open(config_path, "w") as f:
        f.writelines(config_lines)

# ------------------------------
# ✅ Session State Initialization
# ------------------------------
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

def next_step():
    st.session_state.wizard_step += 1

def prev_step():
    st.session_state.wizard_step -= 1

# ------------------------------
# ✅ Wizard UI
# ------------------------------
st.title("🔧 Add Config (Client Name Only)")

total_steps = 5
st.progress(st.session_state.wizard_step / total_steps)
st.caption(f"Step {st.session_state.wizard_step} of {total_steps}")

valid_carriers = ["Atlasat", "Indosat", "Telkom", "Quiros", "MGM"]
available_call_types = ["outbound call", "predictive dialer", "incoming call", "play_sound", "read_dtmf", "answering machine"]
existing_clients = [c.client for c in CONFIG]

# ------------------------------
# ✅ STEP 1 - Basic Info
# ------------------------------
if st.session_state.wizard_step == 1:
    with st.form("step1_form"):
        client_name = st.text_input("Client name (e.g., tenant-id)", value=st.session_state.form_data.get("client", ""))
        folder_prefix = st.text_input("Folder prefix (e.g., 202505)", value=st.session_state.form_data.get("folder_prefix", ""))

        next_clicked = st.form_submit_button("Next ➡️")

    if next_clicked:
        if not client_name or not folder_prefix:
            st.error("Please fill in both client name and folder prefix.")
        else:
            dashboard_path = f"{folder_prefix}/DB/{client_name}.csv"
            console_path = f"{folder_prefix}/Console/{client_name}.csv"
            output_path = f"{folder_prefix}/Merge/{client_name}.csv"

            st.session_state.form_data.update({
                "client": client_name,
                "folder_prefix": folder_prefix,
                "dashboard": dashboard_path,
                "console": console_path,
                "output": output_path,
            })
            next_step()

# ------------------------------
# ✅ STEP 2 - Basic Rates
# ------------------------------
elif st.session_state.wizard_step == 2:
    with st.form("step2_form"):
        carrier = st.selectbox("Carrier", valid_carriers,
                            index=valid_carriers.index(st.session_state.form_data.get("carrier", "Atlasat")))
        rate = st.number_input("Rate", value=st.session_state.form_data.get("rate", 720.0), min_value=0.0)
        rate_type = st.selectbox("Rate Type", ["per_minute", "per_second"],
                                index=0 if st.session_state.form_data.get("rate_type", "per_minute") == "per_minute" else 1)

        s2c = st.text_input("S2C number (optional)", value=st.session_state.form_data.get("s2c", ""))
        s2c_rate = st.number_input("S2C Rate", value=st.session_state.form_data.get("s2c_rate", 0.0), min_value=0.0)
        s2c_rate_type = st.selectbox("S2C Rate Type", ["per_minute", "per_second"],
                                    index=0 if st.session_state.form_data.get("s2c_rate_type", "per_minute") == "per_minute" else 1)

        col1, col2 = st.columns(2)
        back_clicked = col1.form_submit_button("⬅️ Back")
        next_clicked = col2.form_submit_button("Next ➡️")

    if back_clicked:
        prev_step()
    if next_clicked:
        st.session_state.form_data.update({
            "carrier": carrier,
            "rate": rate,
            "rate_type": rate_type,
            "s2c": s2c,
            "s2c_rate": s2c_rate,
            "s2c_rate_type": s2c_rate_type,
        })
        next_step()

# ------------------------------
# ✅ STEP 3 - Chargeable Call Types
# ------------------------------
elif st.session_state.wizard_step == 3:
    with st.form("step3_form"):
        st.markdown("**Select Chargeable Call Types**")
        selected_types = st.session_state.form_data.get("chargeable_call_types", [])
        chargeable_call_types = []
        for ct in available_call_types:
            if st.checkbox(ct, value=ct in selected_types):
                chargeable_call_types.append(ct)

        col1, col2 = st.columns(2)
        back_clicked = col1.form_submit_button("⬅️ Back")
        next_clicked = col2.form_submit_button("Next ➡️")

    if back_clicked:
        prev_step()
    if next_clicked:
        st.session_state.form_data["chargeable_call_types"] = chargeable_call_types
        next_step()

# ------------------------------
# ✅ STEP 4 - Optional Numbers
# ------------------------------
elif st.session_state.wizard_step == 4:
    with st.form("step4_form"):
        number1 = st.text_input("Number 1 (optional)", value=st.session_state.form_data.get("number1", ""))
        number1_rate = st.number_input("Number 1 Rate", value=st.session_state.form_data.get("number1_rate", 0.0), min_value=0.0)
        number1_rate_type = st.selectbox("Number 1 Rate Type", ["per_minute", "per_second"],
                                        index=0 if st.session_state.form_data.get("number1_rate_type", "per_minute") == "per_minute" else 1)
        number1_chargeable_call_types_str = st.text_input(
            "Number 1 Chargeable Call Types (comma separated)",
            ",".join(st.session_state.form_data.get("number1_chargeable_call_types", []))
        )

        number2 = st.text_input("Number 2 (optional)", value=st.session_state.form_data.get("number2", ""))
        number2_rate = st.number_input("Number 2 Rate", value=st.session_state.form_data.get("number2_rate", 0.0), min_value=0.0)
        number2_rate_type = st.selectbox("Number 2 Rate Type", ["per_minute", "per_second"],
                                        index=0 if st.session_state.form_data.get("number2_rate_type", "per_minute") == "per_minute" else 1)
        number2_chargeable_call_types_str = st.text_input(
            "Number 2 Chargeable Call Types (comma separated)",
            ",".join(st.session_state.form_data.get("number2_chargeable_call_types", []))
        )

        col1, col2 = st.columns(2)
        back_clicked = col1.form_submit_button("⬅️ Back")
        next_clicked = col2.form_submit_button("Next ➡️")

    if back_clicked:
        prev_step()
    if next_clicked:
        st.session_state.form_data.update({
            "number1": number1 or None,
            "number1_rate": number1_rate,
            "number1_rate_type": number1_rate_type,
            "number1_chargeable_call_types": [ct.strip() for ct in number1_chargeable_call_types_str.split(",") if ct.strip()],
            "number2": number2 or None,
            "number2_rate": number2_rate,
            "number2_rate_type": number2_rate_type,
            "number2_chargeable_call_types": [ct.strip() for ct in number2_chargeable_call_types_str.split(",") if ct.strip()],
        })
        next_step()

# ------------------------------
# ✅ STEP 5 - Review & Submit
# ------------------------------
elif st.session_state.wizard_step == 5:
    data = st.session_state.form_data
    st.subheader("Step 5: Review & Submit")

    st.json(data)

    with st.form("step5_form"):
        overwrite_warning = ""
        should_overwrite = False
        if data["client"] in existing_clients:
            overwrite_choice = st.radio(
                f"⚠ Client `{data['client']}` already exists. Overwrite?",
                ["No", "Yes"], index=0
            )
            should_overwrite = overwrite_choice == "Yes"

        col1, col2, col3 = st.columns(3)
        back_clicked = col1.form_submit_button("⬅️ Back")
        submit_clicked = col3.form_submit_button("✅ Submit")

    if back_clicked:
        prev_step()

    if submit_clicked:
        if data["client"] in existing_clients and not should_overwrite:
            st.warning("❌ Entry not added. Choose 'Yes' to overwrite.")
        else:
            new_entry = generate_config_entry(data)
            insert_entry_to_config(new_entry, data["client"])
            st.success("✔ Config added or updated successfully!")
            st.code(f"""
Dashboard: {data['dashboard']}
Console:   {data['console']}
Output:    {data['output']}
""", language="text")

    if st.button("🔄 Reset Form"):
        for k in list(st.session_state.keys()):
            if k not in ["current_step"]:
                del st.session_state[k]
        st.session_state.current_step = 1
        st.rerun()