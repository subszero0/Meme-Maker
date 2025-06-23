# Lightsail Container Service Setup Guide

## 🎯 **New Deployment Method: Lightsail Container Service**

You've switched from SSH-based deployment to **AWS Lightsail Container Service**, which is more robust and doesn't require SSH key management.

### **Benefits of This Approach:**
- ✅ **No SSH keys needed** - Uses AWS credentials instead
- ✅ **Auto-scaling capabilities** - Can handle traffic spikes
- ✅ **Built-in load balancing** - Better reliability
- ✅ **Easier rollbacks** - Container-based deployments
- ✅ **Health monitoring** - Automatic health checks

---

## 📋 **Step-by-Step Setup Instructions**

### **Step 1: Create AWS IAM User for GitHub Actions**

1. **Go to AWS IAM Console**: `https://console.aws.amazon.com/iam/`

2. **Create User**:
   - Click **"Users"** → **"Create user"**
   - User name: `github-actions-lightsail`
   - Access type: **Programmatic access**

3. **Attach Permissions**:
   - Click **"Attach policies directly"**
   - Create custom policy with this JSON:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "lightsail:*",
           "iam:PassRole"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

4. **Save Credentials**:
   - Copy **Access Key ID**
   - Copy **Secret Access Key**
   - ⚠️ **Keep these secure** - you'll need them for GitHub

---

### **Step 2: Create Lightsail Container Service**

1. **Go to Lightsail Console**: `https://lightsail.aws.amazon.com/`

2. **Create Container Service**:
   - Click **"Containers"** → **"Create container service"**
   - **Service name**: `meme-maker-service` (must match workflow)
   - **Region**: `Asia Pacific (Mumbai) ap-south-1`
   - **Power**: **Micro** (1 GB RAM, 0.5 vCPU) - Recommended
   - **Scale**: `1` node initially

3. **Skip Initial Container Setup**:
   - Don't configure containers yet
   - GitHub Actions will handle the deployment
   - Click **"Create container service"**

4. **Wait for Service Creation**:
   - Takes ~5-10 minutes
   - Status should show **"Ready"**

---

### **Step 3: Configure GitHub Secrets**

1. **Go to Repository Secrets**: `https://github.com/subszero0/Meme-Maker/settings/secrets/actions`

2. **Remove Old SSH Secrets** (if they exist):
   - Delete `LIGHTSAIL_HOST`
   - Delete `LIGHTSAIL_USER`
   - Delete `LIGHTSAIL_SSH_KEY`

3. **Add New AWS Secrets**:
   
   **Secret 1:**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: (your IAM user access key)

   **Secret 2:**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: (your IAM user secret key)

---

### **Step 4: Verify Configuration**

Your workflow is now configured with:

```yaml
env:
  AWS_REGION: ap-south-1           # Mumbai region
  LIGHTSAIL_SERVICE_NAME: meme-maker-service
  CONTAINER_NAME: meme-maker-app
```

**Make sure these match your Lightsail setup!**

---

### **Step 5: Test the Deployment**

1. **Check GitHub Actions**: `https://github.com/subszero0/Meme-Maker/actions`

2. **Look for latest workflow run** (commit `0d20c07`)

3. **Expected Results**:
   - ✅ **Lint and Test**: Should pass
   - 🎯 **Deploy to Lightsail Container Service**: Check this job

---

## 🚀 **What the New Pipeline Does**

### **Build Phase:**
1. **Builds Docker image** using your docker-compose.yml
2. **Tags image** with Git commit SHA for traceability
3. **Pushes to Lightsail** container registry

### **Deploy Phase:**
1. **Creates deployment** with your app + Redis containers
2. **Sets environment variables** for local storage
3. **Configures health checks** on `/health` endpoint
4. **Exposes public URL** for your application

### **Container Configuration:**
```yaml
App Container:
  - Image: Your built application
  - Port: 8000 (HTTP)
  - Environment: Local storage config
  - Health Check: /health endpoint

Redis Container:
  - Image: redis:7-alpine
  - Port: 6379
  - Purpose: Job queue management
```

---

## 📊 **Monitoring Your Deployment**

### **Lightsail Console:**
1. Go to: `https://lightsail.aws.amazon.com/ls/webapp/us-east-1/container-services`
2. Click on **"meme-maker-service"**
3. Monitor:
   - **Deployments** tab - See deployment history
   - **Metrics** tab - CPU/Memory usage
   - **Logs** tab - Application logs

### **GitHub Actions:**
- **Workflow runs**: See build and deployment status
- **Deployment summary**: Shows deployed image and URL
- **Health checks**: Automatic testing after deployment

---

## 🎯 **Expected Outcomes**

### **After Successful Setup:**
1. ✅ **GitHub Actions passes** both jobs
2. ✅ **Lightsail service** shows "Ready" status
3. ✅ **Public URL available** (e.g., `https://meme-maker-service.ap-south-1.cs.amazonlightsail.com/`)
4. ✅ **Health endpoint** responds at `/health`
5. ✅ **Application accessible** via Lightsail URL

### **Your Website:**
- **Primary URL**: Lightsail Container Service URL
- **Custom Domain**: Can be configured later (memeit.pro)
- **Local Storage**: Files stored within containers
- **Auto-scaling**: Can handle traffic spikes

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

**1. AWS Credentials Error:**
```
Error: The security token included in the request is invalid
```
**Solution**: Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in GitHub secrets

**2. Service Not Found:**
```
Error: Container service 'meme-maker-service' not found
```
**Solution**: Create the Lightsail Container Service first (Step 2)

**3. Region Mismatch:**
```
Error: Service not found in region
```
**Solution**: Ensure service is created in `ap-south-1` (Mumbai)

**4. Health Check Fails:**
```
Health check failed after 10 attempts
```
**Solution**: Check application logs in Lightsail console

---

## 🎉 **Migration Complete!**

You've successfully migrated from:
- ❌ **SSH-based deployment** (unreliable, key management)
- ✅ **Lightsail Container Service** (robust, scalable, managed)

**Next Steps:**
1. ✅ Monitor GitHub Actions for successful deployment
2. ✅ Test the new Lightsail URL
3. ✅ Configure custom domain (optional)
4. ✅ Set up monitoring and alerts

Your application is now running on a modern, scalable container platform! 🚀 