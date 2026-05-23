import io
import os
import sys

import pandas as pd
import streamlit as st

# Add src to python path to import modules when running with streamlit.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from excel_reader import get_excel_sheets, read_excel_mapping
from script_generator import (
    generate_pyspark_schema,
    generate_spark_sql_ddl,
    generate_spark_sql_merge,
    generate_yaml_config,
)


st.set_page_config(
    page_title="PySpark Schema Generator",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(239, 246, 255, 0.82));
    }

    section[data-testid="stSidebar"] {
        background: #0f172a;
        border-right: 1px solid rgba(148, 163, 184, 0.22);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #e2e8f0;
    }

    section[data-testid="stSidebar"] button p,
    section[data-testid="stSidebar"] button span,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button p,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button span {
        color: #0f172a;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] div {
        color: #cbd5e1;
    }

    .app-shell {
        max-width: 1480px;
        margin: 0 auto;
    }

    .topbar {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        padding: 22px 26px;
        margin-bottom: 18px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.07);
    }

    .eyebrow {
        color: #0f766e;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .title {
        color: #0f172a;
        font-size: 2.15rem;
        line-height: 1.1;
        font-weight: 800;
        margin: 0;
    }

    .subtitle {
        color: #475569;
        font-size: 1rem;
        margin-top: 8px;
        max-width: 900px;
    }

    .panel {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
    }

    .panel-title {
        color: #111827;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 2px;
    }

    .panel-note {
        color: #64748b;
        font-size: 0.86rem;
        margin-bottom: 14px;
    }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin: 12px 0 16px;
    }

    .metric-tile {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        background: #f8fafc;
    }

    .metric-value {
        color: #0f172a;
        font-size: 1.45rem;
        font-weight: 800;
    }

    .metric-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .status-band {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 12px;
    }

    .status-pill {
        background: #ecfeff;
        color: #155e75;
        border: 1px solid #a5f3fc;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.78rem;
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }

    div[data-testid="stCodeBlock"] pre {
        border-radius: 8px !important;
        border: 1px solid #1f2937 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def generate_sample_excel():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        sample_df = pd.DataFrame(
            [
                {
                    "Column Name": "customer_id",
                    "Data Type": "bigint",
                    "Nullable": "No",
                    "Description": "Unique customer identifier",
                },
                {
                    "Column Name": "email",
                    "Data Type": "varchar(250)",
                    "Nullable": "No",
                    "Description": "Primary contact email",
                },
                {
                    "Column Name": "first_name",
                    "Data Type": "varchar(100)",
                    "Nullable": "Yes",
                    "Description": "Customer first name",
                },
                {
                    "Column Name": "credit_limit",
                    "Data Type": "decimal(18,2)",
                    "Nullable": "Yes",
                    "Description": "Approved credit limit",
                },
                {
                    "Column Name": "updated_at",
                    "Data Type": "timestamp",
                    "Nullable": "No",
                    "Description": "Latest source update timestamp",
                },
            ]
        )
        sample_df.to_excel(writer, sheet_name="Customer_Mapping", index=False)
    return buffer.getvalue()


def clean_table_name(value):
    return "".join([char if char.isalnum() or char == "_" else "_" for char in str(value)])


def default_merge_keys(df):
    required = df[df["Nullable"].astype(str).str.strip().str.lower().isin(["no", "n", "false", "0"])]
    if not required.empty:
        return required["ColumnName"].astype(str).head(1).tolist()
    return df["ColumnName"].astype(str).head(1).tolist()


