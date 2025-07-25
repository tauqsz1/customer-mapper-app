import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Universal Excel Mapper", layout="wide")
st.title("🔗 Universal Excel Mapper with Smart Column Selection")

# Upload multiple Excel files
uploaded_files = st.file_uploader(
    "📂 Upload one or more Excel files to map",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = {}
    for file in uploaded_files:
        try:
            sheet_names = pd.ExcelFile(file).sheet_names
            df = pd.read_excel(file, sheet_name=sheet_names[0])
            dfs[file.name] = df
            st.success(f"✅ Loaded '{file.name}' (Sheet: {sheet_names[0]})")
        except Exception as e:
            st.error(f"❌ Failed to load {file.name}: {e}")

    selected_file_keys = st.multiselect("📄 Select files to use for mapping", list(dfs.keys()))
    selected_fields = {}

    for file_key in selected_file_keys:
        df = dfs[file_key]
        columns = list(df.columns)
        selected_cols = st.multiselect(f"📌 Select columns from '{file_key}'", columns, key=file_key)
        selected_fields[file_key] = selected_cols

    join_col = st.text_input("🔗 Enter common JOIN column (must exist in all selected files)")

    if st.button("🔄 Merge Files"):
        try:
            merged_df = None
            for file_key in selected_file_keys:
                df = dfs[file_key]
                if join_col not in df.columns:
                    st.warning(f"⚠️ '{join_col}' not found in {file_key}")
                    continue

                use_cols = [join_col] + selected_fields[file_key]
                df = df[use_cols].drop_duplicates(subset=[join_col])

                if merged_df is None:
                    merged_df = df
                else:
                    merged_df = pd.merge(merged_df, df, on=join_col, how="outer")

            if merged_df is not None:
                st.success("✅ Merge Completed")
                st.dataframe(merged_df.head(50))

                towrite = BytesIO()
                merged_df.to_excel(towrite, index=False, sheet_name="Mapped Output")
                towrite.seek(0)
                st.download_button("📥 Download Merged Excel", towrite, "universal_mapped_output.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("❌ Merge failed. Ensure valid join column is used.")
        except Exception as e:
            st.error(f"❌ Error during merging: {e}")
else:
    st.info("⬆️ Upload multiple Excel files to begin.")
