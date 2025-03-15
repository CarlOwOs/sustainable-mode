require('dotenv').config();
const express = require('express');
const multer = require('multer');
const AWS = require('aws-sdk');
const path = require('path');
const cors = require('cors');
const fs = require('fs');

// Initialize Express app
const app = express();
const port = process.env.PORT || 3000;

// Configure middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../public')));

// Configure AWS
AWS.config.update({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

const s3 = new AWS.S3();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = path.join(__dirname, '../uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 100 * 1024 * 1024 }, // 10MB limit
  fileFilter: function (req, file, cb) {
    // Accept images only
    if (!file.originalname.match(/\.(jpg|jpeg|png|gif|JPG)$/)) {
      return cb(new Error('Only image files are allowed!'), false);
    }
    cb(null, true);
  }
});

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.post('/upload', upload.single('image'), async (req, res) => {
  try {
    console.log('Upload request received');
    
    if (!req.file) {
      console.log('No file in request');
      return res.status(400).json({ error: 'No file uploaded' });
    }
    
    console.log('File received:', req.file.filename, 'Size:', req.file.size, 'Type:', req.file.mimetype);

    const fileContent = fs.readFileSync(req.file.path);
    const params = {
      Bucket: process.env.S3_BUCKET_NAME,
      Key: `uploads/${req.file.filename}`,
      Body: fileContent,
      ContentType: req.file.mimetype,
    };

    console.log('Uploading to S3 bucket:', process.env.S3_BUCKET_NAME);
    
    // Upload to S3
    const uploadResult = await s3.upload(params).promise();
    console.log('S3 upload successful, URL:', uploadResult.Location);
    
    // Delete local file after upload
    fs.unlinkSync(req.file.path);

    res.json({
      message: 'File uploaded successfully',
      fileUrl: uploadResult.Location
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ error: `Failed to upload file: ${error.message}` });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
}); 