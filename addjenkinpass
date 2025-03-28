#!/bin/bash

# Start logging
exec > >(tee /var/log/user-data.log) 2>&1
echo "User data script started"

# Update system packages
yum update -y
echo "System packages updated"

# Install Java (required for Jenkins)
yum install -y java-11-openjdk
echo "Java installed"

# Add Jenkins repository and import the key
wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io-2023.key
echo "Jenkins repository added"

# Install Jenkins
yum install -y jenkins
echo "Jenkins installed"

# Start and enable Jenkins service
systemctl enable jenkins
systemctl start jenkins
echo "Jenkins started"

# Wait for Jenkins to fully start
sleep 60  # Give Jenkins time to initialize

# Retrieve Jenkins Initial Admin Password and Store It
ADMIN_PASSWORD_FILE="/var/lib/jenkins/secrets/initialAdminPassword"
JENKINS_CLI="/usr/bin/java -jar /var/cache/jenkins/war/WEB-INF/jenkins-cli.jar"
JENKINS_URL="http://localhost:8080"

if [ -f "$ADMIN_PASSWORD_FILE" ]; then
    ADMIN_PASSWORD=$(cat $ADMIN_PASSWORD_FILE)
    echo "Jenkins Admin Password: $ADMIN_PASSWORD" > /root/jenkins_admin_password.txt
    echo "Jenkins Admin Password stored at /root/jenkins_admin_password.txt"
fi

# Install Git (needed for pulling repositories)
yum install -y git
echo "Git installed"

# Install AWS CLI (needed for uploading backups to S3)
yum install -y aws-cli
echo "AWS CLI installed"

# Install Node.js and PM2
curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
yum install -y nodejs
npm install -g pm2
echo "Node.js and PM2 installed"

# Clone GitHub Repository ONLY IF it doesn't exist
APP_DIR="/var/www/app"
GITHUB_REPO="https://github.com/kishorelevis/AWS_Project.git"

mkdir -p $APP_DIR
cd $APP_DIR

if [ ! -d ".git" ]; then
    git clone $GITHUB_REPO .
    echo "Repository cloned"
else
    echo "Repository already exists. Skipping clone."
fi

# Install required Node.js packages
npm install express multer aws-sdk
echo "Node.js packages installed"

# Start the Node.js application with PM2
cd $APP_DIR
pm2 start server.js --name "file-upload-app"
pm2 save
pm2 startup systemd
echo "Node.js app started with PM2"

# Display stored Jenkins admin password
echo "Jenkins setup completed."
echo "Admin password stored at: /root/jenkins_admin_password.txt"

echo "User data script completed"
