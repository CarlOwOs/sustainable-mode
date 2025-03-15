# S3 Image Uploader

A simple web application that allows users to upload images to an AWS S3 bucket.

## Features

- Upload images to an AWS S3 bucket
- Drag and drop interface
- Image preview before upload
- File type validation (only images allowed)
- File size limit (10MB)

## Prerequisites

- Node.js (v12 or higher)
- AWS account with S3 bucket
- AWS access key and secret key with S3 permissions

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd s3-image-uploader
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file in the root directory with the following variables:
   ```
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_REGION=your_region
   S3_BUCKET_NAME=your_bucket_name
   PORT=3000
   ```

4. Make sure your S3 bucket has the appropriate CORS configuration to allow uploads from your application domain.

## Running the Application

Start the development server:
```
npm run dev
```

The application will be available at http://localhost:3000

## Production Deployment

For production deployment, you can use:
```
npm start
```

## S3 Bucket CORS Configuration

You may need to configure CORS for your S3 bucket. Here's an example configuration:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["http://localhost:3000", "https://yourdomain.com"],
    "ExposeHeaders": []
  }
]
```

## License

MIT