st.markdown('<div class="app-shell">', unsafe_allow_html=True)
st.markdown(
    """
<div class="topbar">
    <div class="eyebrow">Metadata-driven Spark generator</div>
    <h1 class="title">PySpark Schema, DDL, MERGE, and YAML Generator</h1>
    <div class="subtitle">
        Upload an Excel mapping sheet, review the parsed metadata, and generate production-ready Spark assets from one controlled workspace.
    </div>
    <div class="status-band">
        <span class="status-pill">Schema-first workflow</span>
        <span class="status-pill">Spark SQL MERGE output</span>
        <span class="status-pill">Fabric and lakehouse friendly</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("## Control Center")
st.sidebar.download_button(
    label="Download Excel Template",
    data=generate_sample_excel(),
    file_name="pyspark_mapping_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

uploaded_file = st.sidebar.file_uploader(
    "Upload mapping workbook",
    type=["xlsx", "xls"],
    help="Upload an Excel workbook with column name, datatype, nullable, and description metadata.",
)

excel_file_path = uploaded_file
default_path = "input/Workday.Days.xlsx"
if excel_file_path is None and os.path.exists(default_path):
    excel_file_path = default_path
    st.sidebar.info("Using the default Workday.Days.xlsx sample.")
elif excel_file_path is None:
    st.sidebar.warning("Upload a workbook or download the template to get started.")


if excel_file_path is not None:
    try:
        sheets = get_excel_sheets(excel_file_path)
        selected_sheet = st.sidebar.selectbox("Worksheet", sheets)

        mapping_side = st.sidebar.radio(
            "Mapping side",
            ["Destination", "Source"],
            horizontal=True,
            index=0,
            help="Choose the side of the mapping sheet used for generation.",
        )
        target_side = "destination" if mapping_side == "Destination" else "source"

        with st.sidebar.expander("Parsing", expanded=False):
            auto_detect = st.checkbox("Auto-detect header row", value=True)
            skip_rows_val = None
            if not auto_detect:
                skip_rows_val = st.number_input("Header row offset", min_value=0, value=0, step=1)

        st.sidebar.markdown("### Target")
        is_fabric = st.sidebar.toggle("Fabric Lakehouse mode", value=True)
        if is_fabric:
            catalog = st.sidebar.text_input("Workspace", value="", placeholder="optional_workspace")
            database = st.sidebar.text_input("Lakehouse", value="finance_lh")
            table_format = "DELTA"
        else:
            catalog = st.sidebar.text_input("Catalog", value="", placeholder="main")
            database = st.sidebar.text_input("Database / schema", value="bronze")
            table_format = st.sidebar.selectbox("Table format", ["DELTA", "PARQUET", "CSV", "ORC", "ICEBERG"])

        default_table = clean_table_name(selected_sheet)
        table_name = st.sidebar.text_input("Target table", value=default_table)
        source_table = st.sidebar.text_input("Merge source table/view", value=f"staging_{table_name}")

        st.sidebar.markdown("### Output")
        include_comments = st.sidebar.checkbox("Include comments", value=True)
        include_reader = st.sidebar.checkbox("Include read template", value=True)

        skiprows_arg = None if auto_detect else skip_rows_val
        df_parsed = read_excel_mapping(excel_file_path, selected_sheet, skiprows_arg, target_side=target_side)

        if df_parsed is not None and not df_parsed.empty:
            col_left, col_right = st.columns([5, 7], gap="large")

            with col_left:
                st.markdown(
                    """
<div class="panel">
    <div class="panel-title">Mapping Editor</div>
    <div class="panel-note">Review and adjust parsed columns before generating Spark assets.</div>
</div>
""",
                    unsafe_allow_html=True,
                )

                edited_df = st.data_editor(
                    df_parsed,
                    use_container_width=True,
                    num_rows="dynamic",
                    hide_index=True,
                    column_config={
                        "ColumnName": st.column_config.TextColumn("Column", required=True),
                        "DataType": st.column_config.TextColumn("Datatype", required=True),
                        "Nullable": st.column_config.SelectboxColumn(
                            "Nullable",
                            options=["Yes", "No"],
                            default="Yes",
                            required=True,
                        ),
                        "Description": st.column_config.TextColumn("Description"),
                    },
                )

                total_cols = len(edited_df)
                nullable_cols = len(
                    edited_df[edited_df["Nullable"].astype(str).str.strip().str.lower().isin(["yes", "y", "true", "1"])]
                )
                required_cols = total_cols - nullable_cols
                st.markdown(
                    f"""
<div class="metric-row">
    <div class="metric-tile"><div class="metric-value">{total_cols}</div><div class="metric-label">Columns</div></div>
    <div class="metric-tile"><div class="metric-value">{nullable_cols}</div><div class="metric-label">Nullable</div></div>
    <div class="metric-tile"><div class="metric-value">{required_cols}</div><div class="metric-label">Required</div></div>
</div>
""",
                    unsafe_allow_html=True,
                )

                type_counts = edited_df["DataType"].astype(str).str.lower().str.split("(").str[0].value_counts().reset_index()
                type_counts.columns = ["Datatype", "Count"]
                st.bar_chart(type_counts, x="Datatype", y="Count", color="#0f766e", height=210)

            with col_right:
                st.markdown(
                    """
<div class="panel">
    <div class="panel-title">Generated Assets</div>
    <div class="panel-note">Choose merge keys, inspect generated code, and download each artifact.</div>
</div>
""",
                    unsafe_allow_html=True,
                )

                available_columns = edited_df["ColumnName"].dropna().astype(str).tolist()
                selected_merge_keys = st.multiselect(
                    "MERGE key columns",
                    options=available_columns,
                    default=[col for col in default_merge_keys(edited_df) if col in available_columns],
                    help="These columns form the Spark SQL MERGE ON clause.",
                )

                pyspark_code = generate_pyspark_schema(
                    edited_df,
                    table_name,
                    include_comments=include_comments,
                    include_reader=include_reader,
                    file_format=table_format.lower(),
                )
                sql_code = generate_spark_sql_ddl(
                    edited_df,
                    table_name,
                    catalog_name=catalog,
                    database_name=database,
                    include_comments=include_comments,
                    table_format=table_format,
                )
                merge_code = generate_spark_sql_merge(
                    edited_df,
                    target_table=table_name,
                    source_table=source_table,
                    key_columns=selected_merge_keys,
                    catalog_name=catalog,
                    database_name=database,
                )
                yaml_code = generate_yaml_config(
                    edited_df,
                    table_name,
                    catalog_name=catalog,
                    database_name=database,
                )

                if is_fabric:
                    fabric_header = (
                        "-- Microsoft Fabric Lakehouse script\n"
                        f"-- Lakehouse: {database or 'not specified'}\n"
                        f"-- Table: {table_name}\n\n"
                    )
                    sql_code = fabric_header + sql_code
                    merge_code = fabric_header + merge_code

                tab_pyspark, tab_sql, tab_merge, tab_yaml = st.tabs(
                    ["PySpark Schema", "Spark SQL DDL", "Spark SQL MERGE", "YAML Config"]
                )

                with tab_pyspark:
                    st.code(pyspark_code, language="python")
                    st.download_button(
                        "Download PySpark",
                        data=pyspark_code,
                        file_name=f"{table_name}_schema.py",
                        mime="text/plain",
                        use_container_width=True,
                    )

                with tab_sql:
                    st.code(sql_code, language="sql")
                    st.download_button(
                        "Download DDL",
                        data=sql_code,
                        file_name=f"{table_name}_ddl.sql",
                        mime="text/plain",
                        use_container_width=True,
                    )

                with tab_merge:
                    st.code(merge_code, language="sql")
                    st.download_button(
                        "Download MERGE",
                        data=merge_code,
                        file_name=f"{table_name}_merge.sql",
                        mime="text/plain",
                        use_container_width=True,
                    )

                with tab_yaml:
                    st.code(yaml_code, language="yaml")
                    st.download_button(
                        "Download YAML",
                        data=yaml_code,
                        file_name=f"{table_name}_config.yaml",
                        mime="text/plain",
                        use_container_width=True,
                    )

        else:
            st.error("The selected sheet could not be parsed. Check the header row or upload the standard template.")
    except Exception as exc:
        st.error(f"Error processing workbook: {exc}")
else:
    st.info("Start by uploading a mapping workbook from the sidebar, or download the Excel template.")

st.markdown("</div>", unsafe_allow_html=True)
