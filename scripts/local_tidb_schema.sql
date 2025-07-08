-- 本機結構化資料表
CREATE DATABASE IF NOT EXISTS local_db;

USE local_db;

CREATE TABLE IF NOT EXISTS fin_bill (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    item VARCHAR(255),
    amount DECIMAL(10, 2),
    category VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS health_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    metric_name VARCHAR(255),
    value VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS report_meta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_id VARCHAR(128),
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
