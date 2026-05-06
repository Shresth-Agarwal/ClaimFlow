import os
import shutil

base_dir = r"C:\Users\guest123\ClaimFlow\backend"
core_dir = os.path.join(base_dir, "core")
guardrails_dir = os.path.join(base_dir, "guardrails")

os.makedirs(core_dir, exist_ok=True)
os.makedirs(guardrails_dir, exist_ok=True)

# 1. guardrails.py
with open(os.path.join(base_dir, "guardrails.py"), "r", encoding="utf-8") as f:
    guardrails_content = f.read()

guardrails_new_content = '''# This will be enhanced by Amazon Bedrock Guardrails
import boto3

def apply_bedrock_guardrail(text, guardrail_id, guardrail_version):
    client = boto3.client('bedrock-runtime')
    response = client.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source='INPUT',
        content=[{'text': {'text': text}}]
    )
    if response.get('action') == 'GUARDRAIL_INTERVENED':
        for output in response.get('outputs', []):
            return output.get('text', text)
    return text

''' + guardrails_content

with open(os.path.join(guardrails_dir, "local_guardrails.py"), "w", encoding="utf-8") as f:
    f.write(guardrails_new_content)
os.remove(os.path.join(base_dir, "guardrails.py"))

# 2. retrieval.py
with open(os.path.join(base_dir, "retrieval.py"), "r", encoding="utf-8") as f:
    retrieval_content = f.read()

retrieval_new_content = retrieval_content.replace("def retrieve(original_query, kb):", "def local_retrieve(original_query, kb):")

with open(os.path.join(core_dir, "local_retrieval.py"), "w", encoding="utf-8") as f:
    f.write(retrieval_new_content)
os.remove(os.path.join(base_dir, "retrieval.py"))

# 3. generator.py
with open(os.path.join(base_dir, "generator.py"), "r", encoding="utf-8") as f:
    generator_content = f.read()

generator_new_content = generator_content.replace("def generate_answer(context, query):", "def local_generate(context, query):")

with open(os.path.join(core_dir, "local_generator.py"), "w", encoding="utf-8") as f:
    f.write(generator_new_content)
os.remove(os.path.join(base_dir, "generator.py"))

# 4. intent.py
shutil.move(os.path.join(base_dir, "intent.py"), os.path.join(core_dir, "intent.py"))

# 5. pipeline.py
shutil.move(os.path.join(base_dir, "pipeline.py"), os.path.join(core_dir, "legacy_pipeline.py"))

print("Migration complete. All Akhira logic preserved in ClaimFlow backend.")
