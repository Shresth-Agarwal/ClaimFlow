import boto3
import json

# Read insurance_kb.json
with open(r'C:\Users\guest123\ClaimFlow\backend\insurance_kb.json') as f:
    kb_data = json.load(f)

# Convert to readable text
lines = []
for entry in kb_data:
    page = entry.get('page', 'N/A')
    clause = entry.get('clause', 'N/A')
    text = entry.get('text', '')
    lines.append(f"Page {page}, Clause {clause}: {text}")

full_text = "\n\n".join(lines)

# Save locally
with open(r'C:\Users\guest123\ClaimFlow\backend\insurance_policy_full.txt', 'w') as f:
    f.write(full_text)

print("Content to upload:")
print(full_text)

# Upload to S3
s3 = boto3.client('s3', region_name='us-east-1')
s3.put_object(
    Bucket='claimflow-knowledge-base',
    Key='policies/insurance_policy_full.txt',
    Body=full_text,
    ContentType='text/plain'
)
print("Uploaded to S3 successfully!")
