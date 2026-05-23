import os
import argparse
from excel_reader import read_excel_mapping, get_excel_sheets
from script_generator import generate_pyspark_schema, generate_spark_sql_ddl, generate_yaml_config

def main():
    parser = argparse.ArgumentParser(description="PySpark Schema & Spark SQL DDL Generator")
    parser.add_argument("--input", "-i", type=str, default="input/Workday.Days.xlsx", help="Path to input Excel mapping file")
    parser.add_argument("--sheet", "-s", type=str, default=None, help="Excel sheet name (defaults to first sheet)")
    parser.add_argument("--skip-rows", "-sr", type=int, default=None, help="Number of rows to skip at the top (defaults to auto-detection)")
    parser.add_argument("--table-name", "-t", type=str, default=None, help="Target table name (defaults to sheet name or file name)")
    parser.add_argument("--catalog", "-c", type=str, default="", help="Target Catalog Name")
    parser.add_argument("--database", "-d", type=str, default="", help="Target Database/Schema Name")
    parser.add_argument("--format", "-f", type=str, default="DELTA", help="Target Spark table format (DELTA, PARQUET, etc.)")
    parser.add_argument("--side", type=str, choices=["source", "destination"], default="destination", help="Extract mapping for source or destination columns (default: destination)")
    parser.add_argument("--out-pyspark", "-op", type=str, default="output/generated_schema.py", help="Output path for PySpark StructType script")
    parser.add_argument("--out-sql", "-os", type=str, default="output/generated_ddl.sql", help="Output path for Spark SQL DDL")
    parser.add_argument("--out-yaml", "-oy", type=str, default="output/generated_config.yaml", help="Output path for YAML config")
    
    args = parser.parse_args()
    
    input_file = args.input
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
        
    # Auto-resolve sheet name
    sheets = get_excel_sheets(input_file)
    if not sheets:
        print("Error: Could not read any sheets from the Excel file.")
        return
        
    sheet_name = args.sheet
    if not sheet_name:
        sheet_name = sheets[0]
        print(f"Auto-selected first sheet: '{sheet_name}'")
    elif sheet_name not in sheets:
        print(f"Warning: Sheet '{sheet_name}' not found. Available sheets: {sheets}. Using '{sheets[0]}'")
        sheet_name = sheets[0]
        
    # Auto-resolve table name
    table_name = args.table_name
    if not table_name:
        # Excel Sheet name is Nothing But Table_Name
        table_name = "".join([c if c.isalnum() or c == '_' else '_' for c in sheet_name])
        
    print(f"Reading Excel mapping from '{input_file}' [Sheet: '{sheet_name}', Side: '{args.side}']...")
    df = read_excel_mapping(input_file, sheet_name, args.skip_rows, target_side=args.side)
    
    if df is None or df.empty:
        print("Error: Standardized DataFrame is empty or could not be created.")
        return
        
    print(f"Successfully loaded mapping with {len(df)} columns.")
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # 1. Generate PySpark Schema
    if args.out_pyspark:
        print(f"Generating PySpark Schema -> '{args.out_pyspark}'")
        pyspark_code = generate_pyspark_schema(df, table_name, include_comments=True, include_reader=True)
        with open(args.out_pyspark, "w", encoding="utf-8") as f:
            f.write(pyspark_code)
            
    # 2. Generate Spark SQL DDL
    if args.out_sql:
        print(f"Generating Spark SQL DDL -> '{args.out_sql}'")
        sql_ddl = generate_spark_sql_ddl(df, table_name, args.catalog, args.database, include_comments=True, table_format=args.format)
        with open(args.out_sql, "w", encoding="utf-8") as f:
            f.write(sql_ddl)
            
    # 3. Generate YAML config
    if args.out_yaml:
        print(f"Generating YAML configuration -> '{args.out_yaml}'")
        yaml_config = generate_yaml_config(df, table_name, args.catalog, args.database)
        with open(args.out_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_config)
            
    print("\n[+] Schema Generation Completed successfully!")
    print(f"Preview of generated columns:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()