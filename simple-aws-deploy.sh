#!/bin/bash

# Simple AWS Deployment Script
# This script creates EC2 instance without complex user data

set -e

echo "🚀 Simple AWS Deployment for RAG Chatbot"
echo "========================================="

# Configuration
AWS_REGION="us-east-1"
PROJECT_NAME="etsychatbot"
KEY_NAME="${PROJECT_NAME}-key"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

print_success "AWS CLI and credentials verified!"

# Step 1: Create Key Pair
print_status "Creating EC2 key pair..."
if aws ec2 describe-key-pairs --key-names $KEY_NAME &> /dev/null; then
    print_warning "Key pair $KEY_NAME already exists."
else
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    
    chmod 400 ${KEY_NAME}.pem
    print_success "Key pair created: ${KEY_NAME}.pem"
fi

# Step 2: Create Security Group
print_status "Creating security group..."
SG_NAME="${PROJECT_NAME}-sg"

if aws ec2 describe-security-groups --group-names $SG_NAME &> /dev/null; then
    print_warning "Security group $SG_NAME already exists."
    SG_ID=$(aws ec2 describe-security-groups --group-names $SG_NAME --query 'SecurityGroups[0].GroupId' --output text)
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SG_NAME \
        --description "Security group for $PROJECT_NAME" \
        --query 'GroupId' --output text)
    
    # Add security group rules
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 80 --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp --port 443 --cidr 0.0.0.0/0
    
    print_success "Security group created: $SG_ID"
fi

# Step 3: Get Latest Ubuntu AMI
print_status "Getting latest Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text)

print_success "Using AMI: $AMI_ID"

# Step 4: Launch EC2 Instance
print_status "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type t3.small \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --query "Instances[0].InstanceId" \
    --output text)

print_success "Instance created: $INSTANCE_ID"

# Step 5: Wait for instance to be running
print_status "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Step 6: Get Public IP
print_status "Getting public IP..."
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text)

print_success "Instance is running at: $PUBLIC_IP"

# Step 7: Display next steps
echo ""
echo "🎉 EC2 instance deployed successfully!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. SSH into your instance:"
echo "   ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo ""
echo "2. Install Docker:"
echo "   sudo apt update && sudo apt upgrade -y"
echo "   sudo apt install -y docker.io"
echo "   sudo systemctl start docker"
echo "   sudo systemctl enable docker"
echo "   sudo usermod -aG docker ubuntu"
echo "   exit"
echo ""
echo "3. Upload your code:"
echo "   scp -i ${KEY_NAME}.pem -r . ubuntu@$PUBLIC_IP:~/app/"
echo ""
echo "4. Deploy application:"
echo "   ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo "   cd ~/app"
echo "   nano .env  # Add your environment variables"
echo "   docker-compose up -d --build"
echo ""
echo "5. Access your application:"
echo "   http://$PUBLIC_IP"
echo ""
echo "🔑 Key file: ${KEY_NAME}.pem"
echo "🌐 Public IP: $PUBLIC_IP"
echo "🆔 Instance ID: $INSTANCE_ID"
echo ""
echo "💡 Tip: Your application will be available at http://$PUBLIC_IP once deployed!"
