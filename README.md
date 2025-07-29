# 🚀 ETL Pipeline with Airflow, AWS S3, Glue, Athena, and Power BI

## 📌 Project Overview
This project demonstrates a **production-ready ETL pipeline** using Apache Airflow to orchestrate data ingestion, transformation, and loading into AWS services.  
The pipeline processes raw data, stores both raw and transformed datasets in S3, catalogs them in AWS Glue, queries with Athena, and visualizes results in Power BI.

---

## 📂 Architecture Flow
1. **Airflow DAG** orchestrates the pipeline.
2. **Extraction** – Raw data pulled from source (API, CSV, or DB).
3. **Upload Raw File to S3** – Stored in `s3://bucket/raw/`.
4. **Transformation** – Data cleaned and formatted in Airflow.
5. **Upload Transformed File to S3** – Stored in `s3://bucket/processed/`.
6. **AWS Glue Crawler** updates Glue Database tables.
7. **Athena** queries transformed data.
8. **Power BI** connects to Athena for interactive dashboards.

---

## 🛠️ Tech Stack
- **Orchestration**: Apache Airflow  
- **Storage**: AWS S3 (Raw & Transformed Buckets)  
- **Data Catalog**: AWS Glue (Crawler + Database)  
- **Query Engine**: Amazon Athena  
- **Visualization**: Power BI  

---

⚡ Workflow Diagram

<img width="6038" height="2138" alt="Blank diagram (3)" src="https://github.com/user-attachments/assets/017f16d8-9b9e-4f86-85a3-625fe95ddf3d" />



▶️ How to Run
1. Setup Airflow
Create AWS connection (aws_conn_id) in Airflow.

Add S3 bucket name and file paths in Airflow Variables.

2. Trigger DAG
Run Airflow DAG to extract, transform, and load data to S3.

3. Run Glue Crawler
Crawl raw/ and processed/ folders to create/update tables in Glue Database.

4. Query in Athena
Validate transformation and aggregations using SQL.

5. Visualize in Power BI
Connect Power BI to Athena for real-time dashboards.
