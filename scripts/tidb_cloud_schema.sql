-- 雲端向量表
CREATE DATABASE IF NOT EXISTS rag;

USE rag;

CREATE TABLE IF NOT EXISTS embeddings(
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  doc_id VARCHAR(128),
  chunk  TEXT,
  vec    VECTOR(1536)
);

-- 為 TiDB Cloud 建立向量索引
-- 使用 COSINE 距離的 HNSW 索引，並按需添加列存副本
ALTER TABLE embeddings
ADD VECTOR INDEX vec_hnsw ((VEC_COSINE_DISTANCE(vec))) ADD_COLUMNAR_REPLICA_ON_DEMAND;
