#!/bin/bash

# Start logging to a file for debugging
exec > >(tee -a /var/log/user-data.log) 2>&1
echo "User data script started"

# Update system packages
yum update -y
echo "System packages updated"

# Install Node.js (latest LTS version)
curl --silent --location https://rpm.nodesource.com/setup_16.x | bash -
yum install -y nodejs
echo "Node.js installed"

# Install required packages for AWS S3 and file upload (including build tools)
yum install -y gcc-c++ make
echo "Build tools installed"

# Install PM2 (Process Manager for Node.js)
npm install -g pm2
echo "PM2 installed"

# Create the Node.js app directory
mkdir -p /var/www/app
cd /var/www/app

# Initialize Node.js app
npm init -y
echo "Node.js app initialized"

# Install necessary Node.js packages
npm install express multer aws-sdk
if [ $? -eq 0 ]; then
    echo "Node.js packages installed"
else
    echo "Error installing Node.js packages" >&2
    exit 1
fi

# Create the basic HTML file to upload files
echo "<html>
<head>
    <title>File Upload to S3</title>
</head>
<body>
    <h1>Upload Files to S3 Bucket</h1>
    <form action='/upload' method='post' enctype='multipart/form-data'>
        <input type='file' name='file' required><br><br>
        <button type='submit'>Upload File</button>
    </form>
</body>
</html>" > /var/www/app/index.html
echo "HTML upload form created"

# Create the Node.js server for handling file uploads
echo "const express = require('express');
const multer = require('multer');
const AWS = require('aws-sdk');
const path = require('path');
const app = express();

// Set up AWS SDK with region and access
AWS.config.update({ region: 'us-east-1' });
const s3 = new AWS.S3();

// Set up multer storage for file uploads
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// Handle file uploads
app.post('/upload', upload.single('file'), (req, res) => {
    const params = {
        Bucket: 's3-project2-bucket',  // Replace with your S3 bucket name
        Key: \`\${Date.now()}-\${path.basename(req.file.originalname)}\`,
        Body: req.file.buffer,
        ContentType: req.file.mimetype,
    };

    s3.upload(params, (err, data) => {
        if (err) {
            return res.status(500).send('Error uploading file to S3');
        }
        res.send('File uploaded successfully! <a href=\'/\'>Back to home</a>');
    });
});

// Serve the static HTML file
app.get('/', (req, res) => {
    res.sendFile('/var/www/app/index.html');
});

// Start the server on port 80 and bind to all interfaces
app.listen(80, '0.0.0.0', () => {
    console.log('Server running on http://<your-ec2-ip>');
});" > /var/www/app/server.js
echo "Node.js server created"

# Start the Node.js server using PM2 for background management
cd /var/www/app
pm2 start /var/www/app/server.js --name "file-upload-app" --watch --no-daemon
echo "Node.js server started with PM2"

# Save PM2 process list to resurrect on reboot
pm2 save
echo "PM2 process list saved"

# Set up PM2 to restart on reboot
pm2 startup systemd
echo "PM2 startup configured"

echo "User data script completed"
