import pandas as pd
import numpy as np

def get_excel_sheets(file_path):
    """
    Helper to return list of sheet names in the Excel file.
    """
    try:
        xl = pd.ExcelFile(file_path)
        return xl.sheet_names
    except Exception as e:
        print(f"Error reading Excel sheets: {e}")
        return []

def read_excel_mapping(file_path, sheet_name, rows_skip=None, target_side="destination"):
    """
    Reads an Excel file sheet, auto-detects headers if rows_skip is None, 
    applies fuzzy header matching based on target_side ('source' or 'destination'),
    and returns a standardized pandas DataFrame.
    """
    try:
        xl = pd.ExcelFile(file_path)
        
        # Auto-detect headers row if rows_skip is not provided
        if rows_skip is None:
            # Read first 15 rows with no headers to find the best match
            df_raw = xl.parse(sheet_name, header=None, nrows=15)
            
            best_row = 0
            max_matches = 0
            
            headers_cands = [
                'columnname', 'column name', 'targetcolumn', 'fieldname', 'field name',
                'datatype', 'data type', 'sourcedatatype', 'type', 'nullable', 'description', 'comment'
            ]
            
            for idx, row in df_raw.iterrows():
                matches = 0
                for val in row:
                    if pd.isna(val):
                        continue
                    val_str = str(val).strip().lower().replace(" ", "").replace("_", "").replace("?", "")
                    if any(cand in val_str for cand in headers_cands):
                        matches += 1
                if matches > max_matches:
                    max_matches = matches
                    best_row = idx
            
            rows_skip = best_row
            
        # Read the DataFrame using detected or specified rows_skip
        df = xl.parse(sheet_name, skiprows=rows_skip)
        
        # Standardize columns
        df = standardize_dataframe(df, target_side=target_side)
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def standardize_dataframe(df, target_side="destination"):
    """
    Standardizes a parsed Excel DataFrame by mapping columns to standard names:
    - ColumnName, DataType, Nullable, Description
    Can extract either 'source' or 'destination' schema mappings.
    Filters out invalid rows and trims all data.
    """
    columns = list(df.columns)
    
    # Standardize column names to lower case, stripped of spaces, underscores, parentheses, dashes
    def clean(s):
        return str(s).strip().lower().replace(" ", "").replace("_", "").replace("?", "").replace("(", "").replace(")", "").replace("-", "")
        
    cleaned_cols = [clean(c) for c in columns]
    
    # We will find the index of columns that best match each field
    col_idx = -1
    dt_idx = -1
    null_idx = -1
    desc_idx = -1
    
    # Find Description/Comment column
    for i, c in enumerate(cleaned_cols):
        if any(cand in c for cand in ['description', 'comment', 'notes', 'remarks', 'metadata']):
            desc_idx = i
            break
            
    if target_side == "destination":
        # Look for target/destination/destinationtablefields, or fields containing "destination" or "target" or "dest" or "to"
        # Column Name
        for i, c in enumerate(cleaned_cols):
            if any(cand in c for cand in ['destination', 'target', 'dest', 'output', 'tofield', 'field2', 'column2']):
                col_idx = i
                break
        if col_idx == -1:
            # Fallback: look for any column containing 'field' or 'column' that isn't source
            for i, c in enumerate(cleaned_cols):
                if 'source' not in c and any(cand in c for cand in ['field', 'column', 'target']):
                    col_idx = i
                    break
                    
        # DataType
        # Look for 'datatype2', 'datatype3', or 'datatype' that is after col_idx
        for i, c in enumerate(cleaned_cols):
            if 'datatype' in c or 'type' in c:
                if i > col_idx or '2' in c or '3' in c or 'dest' in c or 'target' in c:
                    dt_idx = i
                    break
        if dt_idx == -1:
            # Fallback to any datatype column
            for i, c in enumerate(cleaned_cols):
                if 'datatype' in c or 'type' in c:
                    dt_idx = i
                    break
                    
        # Nullable
        for i, c in enumerate(cleaned_cols):
            if 'nullable' in c or 'null' in c:
                if i > col_idx or '2' in c or '3' in c or 'dest' in c or 'target' in c:
                    null_idx = i
                    break
        if null_idx == -1:
            for i, c in enumerate(cleaned_cols):
                if 'nullable' in c or 'null' in c:
                    null_idx = i
                    break
                    
    else: # source side
        # Look for source/src/input, or columns containing "source" or "src"
        for i, c in enumerate(cleaned_cols):
            if any(cand in c for cand in ['source', 'src', 'input', 'fromfield', 'field1', 'column1']):
                col_idx = i
                break
        if col_idx == -1:
            for i, c in enumerate(cleaned_cols):
                if any(cand in c for cand in ['field', 'column']):
                    col_idx = i
                    break
                    
        # DataType
        for i, c in enumerate(cleaned_cols):
            if 'datatype' in c or 'type' in c:
                if 'source' in c or ('2' not in c and '3' not in c and i < (col_idx + 3)):
                    dt_idx = i
                    break
        if dt_idx == -1:
            for i, c in enumerate(cleaned_cols):
                if 'datatype' in c or 'type' in c:
                    dt_idx = i
                    break
                    
        # Nullable
        for i, c in enumerate(cleaned_cols):
            if 'nullable' in c or 'null' in c:
                if 'source' in c or ('2' not in c and '3' not in c and i < (col_idx + 3)):
                    null_idx = i
                    break
        if null_idx == -1:
            for i, c in enumerate(cleaned_cols):
                if 'nullable' in c or 'null' in c:
                    null_idx = i
                    break
                    
    # Map back to names
    mapping = {}
    if col_idx != -1:
        mapping[columns[col_idx]] = 'ColumnName'
    if dt_idx != -1:
        mapping[columns[dt_idx]] = 'DataType'
    if null_idx != -1:
        mapping[columns[null_idx]] = 'Nullable'
    if desc_idx != -1:
        mapping[columns[desc_idx]] = 'Description'
        
    df = df.rename(columns=mapping)
    
    # Ensure ColumnName and DataType are present
    if 'ColumnName' not in df.columns and len(columns) > 0:
        df = df.rename(columns={columns[0]: 'ColumnName'})
    if 'DataType' not in df.columns:
        df['DataType'] = 'string'
        
    # Standardize values, strip zero-width spaces, and handle empty/nan strings
    for col in ['ColumnName', 'DataType', 'Nullable', 'Description']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('\u200b', '', regex=False).str.replace('\u200e', '', regex=False).str.strip()
            df[col] = df[col].replace({'nan': '', 'NaN': ''})
            
    # Set default values for missing fields
    if 'DataType' in df.columns:
        df['DataType'] = df['DataType'].replace({'': 'string'})
    if 'Nullable' in df.columns:
        df['Nullable'] = df['Nullable'].replace({'': 'Yes'})
        
    # Filter out empty ColumnName rows and unnamed auto-generated columns
    df = df[df['ColumnName'].notna() & (df['ColumnName'] != '') & (~df['ColumnName'].str.startswith('Unnamed:'))]
    
    return df[['ColumnName', 'DataType', 'Nullable', 'Description']].copy()
