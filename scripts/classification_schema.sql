-- 家庭資料管理分類與標記系統資料庫架構
-- 建立日期：2025-07-14

USE rag;

-- 1. 文件類別表
CREATE TABLE IF NOT EXISTS categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50), -- 前端顯示圖示
    color VARCHAR(7), -- 十六進制顏色代碼
    parent_id BIGINT NULL, -- 支援階層分類
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- 2. 家庭成員表
CREATE TABLE IF NOT EXISTS family_members (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50), -- 父親、母親、兒子、女兒等
    birth_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. 標籤表
CREATE TABLE IF NOT EXISTS tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7), -- 標籤顏色
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 文件元資料表
CREATE TABLE IF NOT EXISTS documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    category_id BIGINT,
    family_member_id BIGINT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    document_date DATE, -- 文件日期（從內容提取）
    extracted_amount DECIMAL(15,2), -- 提取的金額
    extracted_date DATE, -- 提取的日期
    ocr_text TEXT, -- OCR 提取的完整文字
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    confidence_score FLOAT, -- 分類信心度
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (family_member_id) REFERENCES family_members(id) ON DELETE SET NULL,
    INDEX idx_category (category_id),
    INDEX idx_family_member (family_member_id),
    INDEX idx_document_date (document_date),
    INDEX idx_upload_date (upload_date)
);

-- 5. 文件標籤關聯表（多對多）
CREATE TABLE IF NOT EXISTS document_tags (
    document_id BIGINT,
    tag_id BIGINT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 6. 更新 embeddings 表以關聯文件
ALTER TABLE embeddings 
ADD COLUMN IF NOT EXISTS document_id BIGINT,
ADD FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE;

-- 新增索引以提升查詢效能
ALTER TABLE embeddings 
ADD INDEX IF NOT EXISTS idx_document_id (document_id);

-- 7. 插入預設分類
INSERT IGNORE INTO categories (name, description, icon, color) VALUES
('帳單', '水電費、電話費、信用卡帳單等', '💳', '#FF6B6B'),
('收據', '購物收據、醫療收據、教育支出等', '🧾', '#4ECDC4'),
('成績單', '學校成績、考試結果、學習進度', '📊', '#45B7D1'),
('健康記錄', '身高體重、健康檢查報告、疫苗記錄', '🏥', '#96CEB4'),
('保險文件', '保險單、理賠申請、保險證明', '🛡️', '#FFEAA7'),
('稅務文件', '報稅資料、稅單、扣繳憑單', '📋', '#DDA0DD'),
('合約文件', '租約、購屋合約、服務合約', '📄', '#98D8C8'),
('證書證照', '畢業證書、專業證照、資格證明', '🏆', '#F7DC6F'),
('其他', '未分類或其他類型文件', '📁', '#BDC3C7');

-- 8. 插入預設標籤
INSERT IGNORE INTO tags (name, color, description) VALUES
('重要', '#FF4757', '重要文件標記'),
('緊急', '#FF3838', '需要緊急處理'),
('待處理', '#FFA502', '需要後續處理'),
('已完成', '#2ED573', '已處理完成'),
('定期', '#3742FA', '定期產生的文件'),
('年度', '#8E44AD', '年度相關文件'),
('醫療', '#E74C3C', '醫療相關'),
('教育', '#3498DB', '教育相關'),
('財務', '#F39C12', '財務相關'),
('法律', '#9B59B6', '法律相關');

-- 9. 插入範例家庭成員（可選）
INSERT IGNORE INTO family_members (name, relationship) VALUES
('家庭共用', '共用'),
('父親', '父親'),
('母親', '母親'),
('長子/女', '子女'),
('次子/女', '子女');
