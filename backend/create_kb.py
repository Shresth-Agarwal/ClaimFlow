import boto3
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError

def main():
    kb_name = "claimflow-policy-kb"
    role_arn = "arn:aws:iam::795001058515:role/WSParticipantRole"
    embedding_model_arn = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
    bucket_name = "claimflow-knowledge-base"
    prefix = "policies/"
    region = "us-east-1"
    collection_name = "claimflow-vector-store"
    index_name = "bedrock-knowledge-base-default-index"
    
    aoss_client = boto3.client('opensearchserverless', region_name=region)
    bedrock_agent = boto3.client('bedrock-agent', region_name=region)
    sts_client = boto3.client('sts', region_name=region)
    
    caller_arn = sts_client.get_caller_identity()['Arn']
    
    print("1. Creating OpenSearch Serverless Policies...")
    
    # 1. Encryption Policy
    enc_policy = json.dumps({
        "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]}],
        "AWSOwnedKey": True
    })
    try:
        aoss_client.create_security_policy(
            name=f"{collection_name}-enc",
            type='encryption',
            policy=enc_policy
        )
    except ClientError as e:
        if "ConflictException" not in str(e): print(f"Warning/Error creating encryption policy: {e}")

    # 2. Network Policy
    net_policy = json.dumps([{
        "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{collection_name}"]},
                  {"ResourceType": "dashboard", "Resource": [f"collection/{collection_name}"]}],
        "AllowFromPublic": True
    }])
    try:
        aoss_client.create_security_policy(
            name=f"{collection_name}-net",
            type='network',
            policy=net_policy
        )
    except ClientError as e:
        if "ConflictException" not in str(e): print(f"Warning/Error creating network policy: {e}")

    # 3. Data Access Policy
    data_policy = json.dumps([{
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": [f"collection/{collection_name}"],
                "Permission": ["aoss:*"]
            },
            {
                "ResourceType": "index",
                "Resource": [f"index/{collection_name}/*"],
                "Permission": ["aoss:*"]
            }
        ],
        "Principal": [
            caller_arn,
            role_arn
        ]
    }])
    try:
        aoss_client.create_access_policy(
            name=f"{collection_name}-acc",
            type='data',
            policy=data_policy
        )
    except ClientError as e:
        if "ConflictException" not in str(e): print(f"Warning/Error creating data access policy: {e}")

    print("2. Creating OpenSearch Serverless Collection...")
    
    collection_id = None
    collection_arn = None
    collection_ep = None
    
    try:
        response = aoss_client.create_collection(
            name=collection_name,
            type='VECTORSEARCH'
        )
        collection_id = response['createCollectionDetail']['id']
        collection_arn = response['createCollectionDetail']['arn']
    except ClientError as e:
        if "ConflictException" in str(e):
            print("Collection already exists, retrieving details...")
            collections = aoss_client.list_collections(collectionFilters={'name': collection_name})['collectionSummaries']
            if collections:
                collection_id = collections[0]['id']
                collection_arn = collections[0]['arn']
        else:
            raise e

    print("Waiting for Collection to become ACTIVE (this may take a few minutes)...")
    while True:
        resp = aoss_client.batch_get_collection(ids=[collection_id])
        status = resp['collectionDetails'][0]['status']
        if status == 'ACTIVE':
            collection_ep = resp['collectionDetails'][0]['collectionEndpoint']
            break
        print(f"Status: {status}. Waiting 15s...")
        time.sleep(15)

    print(f"Collection ACTIVE! Endpoint: {collection_ep}")
    
    print("3. Creating Vector Index...")
    time.sleep(15) # Wait briefly after active for DNS/routing to settle
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    
    host = collection_ep.replace('https://', '')
    
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )
    
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "bedrock-embedding": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "l2"
                    }
                },
                "AMAZON_BEDROCK_TEXT_CHUNK": {
                    "type": "text"
                },
                "AMAZON_BEDROCK_METADATA": {
                    "type": "text",
                    "index": False
                }
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=index_body)
        print("Vector index created.")
        time.sleep(10) # wait for index to be fully propagated
    except Exception as e:
        if "resource_already_exists_exception" in str(e):
            print("Vector index already exists.")
        else:
            raise e

    print(f"4. Creating Knowledge Base '{kb_name}'...")
    kb_id = None
    
    try:
        response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': embedding_model_arn
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': index_name,
                    'fieldMapping': {
                        'vectorField': 'bedrock-embedding',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            }
        )
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"Knowledge Base ID: {kb_id}")
    except ClientError as e:
        if "ConflictException" in str(e):
            print("Knowledge Base already exists.")
            # find the KB id
            kbs = bedrock_agent.list_knowledge_bases()['knowledgeBaseSummaries']
            for kb in kbs:
                if kb['name'] == kb_name:
                    kb_id = kb['knowledgeBaseId']
                    print(f"Found existing Knowledge Base ID: {kb_id}")
                    break
        else:
            raise e
    
    if not kb_id:
        print("Failed to determine Knowledge Base ID.")
        return

    print("5. Creating Data Source...")
    ds_id = None
    try:
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"{kb_name}-datasource",
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f"arn:aws:s3:::{bucket_name}",
                    'inclusionPrefixes': [prefix]
                }
            }
        )
        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"Data Source ID: {ds_id}")
    except ClientError as e:
        if "ConflictException" in str(e):
            print("Data Source already exists.")
            dss = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)['dataSourceSummaries']
            for ds in dss:
                if ds['name'] == f"{kb_name}-datasource":
                    ds_id = ds['dataSourceId']
                    print(f"Found existing Data Source ID: {ds_id}")
                    break
        else:
            raise e

    if not ds_id:
        print("Failed to determine Data Source ID.")
        return

    print("6. Starting Ingestion Job...")
    try:
        ingest_resp = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        print(f"Ingestion Job started! ID: {ingest_resp['ingestionJob']['ingestionJobId']}")
    except ClientError as e:
        print(f"Failed to start ingestion job: {e}")

    # Save to json
    out_path = r"C:\Users\guest123\ClaimFlow\backend\kb_config.json"
    with open(out_path, 'w') as f:
        json.dump({
            "knowledge_base_id": kb_id,
            "data_source_id": ds_id
        }, f, indent=4)
    print(f"Saved IDs to {out_path}")

if __name__ == "__main__":
    main()
