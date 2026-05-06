import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def setup_s3_bucket():
    bucket_name = "claimflow-knowledge-base"
    region = "us-east-1"
    
    try:
        s3_client = boto3.client('s3', region_name=region)
        
        # 1. Create Bucket
        try:
            # Note: us-east-1 doesn't require LocationConstraint for create_bucket
            s3_client.create_bucket(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['BucketAlreadyExists', 'BucketAlreadyOwnedByYou']:
                pass # Bucket already exists, move on
            else:
                raise e
                
        # 2. Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # 3. Block all public access
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        # 4. Print success message
        print(f"Bucket ready: {bucket_name}")
        
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please run 'aws configure' to set up your credentials.")
    except ClientError as e:
        print(f"An AWS API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    setup_s3_bucket()
