import os
from unstructured.partition.auto import partition
import pytesseract
from PIL import Image
import argparse

# 確保 Tesseract 在系統 PATH 中，或在此處指定路徑
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def extract_text_from_file(file_path, output_dir):
    """
    Extracts text from a given file (PDF, image, etc.) and saves it to a .txt file.
    """
    try:
        print(f"Processing file: {file_path}")
        elements = partition(filename=file_path)
        
        # 合併所有元素的文字
        content = "\n\n".join([str(el) for el in elements])
        
        # 建立輸出檔案路徑
        base_name = os.path.basename(file_path)
        file_name, _ = os.path.splitext(base_name)
        output_path = os.path.join(output_dir, f"{file_name}.txt")
        
        # 寫入文字檔案
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"Successfully extracted text to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        # 嘗試使用 Tesseract 直接處理圖片
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            try:
                print(f"Trying direct OCR with Tesseract for image: {file_path}")
                text = pytesseract.image_to_string(Image.open(file_path), lang='chi_tra+eng')
                
                base_name = os.path.basename(file_path)
                file_name, _ = os.path.splitext(base_name)
                output_path = os.path.join(output_dir, f"{file_name}_ocr.txt")

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)
                
                print(f"Successfully extracted text with Tesseract to: {output_path}")
                return output_path
            except Exception as te:
                print(f"Tesseract OCR failed for {file_path}: {te}")
        return None

def main():
    parser = argparse.ArgumentParser(description="OCR and text extraction script.")
    parser.add_argument("input_path", type=str, help="Path to the input file or directory.")
    parser.add_argument("--output-dir", type=str, default="/home/hom/services/rag-store/ocr_txt", help="Directory to save the extracted text files.")
    
    args = parser.parse_args()
    
    input_path = args.input_path
    output_dir = args.output_dir
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if os.path.isfile(file_path):
                extract_text_from_file(file_path, output_dir)
    elif os.path.isfile(input_path):
        extract_text_from_file(input_path, output_dir)
    else:
        print(f"Error: Input path not found - {input_path}")

if __name__ == "__main__":
    main()
