# 🚀 PySpark Schema Generator

A metadata-driven automation tool built using Python and PySpark that reads Excel mapping documents and automatically generates PySpark schema definitions and Spark SQL scripts for modern data engineering platforms like Microsoft Fabric, Azure Databricks, and Apache Spark.

---

# 📌 Features

- Read Excel mapping documents
- Generate PySpark StructType schemas
- Generate Spark SQL table creation scripts
- Metadata-driven architecture
- Automatic datatype conversion
- Nullable column handling
- Extensible for Fabric and Databricks

---

# 🏗️ Project Architecture

```text
Excel Mapping File
        ↓
Metadata Reader (Pandas)
        ↓
Datatype Mapper
        ↓
Code Generator Engine
        ↓
Generated Outputs:
   • PySpark Schema
   • Spark SQL Scripts

# 📂 Project Structure

```text
pyspark-schema-generator/
│
├── input/
│   └── sample_mapping.xlsx
│
├── output/
│   └── generated_schema.py
│
├── src/
│   ├── main.py
│   ├── excel_reader.py
│   ├── datatype_mapper.py
│   └── script_generator.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 📊 Sample Input

| TargetColumn | SourceDataType | Nullable |
|---|---|---|
| CustomerID | int | N |
| CustomerName | varchar | Y |
| CreatedDate | datetime | Y |

---

# 📄 Sample Generated Output

```python
schema = StructType([
    StructField("CustomerID", IntegerType(), False),
    StructField("CustomerName", StringType(), True),
    StructField("CreatedDate", TimestampType(), True)
])
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/Kiranvick0602/pyspark-schema-generator.git
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Project

```bash
python src/main.py
```

---

# 🛠️ Technologies Used

- Python
- PySpark
- Pandas
- OpenPyXL
- GitHub
- VS Code

---

# 🚀 Future Enhancements

- Delta Table Script Generation
- Fabric Lakehouse Integration
- Multi-table Metadata Support
- Streamlit UI
- AI-powered SQL Generation
- SCD Type 2 Automation
- YAML-based Config Framework

---

# 💡 Use Cases

- Enterprise Data Engineering
- Metadata-driven ETL Frameworks
- Azure Fabric Projects
- Databricks Automation
- Rapid Schema Generation

---

# 👨‍💻 Author

Developed as part of a modern Data Engineering automation initiative focused on scalable metadata-driven solutions.