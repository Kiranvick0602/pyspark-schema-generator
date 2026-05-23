from datatype_mapper import map_datatype, map_to_spark_sql_type

def generate_pyspark_schema(df, table_name, include_comments=True, include_reader=False, file_format="parquet"):
    """
    Generates a Python script containing the PySpark StructType schema definition.
    """
    # Collect all needed imports
    classes_needed = {'StructType', 'StructField'}
    
    for _, row in df.iterrows():
        mapped = map_datatype(row['DataType'])
        classes_needed.add(mapped['class_name'])
        
    imports_str = f"from pyspark.sql.types import {', '.join(sorted(classes_needed))}\n"
    
    schema_var_name = f"{table_name.lower().replace('.', '_').replace(' ', '_')}_schema"
    
    script = f"# PySpark Schema generated for table: {table_name}\n"
    script += imports_str + "\n"
    script += f"{schema_var_name} = StructType([\n"
    
    for _, row in df.iterrows():
        column_name = row['ColumnName']
        mapped = map_datatype(row['DataType'])
        datatype_inst = mapped['instance']
        
        nullable = 'True'
        if str(row['Nullable']).strip().lower() in ['no', 'n', 'false', '0']:
            nullable = 'False'
            
        desc = str(row.get('Description', '') or '').strip()
        if include_comments and desc and desc.lower() not in ['nan', 'none', '']:
            # Escape single quotes in description
            escaped_desc = desc.replace("'", "\\'")
            metadata_str = f", metadata={{'comment': '{escaped_desc}'}}"
        else:
            metadata_str = ""
            
        script += f"    StructField('{column_name}', {datatype_inst}, {nullable}{metadata_str}),\n"
        
    script += "])\n"
    
    if include_reader:
        script += "\n# Boilerplate PySpark Read Code\n"
        script += f"# df_spark = (spark.read\n"
        script += f"#     .format('{file_format}')\n"
        script += f"#     .schema({schema_var_name})\n"
        script += f"#     .load('path/to/data'))\n"
        
    return script

def generate_spark_sql_ddl(df, table_name, catalog_name="", database_name="", include_comments=True, table_format="DELTA", table_comment=""):
    """
    Generates standard Spark SQL DDL CREATE TABLE statement.
    """
    full_table_name = ""
    if catalog_name:
        full_table_name += f"`{catalog_name}`."
    if database_name:
        full_table_name += f"`{database_name}`."
    full_table_name += f"`{table_name}`"
    
    sql = f"CREATE TABLE IF NOT EXISTS {full_table_name} (\n"
    
    cols_sql = []
    for _, row in df.iterrows():
        column_name = row['ColumnName']
        sql_type = map_to_spark_sql_type(row['DataType'])
        
        nullable = ''
        if str(row['Nullable']).strip().lower() in ['no', 'n', 'false', '0']:
            nullable = ' NOT NULL'
            
        desc = str(row.get('Description', '') or '').strip()
        comment_str = ''
        if include_comments and desc and desc.lower() not in ['nan', 'none', '']:
            escaped_desc = desc.replace("'", "\\'")
            comment_str = f" COMMENT '{escaped_desc}'"
            
        cols_sql.append(f"  `{column_name}` {sql_type}{nullable}{comment_str}")
        
    sql += ",\n".join(cols_sql)
    sql += "\n)\n"
    
    if table_format:
        sql += f"USING {table_format.upper()}\n"
        
    if table_comment:
        escaped_comment = str(table_comment).replace("'", "\\'")
        sql += f"COMMENT '{escaped_comment}'\n"
        
    return sql

def generate_yaml_config(df, table_name, catalog_name="", database_name=""):
    """
    Generates a YAML schema config file representing the parsed mapping.
    """
    yaml = f"table_name: \"{table_name}\"\n"
    if catalog_name:
        yaml += f"catalog: \"{catalog_name}\"\n"
    if database_name:
        yaml += f"database: \"{database_name}\"\n"
        
    yaml += "columns:\n"
    for _, row in df.iterrows():
        column_name = row['ColumnName']
        datatype = row['DataType']
        nullable = 'true' if str(row['Nullable']).strip().lower() not in ['no', 'n', 'false', '0'] else 'false'
        desc = str(row.get('Description', '') or '').strip()
        if desc.lower() in ['nan', 'none', '']:
            desc = ''
        else:
            desc = desc.replace('"', '\\"')
        
        yaml += f"  - name: \"{column_name}\"\n"
        yaml += f"    type: \"{datatype}\"\n"
        yaml += f"    nullable: {nullable}\n"
        if desc:
            yaml += f"    description: \"{desc}\"\n"
            
    return yaml