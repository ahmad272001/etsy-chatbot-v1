# Manual EC2 Deployment Guide

## 🎯 **Step-by-Step Manual EC2 Setup**

### **Step 1: Create EC2 Instance via AWS Console**

1. **Go to AWS Console** → EC2 → Launch Instance
2. **Choose AMI**: Ubuntu 22.04 LTS (Free tier eligible)
3. **Instance Type**: t3.small (or t2.micro for free tier)
4. **Key Pair**: Create new key pair (download .pem file)
5. **Security Group**: Create new with these rules:
   - SSH (22): 0.0.0.0/0
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0
6. **Launch Instance**

### **Step 2: SSH into Your Instance**

```bash
# Replace with your actual key and IP
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

### **Step 3: Install Docker**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Logout and login again for group changes to take effect
exit
```

### **Step 4: Upload Your Code**

```bash
# From your local machine, upload the project
scp -i your-key.pem -r . ubuntu@YOUR_PUBLIC_IP:~/app/
```

### **Step 5: Deploy Application**

```bash
# SSH back into instance
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP

# Navigate to app directory
cd ~/app

# Create .env file with your actual values
nano .env
```

**Add your environment variables to .env:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# JWT Configuration
JWT_SECRET=123
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_MIN=0.7

QDRANT_URL=https://7162f887-8e1e-431b-ac7d-f78e1e0dc1db.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.u7vsGZVQmnvWuBy9oOpx5fBmzfMaBa_it0qAo2SUBuc
QDRANT_COLLECTION_NAME=rag_chatbot

ENV=production
```

```bash
# Build and run
docker-compose up -d --build

# Check status
docker ps
docker logs etsychatbot-app
```

### **Step 6: Access Your Application**

- **URL**: http://YOUR_PUBLIC_IP
- **Health Check**: http://YOUR_PUBLIC_IP/health

---

## **Method 2: AWS CLI Simple Deployment**

### **Step 1: Create Instance with AWS CLI**

```bash
# Create key pair
aws ec2 create-key-pair \
    --key-name etsychatbot-key \
    --query 'KeyMaterial' \
    --output text > etsychatbot-key.pem

chmod 400 etsychatbot-key.pem

# Create security group
aws ec2 create-security-group \
    --group-name etsychatbot-sg \
    --description "Security group for RAG Chatbot"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
    --group-names etsychatbot-sg \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

# Add rules
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp --port 80 --cidr 0.0.0.0/0

# Get latest Ubuntu AMI
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text)

# Launch instance
aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type t3.small \
    --key-name etsychatbot-key \
    --security-group-ids $SG_ID
```

### **Step 2: Follow Manual Steps 2-6 Above**

---

## **Method 3: AWS Elastic Beanstalk (Easiest)**

### **Step 1: Prepare Your Application**

Create `Procfile` in your project root:
```
web: python run.py
```

### **Step 2: Deploy via AWS Console**

1. **Go to Elastic Beanstalk Console**
2. **Create Application**
3. **Upload your code as ZIP file**
4. **Choose Python platform**
5. **Configure environment variables**
6. **Deploy**

### **Step 3: Set Environment Variables**

In Elastic Beanstalk Console:
- Go to Configuration → Software
- Add environment variables:
  - `OPENAI_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `JWT_SECRET`
  - etc.

---

## **Method 4: AWS App Runner (Serverless)**

### **Step 1: Create apprunner.yaml**

```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.11
  command: python run.py
  network:
    port: 8000
  env:
    - name: OPENAI_API_KEY
      value: your_openai_api_key
    - name: QDRANT_URL
      value: your_qdrant_url
    - name: QDRANT_API_KEY
      value: your_qdrant_api_key
    - name: JWT_SECRET
      value: your_jwt_secret
```

### **Step 2: Deploy via AWS Console**

1. **Go to App Runner Console**
2. **Create Service**
3. **Connect to your GitHub repository**
4. **Configure build settings**
5. **Deploy**

---

## **🎯 Recommended Approach**

**For learning AWS**: Use **Method 1 (Manual EC2)** - gives you full control and understanding

**For quick deployment**: Use **Method 3 (Elastic Beanstalk)** - managed service, no server management

**For production**: Use **Method 4 (App Runner)** - serverless, auto-scaling

---

## **💰 Cost Comparison**

- **EC2 t3.small**: ~$15/month
- **Elastic Beanstalk**: ~$10-25/month
- **App Runner**: ~$5-20/month (pay per request)

---

## **🚨 Troubleshooting**

### **Common Issues:**

1. **Can't SSH**: Check security group rules
2. **Port not accessible**: Verify firewall settings
3. **Docker not working**: Check Docker service status
4. **Environment variables**: Verify .env file format

### **Useful Commands:**

```bash
# Check instance status
aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# Get public IP
aws ec2 describe-instances \
    --instance-ids i-1234567890abcdef0 \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text

# Check security group
aws ec2 describe-security-groups --group-names etsychatbot-sg
```

---

**🎉 Choose the method that best fits your learning goals and deployment needs!**
