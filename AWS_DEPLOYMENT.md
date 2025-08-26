# AWS Deployment Guide

## 🚀 **Quick Deployment Options**

### **Option 1: Simple EC2 Deployment (Recommended for Learning)**

```bash
# Run the simple deployment script
chmod +x simple-aws-deploy.sh
./simple-aws-deploy.sh
```

This creates an EC2 instance and gives you the commands to:
1. SSH into the instance
2. Install Docker
3. Upload your code
4. Deploy your application

### **Option 2: Manual EC2 Setup**

Follow the step-by-step guide in `manual-ec2-deploy.md`

### **Option 3: AWS Elastic Beanstalk**

1. Use the `Procfile` (already created)
2. Go to AWS Console → Elastic Beanstalk
3. Upload your code as ZIP
4. Configure environment variables (see below)
5. Deploy

### **Option 4: AWS App Runner**

1. Use the `apprunner.yaml` (already configured with your env vars)
2. Go to AWS Console → App Runner
3. Connect to your GitHub repository
4. Deploy

## 🔧 **Environment Variables (Already Configured)**

Your application uses these environment variables (already set in deployment files):

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
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

## 📁 **Files for Deployment**

- `Dockerfile` - Containerizes your app
- `docker-compose.yml` - Local testing with your env vars
- `Procfile` - For Elastic Beanstalk
- `apprunner.yaml` - For App Runner (with your env vars)
- `simple-aws-deploy.sh` - Simple EC2 deployment script
- `manual-ec2-deploy.md` - Manual deployment guide

## 💰 **Cost Comparison**

- **EC2**: ~$15-20/month
- **Elastic Beanstalk**: ~$10-25/month
- **App Runner**: ~$5-20/month

## 🎯 **Recommended Approach**

**For learning AWS**: Use `./simple-aws-deploy.sh`
**For quick deployment**: Use Elastic Beanstalk
**For production**: Use App Runner

---

**🎉 Ready to deploy! Choose your preferred method above.**
