import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import sys

# Add src to python path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from excel_reader import read_excel_mapping, get_excel_sheets, standardize_dataframe
from script_generator import generate_pyspark_schema, generate_spark_sql_ddl, generate_yaml_config

# Set page configurations
st.set_page_config(
    page_title="PySpark Schema Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom CSS Injection for Rich Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .glass-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(88, 28, 135, 0.45));
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 10px 40px 0 rgba(0, 0, 0, 0.5);
        text-align: center;
    }
    
    .glass-card {
        background: rgba(17, 25, 40, 0.75);
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
        transition: all 0.3s ease-in-out;
    }
    
    .glass-card:hover {
        border-color: rgba(0, 255, 204, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 255, 204, 0.12);
        transform: translateY(-1px);
    }
    
    .neon-title {
        color: #ffffff;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 5px;
    }
    
    .neon-cyan {
        color: #00ffcc;
        text-shadow: 0 0 8px rgba(0, 255, 204, 0.4);
    }
    
    .neon-purple {
        color: #cc66ff;
        text-shadow: 0 0 8px rgba(204, 102, 255, 0.4);
    }
    
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 15px;
    }
    
    .metric-box {
        text-align: center;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 10px 15px;
        border-radius: 8px;
        min-width: 110px;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00ffcc;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
    }
    
    /* Code block wrapper styling */
    div[data-testid="stMarkdownContainer"] pre {
        background-color: #0d1117 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Dynamic Template Generator -----------------
def generate_sample_excel():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        sample_df = pd.DataFrame([
            {"Column Name": "customer_id", "Data Type": "bigint", "Nullable": "No", "Description": "Unique identifier for the customer (Primary Key)"},
            {"Column Name": "first_name", "Data Type": "varchar(100)", "Nullable": "Yes", "Description": "Customer's first name"},
            {"Column Name": "last_name", "Data Type": "varchar(100)", "Nullable": "Yes", "Description": "Customer's last name"},
            {"Column Name": "email", "Data Type": "string", "Nullable": "Yes", "Description": "Primary email contact address"},
            {"Column Name": "credit_limit", "Data Type": "decimal(18,2)", "Nullable": "Yes", "Description": "Maximum credit line approved"},
            {"Column Name": "birth_date", "Data Type": "date", "Nullable": "Yes", "Description": "Date of birth"},
            {"Column Name": "is_active", "Data Type": "boolean", "Nullable": "No", "Description": "Indicates if customer status is active (True/False)"},
            {"Column Name": "created_timestamp", "Data Type": "timestamp", "Nullable": "No", "Description": "Auditing field for record creation datetime"}
        ])
        sample_df.to_excel(writer, sheet_name="Customer_Mapping", index=False)
    return buffer.getvalue()

# ----------------- App Header -----------------
st.markdown("""
<div class="glass-header">
    <div class="neon-title">🚀 <span class="neon-cyan">PySpark</span> Schema Generator</div>
    <div style="font-size: 1.15rem; color: #cbd5e1; font-weight: 300;">
        Transform Excel metadata mapping sheets into production-ready schemas, SQL DDLs, and table structures in seconds.
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- Sidebar Control Panel -----------------
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <span style="font-size: 1.4rem; font-weight: 800; color: #cc66ff; border-bottom: 2px solid #cc66ff; padding-bottom: 5px;">
        🎛️ Control Center
    </span>
</div>
""", unsafe_allow_html=True)

# Download template button
template_data = generate_sample_excel()
st.sidebar.download_button(
    label="📥 Download Excel Template",
    data=template_data,
    file_name="pyspark_mapping_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

st.sidebar.markdown("<hr style='margin: 15px 0; opacity: 0.15;'/>", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.sidebar.file_uploader(
    "Upload Schema Mapping Excel File", 
    type=["xlsx", "xls"],
    help="Excel mapping document detailing columns, datatypes, and nullability."
)

# Use default sample file if nothing uploaded
excel_file_path = None
if uploaded_file is not None:
    excel_file_path = uploaded_file
else:
    # Check if Workday.Days.xlsx is available in default path
    default_path = "input/Workday.Days.xlsx"
    if os.path.exists(default_path):
        excel_file_path = default_path
        st.sidebar.info("ℹ️ Using default 'Workday.Days.xlsx' mapping sample.")
    else:
        st.sidebar.warning("⚠️ Please upload an Excel mapping spreadsheet to get started.")

if excel_file_path is not None:
    try:
        sheets = get_excel_sheets(excel_file_path)
        selected_sheet = st.sidebar.selectbox("Select Excel Sheet", sheets)
        
        # Mapping extraction side selection
        mapping_side = st.sidebar.selectbox(
            "Mapping Extraction Side",
            ["Destination / Target Schema", "Source System Schema"],
            help="Choose whether to generate the schema mapping for the Target Destination system or the Source Input system."
        )
        target_side = "destination" if "Destination" in mapping_side else "source"
        
        # Advanced configurations
        with st.sidebar.expander("⚙️ Parsing Configuration", expanded=False):
            auto_detect = st.checkbox("Auto-detect Headers Row", value=True, help="Scan the sheet to automatically locate the header table row.")
            skip_rows_val = None
            if not auto_detect:
                skip_rows_val = st.number_input("Header Skip Rows Offset", min_value=0, value=0, step=1)
                
        # Microsoft Fabric Lakehouse Optimization Option
        st.sidebar.markdown("""
        <div style="font-weight: 600; font-size: 0.95rem; color: #cc66ff; margin-top: 10px;">
            🧱 Fabric Lakehouse Optimization
        </div>
        """, unsafe_allow_html=True)
        is_fabric = st.sidebar.toggle(
            "Enable Fabric Lakehouse Mode", 
            value=True, 
            help="Tailor namespaces, lock storage engines to Delta Lake, and generate custom DDL comments for Microsoft Fabric Lakehouses."
        )
            
        # Target table configurations
        st.sidebar.markdown(f"""
        <div style="font-weight: 600; font-size: 0.95rem; color: #00ffcc; margin-top: 15px;">
            💎 {"Fabric Namespace Setup" if is_fabric else "Target Table Configuration"}
        </div>
        """, unsafe_allow_html=True)
        
        if is_fabric:
            catalog = st.sidebar.text_input("Fabric Workspace (Optional)", value="", placeholder="e.g. finance_workspace")
            database = st.sidebar.text_input("Fabric Lakehouse Name", value="finance_lh", placeholder="e.g. transactions_lh")
        else:
            catalog = st.sidebar.text_input("Target Catalog", value="", placeholder="e.g. unity_catalog")
            database = st.sidebar.text_input("Target Database / Schema", value="bronze", placeholder="e.g. core_db")
        
        # Derive target table name directly from the sheet name!
        # Excel Sheet name is Nothing But Table_Name
        default_table = "".join([c if c.isalnum() or c == '_' else '_' for c in selected_sheet])
        
        table_name = st.sidebar.text_input("Target Table Name", value=default_table)
        
        # Format and custom options
        st.sidebar.markdown("""
        <div style="font-weight: 600; font-size: 0.95rem; color: #00ffcc; margin-top: 15px;">
            📝 Output Script Preferences
        </div>
        """, unsafe_allow_html=True)
        
        if is_fabric:
            table_format = st.sidebar.selectbox("Table SQL Format", ["DELTA"], help="Delta Lake is the standard storage format for Microsoft Fabric Lakehouse tables.")
        else:
            table_format = st.sidebar.selectbox("Table SQL Format", ["DELTA", "PARQUET", "CSV", "ORC", "ICEBERG"])
            
        include_comments = st.sidebar.checkbox("Include Column Comments", value=True)
        include_reader = st.sidebar.checkbox("Include Spark Read Template", value=True)
        
        # Load the data
        skiprows_arg = None if auto_detect else skip_rows_val
        df_parsed = read_excel_mapping(excel_file_path, selected_sheet, skiprows_arg, target_side=target_side)
        
        if df_parsed is not None and not df_parsed.empty:
            # ----------------- Main Layout -----------------
            col_left, col_right = st.columns([5, 6])
            
            with col_left:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 1.25rem; font-weight: 700; color: #cc66ff; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    👁️ Mapping Metadata Editor
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 15px;">
                    Review the parsed spreadsheet schema below. You can double-click cells to <b>modify names or datatypes in real-time</b> to update the generated code instantly!
                </div>
                """, unsafe_allow_html=True)
                
                # Render Streamlit Editable Dataframe
                edited_df = st.data_editor(
                    df_parsed,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "ColumnName": st.column_config.TextColumn(
                            "Column Name",
                            help="Name of the field in PySpark schema / SQL table",
                            required=True,
                        ),
                        "DataType": st.column_config.TextColumn(
                            "Source Datatype",
                            help="Original data type (e.g. varchar, decimal(18,2), int)",
                            required=True,
                        ),
                        "Nullable": st.column_config.SelectboxColumn(
                            "Nullable?",
                            options=["Yes", "No"],
                            default="Yes",
                            required=True,
                        ),
                        "Description": st.column_config.TextColumn(
                            "Description / Comment",
                            help="Column metadata comment used in SQL DDL & StructType",
                        )
                    }
                )
                
                # Show quick statistics
                total_cols = len(edited_df)
                nullable_cols = len(edited_df[edited_df['Nullable'].str.lower().str.startswith('y')])
                
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-box">
                        <div class="metric-value">{total_cols}</div>
                        <div class="metric-label">Total Columns</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value">{nullable_cols}</div>
                        <div class="metric-label">Nullable Columns</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-value">{total_cols - nullable_cols}</div>
                        <div class="metric-label">Required Columns</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Datatype distribution chart
                st.markdown("<div style='font-size: 0.95rem; font-weight: 600; color: #cbd5e1; margin-bottom: 8px;'>Datatype Distribution</div>", unsafe_allow_html=True)
                type_counts = edited_df['DataType'].str.lower().str.split('(').str[0].value_counts().reset_index()
                type_counts.columns = ['Datatype Group', 'Count']
                st.bar_chart(type_counts, x='Datatype Group', y='Count', color='#00ffcc', height=180)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_right:
                st.markdown("<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 1.25rem; font-weight: 700; color: #00ffcc; margin-bottom: 12px;">
                    💻 Generated Code Outputs
                </div>
                """, unsafe_allow_html=True)
                
                # Code generation tabs
                tab_pyspark, tab_sql, tab_yaml = st.tabs([
                    "🐍 PySpark Schema", 
                    "🛢️ Spark SQL DDL", 
                    "📄 YAML Configuration"
                ])
                
                # Generate PySpark Schema Code
                pyspark_code = generate_pyspark_schema(
                    edited_df, 
                    table_name, 
                    include_comments=include_comments, 
                    include_reader=include_reader,
                    file_format=table_format.lower()
                )
                
                with tab_pyspark:
                    st.markdown("""
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 10px;">
                        Copy the code below directly into your Databricks, Fabric, or local PySpark notebook.
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(pyspark_code, language="python")
                    
                    st.download_button(
                        label="📥 Download PySpark Script",
                        data=pyspark_code,
                        file_name=f"{table_name}_schema.py",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                # Generate Spark SQL DDL Code
                sql_code = generate_spark_sql_ddl(
                    edited_df,
                    table_name,
                    catalog_name=catalog,
                    database_name=database,
                    include_comments=include_comments,
                    table_format=table_format
                )
                
                if is_fabric:
                    # Prepend a beautiful header to the DDL
                    header = "-- ========================================================\n"
                    header += f"-- Microsoft Fabric Lakehouse Managed Table DDL\n"
                    if catalog:
                        header += f"-- Workspace: {catalog}\n"
                    if database:
                        header += f"-- Lakehouse: {database}\n"
                    header += f"-- Table:     {table_name}\n"
                    header += "-- ========================================================\n\n"
                    sql_code = header + sql_code
                
                with tab_sql:
                    st.markdown("""
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 10px;">
                        Standard SQL DDL table definition block, fully optimized for delta lakes and lakehouses.
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(sql_code, language="sql")
                    
                    st.download_button(
                        label="📥 Download SQL DDL",
                        data=sql_code,
                        file_name=f"{table_name}_ddl.sql",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                # Generate YAML Code
                yaml_code = generate_yaml_config(
                    edited_df,
                    table_name,
                    catalog_name=catalog,
                    database_name=database
                )
                
                with tab_yaml:
                    st.markdown("""
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 10px;">
                        Clean structured configuration YAML, perfect for metadata-driven frameworks and config files.
                    </div>
                    """, unsafe_allow_html=True)
                    st.code(yaml_code, language="yaml")
                    
                    st.download_button(
                        label="📥 Download YAML Config",
                        data=yaml_code,
                        file_name=f"{table_name}_config.yaml",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.error("❌ The selected sheet could not be parsed. Please check if your row offset configurations are correct, or upload a standard mapping Excel document.")
            
    except Exception as e:
        st.error(f"❌ Error processing Excel mapping sheet: {e}")
        st.info("💡 Try downloading our standard excel template in the sidebar to review the expected structure.")
