# 🚀 PySpark Schema & Spark SQL DDL Generator

A high-performance, metadata-driven automation suite that converts Excel data mapping spreadsheets into clean, production-ready **PySpark StructType schemas**, **Spark SQL DDL definitions**, and **YAML configuration files**.

Includes a premium **Streamlit Web Application** featuring an interactive glassmorphic UI, real-time metadata editing, dynamic statistics, and instant file downloads.

---

## 📌 Key Features

- **Bidirectional Schema Mapping**: Generate schemas for either the **Source Input system** or the **Target Destination tables** automatically from a single mapping sheet.
- **Smart Excel Header Locator**: Automatically scans spreadsheet rows (first 15 rows) to locate header row offsets—no rigid formatting or hardcoded `skiprows` required!
- **Robust Fuzzy Matching**: Auto-maps custom column names (like `"Field Name"`, `"Target Column"`, `"Datatype"`, `"Nullable?"`, `"Description"`, or `"Comments"`) using clean case-insensitive mappings.
- **Advanced Datatype Mapping**: 
  - Dynamic `decimal(precision, scale)` extraction to map `decimal(18,2)` -> Spark `DecimalType(18, 2)` or DDL `DECIMAL(18, 2)`.
  - Clean mapping for integers (`tinyint` -> `ByteType`, `smallint` -> `ShortType`, `int` -> `IntegerType`, `bigint` -> `LongType`), string varchars, dates, timestamps, binaries, and booleans.
- **Automatic Data Cleansing**: Automatically filters out empty columns and strips invisible zero-width space characters (`\u200b`, `\u200e`) which typically cause database loader failures.
- **Stunning Streamlit Web UI**: Modify mapped types and column names **interactively on the screen** before generating code. Features dark glassmorphic styling, syntax-highlighted tabs, copy-to-clipboard, and direct file download options.
- **Zero-Dependency Generator**: The generation engine relies on string formatting, meaning **PySpark is NOT required as a runtime dependency** to run the tool or Web UI, keeping the application super fast and lightweight.

---

## 🏗️ System Architecture

```text
       Excel Mapping File (.xlsx)
                   ↓
     Smart Reader (excel_reader.py)
   ├── Row header scanner (Auto-skip)
   ├── Zero-width space cleaning (\u200b)
   └── Bidirectional selector (Source vs Dest)
                   ↓
      Standardized pandas DataFrame
                   ↓
     Datatype Mapper (datatype_mapper.py)
   ├── Regex-based decimal parser (precision/scale)
   └── Standard database type conversion rules
                   ↓
     Generator Engine (script_generator.py)
   ├── PySpark StructType & Reader code
   ├── Spark SQL Table DDL (Delta/Parquet)
   └── Config YAML Schema
         ↙         ↓         ↘
    CLI Script  Web App    Unit Tests
    (main.py)  (app.py)  (test_generator.py)
```

---

## 📂 Project Structure

```text
pyspark-schema-generator/
│
├── input/
│   └── Workday.Days.xlsx       # Sample Mapping Spreadsheet
│
├── output/
│   ├── generated_schema.py     # Generated PySpark Schema script
│   ├── generated_ddl.sql       # Generated Spark SQL DDL table script
│   └── generated_config.yaml   # Generated YAML configuration
│
├── src/
│   ├── main.py                 # CLI entry point script
│   ├── excel_reader.py         # Advanced Excel reader & cleaner
│   ├── datatype_mapper.py      # Multi-database type mappings
│   └── script_generator.py     # Code generation engines
│
├── tests/
│   └── test_generator.py       # Comprehensive unit test suite
│
├── app.py                      # Glassmorphic Streamlit UI Web Application
├── requirements.txt            # Python dependencies (pandas, openpyxl, streamlit)
├── .gitignore                  # Git exclude configurations
└── README.md                   # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

### Option A: Launch the Premium Streamlit Web Application (Recommended)
```bash
streamlit run app.py
```
*Features:*
- Drag-and-drop Excel mapping uploader.
- Interactive side-by-side **Metadata Editor** to modify columns dynamically.
- Datatype distribution charts and column statistics.
- Dynamically generated **Excel template creator** for easy download.
- Tabs for PySpark Schema, Spark SQL DDL, and YAML.

### Option B: Execute via command-line (CLI)
```bash
python src/main.py --input input/Workday.Days.xlsx --sheet Workday.Days --side destination
```

#### CLI Parameters:
- `--input`, `-i`: Path to Excel mapping file (default: `input/Workday.Days.xlsx`).
- `--sheet`, `-s`: Sheet name in the Excel workbook (default: auto-selects first sheet).
- `--side`: Extract mapping for `"destination"` target columns or `"source"` input columns (default: `destination`).
- `--skip-rows`, `-sr`: Manual skip row offset (default: auto-detects table headers).
- `--table-name`, `-t`: Output table name (default: derived from sheet/file name).
- `--catalog`, `-c`: Unity Catalog name (default: `""`).
- `--database`, `-d`: Target Database / Schema name (default: `"bronze"`).
- `--format`, `-f`: Target Spark SQL storage format (e.g. `DELTA`, `PARQUET`, `CSV`, `ORC`).
- `--out-pyspark`: Output path for generated Python StructType.
- `--out-sql`: Output path for generated SQL DDL.
- `--out-yaml`: Output path for generated YAML config.

---

## 🧪 Run Unit Tests

Execute the unit test suite to verify type mappings and generator formats:
```bash
python -m unittest tests/test_generator.py
```

---

## 📄 Sample Outputs

### 💻 Generated PySpark Schema:
```python
# PySpark Schema generated for table: workday_days
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

workday_days_schema = StructType([
    StructField('StaffNumber', IntegerType(), False),
    StructField('FiscalYear', IntegerType(), False),
    StructField('ARActual', IntegerType(), True),
    StructField('WIPActual', IntegerType(), True),
    StructField('mnETLLastModifiedDate', StringType(), False),
])

# Boilerplate PySpark Read Code
# df_spark = (spark.read
#     .format('parquet')
#     .schema(workday_days_schema)
#     .load('path/to/data'))
```

### 🛢️ Generated Spark SQL DDL:
```sql
CREATE TABLE IF NOT EXISTS `Workday_Days` (
  `StaffNumber` INT NOT NULL,
  `FiscalYear` INT NOT NULL,
  `ARActual` INT,
  `WIPActual` INT,
  `mnETLLastModifiedDate` STRING NOT NULL
)
USING DELTA
```

---

## 👨‍💻 Author
Developed as an enterprise modern data engineering automation framework focused on scalable metadata-driven solutions.