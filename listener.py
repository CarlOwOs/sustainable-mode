import boto3
import time
from datetime import datetime, timedelta
import os
from typing import List
import sqlite3
import subprocess
import dotenv
dotenv.load_dotenv()

class S3Listener:
    def __init__(self, bucket_name: str, check_interval: int = 5):
        """
        Initialize the S3 listener
        
        Args:
            bucket_name (str): Name of the S3 bucket to monitor
            check_interval (int): How often to check for new files (in seconds)
        """
        self.bucket_name = bucket_name
        self.check_interval = check_interval
        self.s3_client = boto3.client('s3')
        self.db_path = "processed_files.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database and create table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS processed_files (
                        file_key TEXT PRIMARY KEY,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    def is_file_processed(self, file_key: str) -> bool:
        """
        Check if a file has been processed before
        
        Args:
            file_key (str): The key of the file to check
            
        Returns:
            bool: True if file has been processed, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM processed_files WHERE file_key = ?", (file_key,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking processed file: {str(e)}")
            return False

    def mark_file_processed(self, file_key: str):
        """
        Mark a file as processed in the database
        
        Args:
            file_key (str): The key of the file to mark as processed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO processed_files (file_key) VALUES (?)", (file_key,))
                conn.commit()
        except Exception as e:
            print(f"Error marking file as processed: {str(e)}")

    def get_recent_files(self, seconds: int = 60) -> List[str]:
        """
        Get list of files uploaded in the last specified seconds
        
        Args:
            seconds (int): Number of seconds to look back
            
        Returns:
            List[str]: List of recently uploaded file keys
        """
        seconds += 3600 # adjust for timezone
        try:
            # Calculate the timestamp for comparison
            time_threshold = datetime.now() - timedelta(seconds=seconds)
            
            # List objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            recent_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) > time_threshold:
                        recent_files.append(obj['Key'])
            
            return recent_files
            
        except Exception as e:
            print(f"Error checking recent files: {str(e)}")
            return []
    
    def process_new_files(self, files: List[str]):
        """
        Process newly uploaded files
        
        Args:
            files (List[str]): List of file keys to process
        """
        for file_key in files:
            if not self.is_file_processed(file_key):
                print(f"Processing new file: {file_key}")
                
                # Get current environment and update it with our env vars
                env = os.environ.copy()
                subprocess.run(["python", "agent-mouse.py"], env=env)
                
                # Mark the file as processed after successful processing
                self.mark_file_processed(file_key)
            else:
                print(f"File already processed: {file_key}")
    
    def start_listening(self):
        """Start the continuous monitoring process"""
        print(f"Starting to monitor S3 bucket: {self.bucket_name}")
        
        while True:
            try:
                print("Checking for recent files...")
                # Check for recent files
                recent_files = self.get_recent_files()
                
                if recent_files:
                    print(f"Found {len(recent_files)} new files!")
                    self.process_new_files(recent_files)
                
                # Wait for the next check interval
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping the listener...")
                break
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    # Replace with your bucket name
    # read from .env
    BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    
    if not BUCKET_NAME:
        raise ValueError("Please set the S3_BUCKET_NAME environment variable")
    
    # Create and start the listener
    listener = S3Listener(BUCKET_NAME)
    listener.start_listening()
