from datatype_mapper import map_datatype, map_to_spark_sql_type

def _is_not_nullable(value):
    return str(value).strip().lower() in ['no', 'n', 'false', '0']

def _quote_sql_identifier(identifier):
    """
    Quotes a Spark SQL identifier and escapes embedded backticks.
    Supports multipart names by quoting each segment.
    """
    parts = [part for part in str(identifier).split('.') if part]
    if not parts:
        return "``"
    return ".".join(f"`{part.replace('`', '``')}`" for part in parts)

def _qualified_table_name(table_name, catalog_name="", database_name=""):
    parts = []
    if catalog_name:
        parts.append(catalog_name)
    if database_name:
        parts.append(database_name)
    parts.append(table_name)
    return ".".join(_quote_sql_identifier(part) for part in parts)

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
    full_table_name = _qualified_table_name(table_name, catalog_name, database_name)
    
    sql = f"CREATE TABLE IF NOT EXISTS {full_table_name} (\n"
    
    cols_sql = []
    for _, row in df.iterrows():
        column_name = row['ColumnName']
        sql_type = map_to_spark_sql_type(row['DataType'])
        
        nullable = ''
        if _is_not_nullable(row['Nullable']):
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

def generate_spark_sql_merge(
    df,
    target_table,
    source_table,
    key_columns=None,
    catalog_name="",
    database_name="",
    include_update=True,
    include_insert=True,
):
    """
    Generates optimized Spark SQL MERGE statement.

    Updates happen only when non-key column values differ.
    """

    columns = [
        str(row['ColumnName']).strip()
        for _, row in df.iterrows()
        if str(row['ColumnName']).strip()
    ]

    if not columns:
        raise ValueError("Cannot generate MERGE SQL without mapped columns.")

    # Determine merge keys
    if key_columns:
        key_columns = [
            str(col).strip()
            for col in key_columns
            if str(col).strip()
        ]
    else:
        key_columns = [
            str(row['ColumnName']).strip()
            for _, row in df.iterrows()
            if str(row['ColumnName']).strip()
            and _is_not_nullable(row.get('Nullable', 'Yes'))
        ]

        if not key_columns:
            key_columns = [columns[0]]

    # Validate keys
    missing_keys = [col for col in key_columns if col not in columns]

    if missing_keys:
        raise ValueError(
            f"Merge key columns not found in mapping: {', '.join(missing_keys)}"
        )

    target_name = _qualified_table_name(
        target_table,
        catalog_name,
        database_name
    )

    source_name = _quote_sql_identifier(source_table)

    # ON clause
    on_clause = " AND ".join(
        f"target.{_quote_sql_identifier(col)} = source.{_quote_sql_identifier(col)}"
        for col in key_columns
    )

    sql = f"MERGE INTO {target_name} AS target\n"
    sql += f"USING {source_name} AS source\n"
    sql += f"ON {on_clause}\n"

    # Non-key columns
    update_columns = [col for col in columns if col not in key_columns]

    # UPDATE section
    if include_update and update_columns:

        # Detect changes
        change_conditions = [
            f"""(
                target.{_quote_sql_identifier(col)} <> source.{_quote_sql_identifier(col)}
                OR target.{_quote_sql_identifier(col)} IS NULL AND source.{_quote_sql_identifier(col)} IS NOT NULL
                OR target.{_quote_sql_identifier(col)} IS NOT NULL AND source.{_quote_sql_identifier(col)} IS NULL
            )"""
            for col in update_columns
        ]

        change_clause = "\n OR ".join(change_conditions)

        assignments = [
            f"  target.{_quote_sql_identifier(col)} = source.{_quote_sql_identifier(col)}"
            for col in update_columns
        ]

        sql += "WHEN MATCHED AND (\n"
        sql += change_clause
        sql += "\n) THEN UPDATE SET\n"

        sql += ",\n".join(assignments)
        sql += "\n"

    # INSERT section
    if include_insert:

        quoted_columns = ", ".join(
            _quote_sql_identifier(col)
            for col in columns
        )

        source_values = ", ".join(
            f"source.{_quote_sql_identifier(col)}"
            for col in columns
        )

        sql += "WHEN NOT MATCHED THEN INSERT (\n"
        sql += f"  {quoted_columns}\n"
        sql += ") VALUES (\n"
        sql += f"  {source_values}\n"
        sql += ")\n"

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
