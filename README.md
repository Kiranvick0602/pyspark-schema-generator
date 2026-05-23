# PySpark Schema & Spark SQL Generator

Convert Excel mapping spreadsheets into production-ready Spark assets:

- PySpark `StructType` schemas
- Spark SQL `CREATE TABLE` DDL
- Spark SQL `MERGE INTO` upsert scripts
- YAML table configuration

The project includes both a command-line generator and a Streamlit workbench for reviewing, editing, and downloading generated artifacts.

## Features

- Excel workbook parsing with automatic header-row detection.
- Source-side or destination-side mapping extraction.
- Datatype mapping for Spark SQL and PySpark, including `decimal(precision, scale)`.
- Editable Streamlit metadata grid before generation.
- Spark SQL `MERGE INTO` generation based on selected key columns.
- Microsoft Fabric Lakehouse-friendly defaults.
- No PySpark runtime dependency required for generation.

## Project Structure

```text
pyspark-schema-generator/
|-- app.py                    # Streamlit workbench
|-- requirements.txt
|-- src/
|   |-- main.py               # CLI entry point
|   |-- excel_reader.py       # Excel parsing and normalization
|   |-- datatype_mapper.py    # Spark datatype mapping
|   `-- script_generator.py   # PySpark, DDL, MERGE, and YAML generators
|-- tests/
|   `-- test_generator.py
|-- input/                    # Optional local mapping workbooks
`-- output/                   # Generated scripts
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run The Streamlit App

```bash
streamlit run app.py
```

The app lets you upload an Excel mapping workbook, edit parsed metadata, choose MERGE key columns, and download generated PySpark, DDL, MERGE, and YAML outputs.

## Run The CLI

```bash
python src/main.py ^
  --input input/your_mapping.xlsx ^
  --sheet Customer_Mapping ^
  --side destination ^
  --table-name customer ^
  --database bronze ^
  --source-table staging_customer ^
  --merge-keys customer_id
```

Useful options:

- `--input`, `-i`: Excel mapping file path.
- `--sheet`, `-s`: Excel sheet name. Defaults to the first sheet.
- `--side`: `destination` or `source`.
- `--skip-rows`, `-sr`: Manual header-row offset. Defaults to auto-detect.
- `--table-name`, `-t`: Target table name.
- `--catalog`, `-c`: Target catalog/workspace.
- `--database`, `-d`: Target database/schema/lakehouse.
- `--format`, `-f`: Spark table format for DDL. Defaults to `DELTA`.
- `--source-table`: Source table or staging view for MERGE SQL.
- `--merge-keys`: Comma-separated MERGE key columns.
- `--out-pyspark`, `-op`: PySpark schema output path.
- `--out-sql`, `-os`: DDL output path.
- `--out-merge`, `-om`: MERGE SQL output path.
- `--out-yaml`, `-oy`: YAML output path.

## Generated MERGE Example

```sql
MERGE INTO `prod`.`silver`.`accounts` AS target
USING `staging_accounts` AS source
ON target.`id` = source.`id`
WHEN MATCHED THEN UPDATE SET
  target.`name` = source.`name`,
  target.`balance` = source.`balance`
WHEN NOT MATCHED THEN INSERT (
  `id`, `name`, `balance`
) VALUES (
  source.`id`, source.`name`, source.`balance`
)
```

## Tests

```bash
python -m unittest tests/test_generator.py
```
