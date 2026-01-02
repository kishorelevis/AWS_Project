#!/bin/bash

# Start logging
exec > >(tee /var/log/user-data.log) 2>&1
echo "User data script started"

# Update system packages

yum update -y
echo "System packages updated"

# Install necessary packages
yum install -y git aws-cli httpd
echo "Git, AWS CLI, and Apache installed"

# Start and enable Apache
systemctl enable httpd
systemctl start httpd
echo "Apache server started"

# Install Node.js and PM2
curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
yum install -y nodejs
npm install -g pm2
echo "Node.js and PM2 installed"

# Clone GitHub Repository for index.html
WEB_DIR="/var/www/html"
GITHUB_REPO="https://github.com/kishorelevis/AWS_Project.git/web_app"

mkdir -p $WEB_DIR
cd $WEB_DIR

if [ ! -d ".git" ]; then
    git clone $GITHUB_REPO .
    echo "Repository cloned"
else
    git fetch --all
    git reset --hard origin/main
    echo "Repository force-updated"
fi

# Set up a cron job to check for GitHub updates every 5 minutes
CRON_JOB="*/5 * * * * cd $WEB_DIR && git fetch --all && git reset --hard origin/main > /var/log/github_cron.log 2>&1"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "Cron job added to check for updates every 5 minutes"

# Create the Node.js file upload server (server.js)
APP_DIR="/var/www/app"
mkdir -p $APP_DIR

cat <<EOF > $APP_DIR/server.js
const express = require('express');
const multer = require('multer');
const AWS = require('aws-sdk');
const path = require('path');
const app = express();

// AWS Configuration
AWS.config.update({ region: 'us-east-1' });
const s3 = new AWS.S3();

// Get EC2 Public IP Automatically
const instanceMetadata = new AWS.MetadataService();
instanceMetadata.request('/latest/meta-data/public-ipv4', (err, data) => {
    if (err) console.error("Could not retrieve EC2 IP:", err);
    else console.log("Server running on http://" + data);
});

// Multer Storage (Temporary Memory)
const storage = multer.memoryStorage();
const upload = multer({
    storage: storage,
    limits: { fileSize: 10 * 1024 * 1024 } // 10MB file limit
});

// Upload API
app.post('/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).send('No file uploaded.');
    }

    const params = {
        Bucket: 's3-pro3-rawbucket',  // Replace with your actual raw S3 bucket
        Key: \`\${Date.now()}-\${path.basename(req.file.originalname)}\`,
        Body: req.file.buffer,
        ContentType: req.file.mimetype,
    };

    s3.upload(params, (err, data) => {
        if (err) {
            console.error("Error uploading:", err);
            return res.status(500).send('Error uploading file to S3');
        }
        console.log("File uploaded:", data.Location);
        res.send(\`File uploaded successfully! <a href="/">Back to home</a>\`);
    });
});

// Serve the HTML upload form
app.get('/', (req, res) => {
    res.sendFile('/var/www/html/index.html');
});

// Start server
app.listen(80, '0.0.0.0', () => {
    console.log('Server running');
});
EOF
echo "server.js created"

# Install required Node.js packages
cd $APP_DIR
npm install express multer aws-sdk
echo "Node.js dependencies installed"

# Start the Node.js application with PM2
pm2 start server.js --name "file-upload-app"
pm2 save
pm2 startup systemd
echo "Node.js app started with PM2"

# Restart Apache to apply changes
systemctl restart httpd
echo "Apache restarted"

echo "User data script completed"
