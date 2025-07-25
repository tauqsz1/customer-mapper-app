
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Customer Mapper Pro", layout="wide")
st.title("📌 Auto-Smart Customer Mapper")

# --- Explicit CW1 Code Columns ---
CW1_COLUMN_MASTER = "Customer Account Number"
CW1_COLUMN_IDENTIFIER = "Identifier"
CW1_COLUMN_CRM = "TMS ID"

def detect_mapping_field(df, field_name):
    for col in df.columns:
        if field_name.lower() in col.lower():
            return col
    return None

# Upload files
master_file = st.file_uploader("Upload MASTER DATA Excel File", type=["xlsx"])
identifier_file = st.file_uploader("Upload Account Identifier File", type=["xlsx"])
crmtms_file = st.file_uploader("Upload CRM-TMS Mapping File", type=["xlsx"])

# Proceed only if all uploaded
if master_file and identifier_file and crmtms_file:
    # Detect and load sheets
    master_sheets = pd.ExcelFile(master_file).sheet_names
    id_sheets = pd.ExcelFile(identifier_file).sheet_names
    crm_sheets = pd.ExcelFile(crmtms_file).sheet_names

    master_df = pd.read_excel(master_file, sheet_name=master_sheets[0])
    id_df = pd.read_excel(identifier_file, sheet_name=id_sheets[0])
    crm_df = pd.read_excel(crmtms_file, sheet_name=crm_sheets[0])

    # Explicit CW1 Code Columns
    if CW1_COLUMN_MASTER not in master_df.columns or CW1_COLUMN_IDENTIFIER not in id_df.columns or CW1_COLUMN_CRM not in crm_df.columns:
        st.error("❌ Could not detect CW1 Code columns. Please ensure 'Customer Account Number', 'Identifier', and 'TMS ID' exist.")
    else:
        master_df['CW1_Code'] = master_df[CW1_COLUMN_MASTER].astype(str).str.strip()
        id_df['CW1_Code'] = id_df[CW1_COLUMN_IDENTIFIER].astype(str).str.strip().str[:8]
        crm_df['CW1_Code'] = crm_df[CW1_COLUMN_CRM].astype(str).str.strip().str[:8]

        # Select field to map
        guess_fields = ['Account ID', 'CRM Account Name', 'Customer Group Name', 'Segment', 'Industry']
        selected_fields = st.multiselect("🧩 Select Fields to Map", guess_fields)

        result_df = master_df.copy()

        for field in selected_fields:
            id_field_col = detect_mapping_field(id_df, field)
            crm_field_col = detect_mapping_field(crm_df, field)

            if id_field_col:
                result_df = result_df.merge(id_df[['CW1_Code', id_field_col]], on='CW1_Code', how='left')
                result_df = result_df.rename(columns={id_field_col: f"{field} (From Identifier)"})
            if crm_field_col:
                result_df = result_df.merge(crm_df[['CW1_Code', crm_field_col]], on='CW1_Code', how='left')
                result_df = result_df.rename(columns={crm_field_col: f"{field} (From CRM-TMS)"})

            if id_field_col and crm_field_col:
                result_df[f"Final {field}"] = result_df[f"{field} (From Identifier)"].combine_first(result_df[f"{field} (From CRM-TMS)"])
            elif id_field_col:
                result_df[f"Final {field}"] = result_df[f"{field} (From Identifier)"]
            elif crm_field_col:
                result_df[f"Final {field}"] = result_df[f"{field} (From CRM-TMS)"]
            else:
                st.warning(f"⚠️ Could not find '{field}' in either file.")

        st.subheader("🔍 Final Preview")
        st.dataframe(result_df.head(30))

        buffer = BytesIO()
        result_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Mapped Excel",
            data=buffer,
            file_name="final_customer_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("⬆️ Please upload all 3 required Excel files to begin.")
