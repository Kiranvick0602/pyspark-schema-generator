import sys
import os
import unittest
import pandas as pd

# Add src to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from datatype_mapper import map_datatype, map_to_spark_sql_type
from script_generator import generate_pyspark_schema, generate_spark_sql_ddl, generate_yaml_config

class TestDatatypeMapper(unittest.TestCase):
    
    def test_basic_types(self):
        self.assertEqual(map_datatype('int')['class_name'], 'IntegerType')
        self.assertEqual(map_datatype('integer')['class_name'], 'IntegerType')
        self.assertEqual(map_datatype('bigint')['class_name'], 'LongType')
        self.assertEqual(map_datatype('string')['class_name'], 'StringType')
        self.assertEqual(map_datatype('varchar(255)')['class_name'], 'StringType')
        self.assertEqual(map_datatype('boolean')['class_name'], 'BooleanType')
        self.assertEqual(map_datatype('bool')['class_name'], 'BooleanType')
        self.assertEqual(map_datatype('date')['class_name'], 'DateType')
        self.assertEqual(map_datatype('timestamp')['class_name'], 'TimestampType')
        self.assertEqual(map_datatype('datetime')['class_name'], 'TimestampType')
        
    def test_decimal_precision(self):
        dec_map = map_datatype('decimal(18, 4)')
        self.assertEqual(dec_map['class_name'], 'DecimalType')
        self.assertEqual(dec_map['instance'], 'DecimalType(18, 4)')
        
        dec_map_spaced = map_datatype('  decimal  ( 10 , 2 ) ')
        self.assertEqual(dec_map_spaced['class_name'], 'DecimalType')
        self.assertEqual(dec_map_spaced['instance'], 'DecimalType(10, 2)')
        
    def test_sql_type_mapping(self):
        self.assertEqual(map_to_spark_sql_type('int'), 'INT')
        self.assertEqual(map_to_spark_sql_type('varchar(100)'), 'STRING')
        self.assertEqual(map_to_spark_sql_type('decimal(18, 2)'), 'DECIMAL(18, 2)')
        self.assertEqual(map_to_spark_sql_type('datetime'), 'TIMESTAMP')

class TestScriptGenerator(unittest.TestCase):
    
    def setUp(self):
        # Create a sample standardised DataFrame
        self.df = pd.DataFrame([
            {"ColumnName": "id", "DataType": "int", "Nullable": "No", "Description": "Record ID"},
            {"ColumnName": "name", "DataType": "varchar(100)", "Nullable": "Yes", "Description": "Client name"},
            {"ColumnName": "balance", "DataType": "decimal(15,2)", "Nullable": "Yes", "Description": "Account balance"},
            {"ColumnName": "active", "DataType": "boolean", "Nullable": "No", "Description": "Status flag"}
        ])
        
    def test_pyspark_schema(self):
        schema_code = generate_pyspark_schema(self.df, "accounts", include_comments=True)
        self.assertIn("StructType", schema_code)
        self.assertIn("StructField('id', IntegerType(), False, metadata={'comment': 'Record ID'})", schema_code)
        self.assertIn("StructField('name', StringType(), True, metadata={'comment': 'Client name'})", schema_code)
        self.assertIn("StructField('balance', DecimalType(15, 2), True, metadata={'comment': 'Account balance'})", schema_code)
        
    def test_sql_ddl(self):
        sql_ddl = generate_spark_sql_ddl(self.df, "accounts", catalog_name="prod", database_name="silver")
        self.assertIn("CREATE TABLE IF NOT EXISTS `prod`.`silver`.`accounts` (", sql_ddl)
        self.assertIn("`id` INT NOT NULL COMMENT 'Record ID'", sql_ddl)
        self.assertIn("`balance` DECIMAL(15, 2) COMMENT 'Account balance'", sql_ddl)
        self.assertIn("USING DELTA", sql_ddl)

    def test_yaml_config(self):
        yaml_config = generate_yaml_config(self.df, "accounts")
        self.assertIn("table_name: \"accounts\"", yaml_config)
        self.assertIn("- name: \"id\"", yaml_config)
        self.assertIn("type: \"int\"", yaml_config)

if __name__ == "__main__":
    unittest.main()
