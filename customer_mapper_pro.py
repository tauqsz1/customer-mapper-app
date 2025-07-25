import streamlit as st
import pandas as pd
from io import BytesIO
from difflib import get_close_matches

st.set_page_config(page_title="Customer Mapper Pro", layout="wide")
st.title("📊 Customer Mapper with Auto Detection + Fallback Logic")

# Upload files
master_file = st.file_uploader("📂 Upload MASTER DATA Excel File", type=["xlsx"])
identifier_file = st.file_uploader("📂 Upload Account Identifier File", type=["xlsx"])
crmtms_file = st.file_uploader("📂 Upload CRM-TMS Mapping File", type=["xlsx"])

if master_file and identifier_file and crmtms_file:
    try:
        # Load all sheets
        master_sheets = pd.ExcelFile(master_file).sheet_names
        id_sheets = pd.ExcelFile(identifier_file).sheet_names
        crm_sheets = pd.ExcelFile(crmtms_file).sheet_names

        master_df = pd.read_excel(master_file, sheet_name=master_sheets[0])
        id_df = pd.read_excel(identifier_file, sheet_name=id_sheets[0])
        crm_df = pd.read_excel(crmtms_file, sheet_name=crm_sheets[0])

        st.success(f"✅ Loaded: {master_sheets[0]}, {id_sheets[0]}, {crm_sheets[0]}")

        # Auto-detect CW1 column in master
        cw1_candidates = [col for col in master_df.columns if 'cw1' in col.lower() or 'account number' in col.lower() or 'customer' in col.lower()]
        if not cw1_candidates:
            cw1_candidates = get_close_matches("CW1", master_df.columns, n=3, cutoff=0.5)
        if cw1_candidates:
            cw1_col = st.selectbox("Select CW1 column in MASTER", cw1_candidates)
        else:
            st.warning("⚠️ Couldn't auto-detect CW1 column. Please select manually.")
            cw1_col = st.selectbox("Select CW1 column in MASTER (manual)", master_df.columns)

        # Auto-detect identifier columns
        id_cw1_candidates = [col for col in id_df.columns if 'identifier' in col.lower() or 'account' in col.lower()]
        crm_cw1_candidates = [col for col in crm_df.columns if 'identifier' in col.lower() or 'tms' in col.lower()]

        id_cw1_col = st.selectbox("Select Identifier column in Account Identifier", id_cw1_candidates or id_df.columns)
        crm_cw1_col = st.selectbox("Select Identifier column in CRM-TMS", crm_cw1_candidates or crm_df.columns)

        # Choose fields to map
        all_fields = sorted(set(id_df.columns).union(set(crm_df.columns)) - {id_cw1_col, crm_cw1_col})
        target_fields = st.multiselect("Select fields to map", all_fields, default=["Account ID"] if "Account ID" in all_fields else None)

        # Normalize CW1
        master_df['CW1_Code'] = master_df[cw1_col].astype(str).str.strip()
        id_df['CW1_Code'] = id_df[id_cw1_col].astype(str).str.strip().str[:8]
        crm_df['CW1_Code'] = crm_df[crm_cw1_col].astype(str).str.strip().str[:8]

        # Fallback merge logic
        result_df = master_df.copy()

        for field in target_fields:
            id_field_present = field in id_df.columns
            crm_field_present = field in crm_df.columns

            if id_field_present:
                result_df = result_df.merge(id_df[['CW1_Code', field]], on='CW1_Code', how='left')
                result_df = result_df.rename(columns={field: f"{field} (From ID)"})

            if crm_field_present:
                result_df = result_df.merge(crm_df[['CW1_Code', field]], on='CW1_Code', how='left')
                result_df = result_df.rename(columns={field: f"{field} (From CRM)"})

            if id_field_present and crm_field_present:
                result_df[f"Final {field}"] = result_df[f"{field} (From ID)"].combine_first(result_df[f"{field} (From CRM)"])
            elif id_field_present:
                result_df[f"Final {field}"] = result_df[f"{field} (From ID)"]
            elif crm_field_present:
                result_df[f"Final {field}"] = result_df[f"{field} (From CRM)"]
            else:
                st.warning(f"⚠️ Field '{field}' not found in either source.")

        # Preview results
        st.subheader("📋 Preview Final Mapped Data")
        st.dataframe(result_df.head(20))

        if any(result_df[f"Final {field}"].isnull().all() for field in target_fields):
            st.warning("⚠️ Some fields are completely unmapped. Please check your CW1 codes or field names.")

        # Export to Excel
        towrite = BytesIO()
        result_df.to_excel(towrite, index=False, sheet_name="Mapped")
        towrite.seek(0)
        st.download_button("📥 Download Final Excel", towrite, "final_mapped.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"❌ Error while processing: {e}")
else:
    st.info("⬆️ Upload all three files to get started.")
