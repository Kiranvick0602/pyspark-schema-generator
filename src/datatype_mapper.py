import re

def map_datatype(datatype):
    """
    Maps a database/Excel datatype string to a PySpark SQL type.
    Returns a dict with:
      - 'instance': The instantiated PySpark type string (e.g., 'DecimalType(18, 2)')
      - 'class_name': The class name for imports (e.g., 'DecimalType')
    """
    if not isinstance(datatype, str):
        return {'instance': 'StringType()', 'class_name': 'StringType'}
        
    datatype = datatype.strip().lower()
    
    # Handle decimals/numerics with precision and scale, e.g., decimal(18, 2) or numeric(10,5)
    decimal_match = re.search(r'^(decimal|numeric)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', datatype)
    if decimal_match:
        precision = decimal_match.group(2)
        scale = decimal_match.group(3)
        return {
            'instance': f'DecimalType({precision}, {scale})',
            'class_name': 'DecimalType'
        }
        
    # Handle decimal without precision/scale
    if datatype in ['decimal', 'numeric']:
        return {'instance': 'DecimalType(10, 0)', 'class_name': 'DecimalType'}
        
    # Handle normal mappings
    mappings = {
        # Integers
        'tinyint': ('ByteType()', 'ByteType'),
        'smallint': ('ShortType()', 'ShortType'),
        'int': ('IntegerType()', 'IntegerType'),
        'integer': ('IntegerType()', 'IntegerType'),
        'bigint': ('LongType()', 'LongType'),
        
        # Floats & Doubles
        'float': ('FloatType()', 'FloatType'),
        'real': ('FloatType()', 'FloatType'),
        'double': ('DoubleType()', 'DoubleType'),
        
        # Strings
        'string': ('StringType()', 'StringType'),
        'text': ('StringType()', 'StringType'),
        'varchar': ('StringType()', 'StringType'),
        'nvarchar': ('StringType()', 'StringType'),
        'char': ('StringType()', 'StringType'),
        'nchar': ('StringType()', 'StringType'),
        
        # Boolean
        'boolean': ('BooleanType()', 'BooleanType'),
        'bool': ('BooleanType()', 'BooleanType'),
        'bit': ('BooleanType()', 'BooleanType'),
        
        # Date and Time
        'date': ('DateType()', 'DateType'),
        'timestamp': ('TimestampType()', 'TimestampType'),
        'datetime': ('TimestampType()', 'TimestampType'),
        'datetime2': ('TimestampType()', 'TimestampType'),
        
        # Binary
        'binary': ('BinaryType()', 'BinaryType'),
        'varbinary': ('BinaryType()', 'BinaryType'),
        'blob': ('BinaryType()', 'BinaryType'),
        'image': ('BinaryType()', 'BinaryType'),
    }
    
    # Check simple direct match
    if datatype in mappings:
        inst, cls = mappings[datatype]
        return {'instance': inst, 'class_name': cls}
        
    # Regex fallback checks (e.g. varchar(255) -> StringType())
    if re.search(r'^(varchar|nvarchar|char|nchar|text)\b', datatype):
        return {'instance': 'StringType()', 'class_name': 'StringType'}
    if re.search(r'^(int|integer|bigint|smallint|tinyint)\b', datatype):
        if 'big' in datatype:
            return {'instance': 'LongType()', 'class_name': 'LongType'}
        elif 'small' in datatype:
            return {'instance': 'ShortType()', 'class_name': 'ShortType'}
        elif 'tiny' in datatype:
            return {'instance': 'ByteType()', 'class_name': 'ByteType'}
        return {'instance': 'IntegerType()', 'class_name': 'IntegerType'}
    if re.search(r'^(float|double|real)\b', datatype):
        if 'double' in datatype:
            return {'instance': 'DoubleType()', 'class_name': 'DoubleType'}
        return {'instance': 'FloatType()', 'class_name': 'FloatType'}
        
    # Default fallback
    return {'instance': 'StringType()', 'class_name': 'StringType'}

def map_to_spark_sql_type(datatype):
    """
    Maps a database/Excel datatype string to a Spark SQL DDL datatype string.
    e.g., 'decimal(18,2)' -> 'DECIMAL(18, 2)'
          'varchar(100)' -> 'STRING'
          'int' -> 'INT'
    """
    mapped = map_datatype(datatype)
    cls = mapped['class_name']
    inst = mapped['instance']
    
    if cls == 'DecimalType':
        # Return DecimalType(p, s) but in SQL format: DECIMAL(p, s)
        # Extract digits
        match = re.search(r'\d+,\s*\d+', inst)
        if match:
            return f"DECIMAL({match.group(0)})"
        return "DECIMAL(10, 0)"
        
    sql_types = {
        'ByteType': 'BYTE',
        'ShortType': 'SHORT',
        'IntegerType': 'INT',
        'LongType': 'BIGINT',
        'FloatType': 'FLOAT',
        'DoubleType': 'DOUBLE',
        'StringType': 'STRING',
        'BooleanType': 'BOOLEAN',
        'DateType': 'DATE',
        'TimestampType': 'TIMESTAMP',
        'BinaryType': 'BINARY'
    }
    
    return sql_types.get(cls, 'STRING')