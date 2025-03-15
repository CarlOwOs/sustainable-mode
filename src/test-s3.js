require('dotenv').config();
const AWS = require('aws-sdk');

// Configure AWS
AWS.config.update({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

const s3 = new AWS.S3();

async function testS3Connection() {
  try {
    console.log('Testing S3 connection...');
    console.log('AWS Region:', process.env.AWS_REGION);
    console.log('S3 Bucket:', process.env.S3_BUCKET_NAME);
    
    // List buckets to test credentials
    const listBucketsResult = await s3.listBuckets().promise();
    console.log('Available buckets:', listBucketsResult.Buckets.map(b => b.Name));
    
    // Check if our bucket exists
    const bucketExists = listBucketsResult.Buckets.some(b => b.Name === process.env.S3_BUCKET_NAME);
    console.log('Target bucket exists:', bucketExists);
    
    if (bucketExists) {
      // List objects in the bucket
      const listObjectsResult = await s3.listObjectsV2({ 
        Bucket: process.env.S3_BUCKET_NAME,
        MaxKeys: 10
      }).promise();
      
      console.log('Objects in bucket:', listObjectsResult.Contents ? listObjectsResult.Contents.length : 0);
      if (listObjectsResult.Contents && listObjectsResult.Contents.length > 0) {
        console.log('Sample objects:', listObjectsResult.Contents.map(obj => obj.Key));
      }
    }
    
    console.log('S3 connection test completed successfully');
  } catch (error) {
    console.error('Error testing S3 connection:', error);
  }
}

testS3Connection(); 