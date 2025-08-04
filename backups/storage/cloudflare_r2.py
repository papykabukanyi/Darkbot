"""
Cloudflare R2 storage module for the sneaker bot.
"""

import logging
import json
import csv
import io
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger(__name__)

class R2Storage:
    """Class for storing and retrieving deals from Cloudflare R2."""
    
    def __init__(self, access_key_id, secret_access_key, endpoint_url, bucket_name):
        """
        Initialize the R2 storage.
        
        Args:
            access_key_id: Cloudflare R2 access key ID
            secret_access_key: Cloudflare R2 secret access key
            endpoint_url: Cloudflare R2 endpoint URL
            bucket_name: Cloudflare R2 bucket name
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        
        self.client = self._get_client()
        
    def _get_client(self):
        """
        Get a boto3 client for Cloudflare R2.
        
        Returns:
            boto3.client: Boto3 S3 client for R2
        """
        try:
            client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto'  # R2 ignores this but boto3 requires it
            )
            
            # Verify connection by listing buckets
            client.list_buckets()
            
            logger.info(f"Successfully connected to Cloudflare R2")
            return client
            
        except ClientError as e:
            logger.error(f"Error connecting to Cloudflare R2: {e}")
            return None
        
    def upload_deals(self, deals: List[Dict[str, Any]]) -> bool:
        """
        Upload deals to Cloudflare R2.
        
        Args:
            deals: List of deal dictionaries to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not deals:
            logger.info("No deals to upload to R2")
            return False
            
        if not self.client:
            logger.error("R2 client not initialized")
            return False
            
        # Get current date for folder structure
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Upload as JSON
        try:
            json_key = f"{today}/deals_{timestamp}.json"
            json_data = json.dumps(deals, indent=2)
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=json_key,
                Body=json_data,
                ContentType='application/json'
            )
            
            logger.info(f"Uploaded {len(deals)} deals as JSON to R2: {json_key}")
            
            # Also upload as CSV
            csv_key = f"{today}/deals_{timestamp}.csv"
            
            # Create CSV in memory
            csv_buffer = io.StringIO()
            fieldnames = [
                'title', 'brand', 'price', 'original_price', 
                'discount_percent', 'source', 'url'
            ]
            
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for deal in deals:
                writer.writerow(deal)
                
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=csv_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            logger.info(f"Uploaded {len(deals)} deals as CSV to R2: {csv_key}")
            
            # Upload a "latest.json" file that's overwritten each time
            latest_key = "latest/latest.json"
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=latest_key,
                Body=json_data,
                ContentType='application/json'
            )
            
            logger.info(f"Updated latest.json in R2")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading deals to R2: {e}")
            return False
            
    def list_deal_files(self) -> List[str]:
        """
        List all deal files in the R2 bucket.
        
        Returns:
            List[str]: List of file keys
        """
        if not self.client:
            logger.error("R2 client not initialized")
            return []
            
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
                
        except ClientError as e:
            logger.error(f"Error listing files in R2: {e}")
            return []
            
    def download_deals(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Download deals from Cloudflare R2.
        
        Args:
            key: The key of the file to download
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of deals, or None if error
        """
        if not self.client:
            logger.error("R2 client not initialized")
            return None
            
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            if key.endswith('.json'):
                return json.loads(content)
            elif key.endswith('.csv'):
                reader = csv.DictReader(io.StringIO(content))
                return list(reader)
            else:
                logger.error(f"Unsupported file format: {key}")
                return None
                
        except ClientError as e:
            logger.error(f"Error downloading {key} from R2: {e}")
            return None
            
    def continue_to_iterate(self, last_file_key: Optional[str] = None) -> bool:
        """
        Check whether we should continue iterating through sites based on historical data.
        
        Args:
            last_file_key: The key of the last file uploaded, if any
            
        Returns:
            bool: True if we should continue iterating, False otherwise
        """
        if not self.client or not last_file_key:
            # No client or no previous file, always continue
            return True
            
        try:
            # Get today's date for comparison
            today = datetime.now().strftime('%Y-%m-%d')
            
            # List all objects for today
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{today}/"
            )
            
            if 'Contents' not in response or not response['Contents']:
                # No files for today yet, continue
                return True
                
            # If we have less than 5 files for today, continue
            if len(response['Contents']) < 5:
                return True
                
            # Get the latest file and check if it's recent enough
            latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
            time_diff = datetime.now() - latest_file['LastModified'].replace(tzinfo=None)
            
            # If the latest file is older than 2 hours, continue
            if time_diff.total_seconds() > 7200:  # 2 hours = 7200 seconds
                return True
                
            # Otherwise, we've done enough iterations for now
            return False
            
        except ClientError as e:
            logger.error(f"Error checking iteration status: {e}")
            # On error, continue to be safe
            return True
