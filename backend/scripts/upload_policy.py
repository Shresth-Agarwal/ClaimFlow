import json
import boto3
import os

kb_path = r"C:\Users\guest123\ClaimFlow\backend\insurance_kb.json"
txt_path = r"C:\Users\guest123\ClaimFlow\backend\insurance_policy.txt"
bucket_name = "claimflow-knowledge-base"
s3_key = "policies/insurance_policy.txt"

def main():
    # 1 & 2. Read JSON and convert to text format
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
        
    text_lines = []
    for entry in kb_data:
        text_lines.append("---")
        text_lines.append(f"Clause: {entry.get('clause', '')}")
        text_lines.append(f"Page: {entry.get('page', '')}")
        text_lines.append(f"Content: {entry.get('text', '')}")
    text_lines.append("---")
    
    # 3. Save as text file
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_lines))
        
    # 4. Upload to S3 with metadata
    s3 = boto3.client('s3')
    
    s3.upload_file(
        txt_path, 
        bucket_name, 
        s3_key,
        ExtraArgs={
            "Metadata": {
                "type": "insurance-policy",
                "version": "1.0"
            }
        }
    )
    
    # 5. Print success message
    print(f"Uploaded successfully: s3://{bucket_name}/{s3_key}")

if __name__ == "__main__":
    main()
