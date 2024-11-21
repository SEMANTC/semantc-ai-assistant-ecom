# Scripts Documentation

## Overview
This directory contains automation scripts for building, deploying, and managing the E-commerce AI Assistant service in Google Cloud Platform (GCP).

## Scripts

### Build and Deploy Script (`build_push.sh`)
Automated script for building and deploying the application to Cloud Run with GPU support.

#### Prerequisites
- Google Cloud SDK (`gcloud`) installed and configured
- Docker installed and configured
- Appropriate GCP permissions:
  - Container Registry access
  - Cloud Run admin
  - Service Account user

#### Configuration
```bash
# Key configuration variables
PROJECT_ID="semantc-sandbox"
REGION="us-central1"
SERVICE_NAME="ai-assistant-ecom"
```

#### Features
- 🔄 Automated build and deploy process
- 🔒 Authentication handling
- 🔙 Automatic rollback on failure
- 🏥 Health checks
- 📊 Deployment verification
- 🎯 GPU configuration

#### Usage
```bash
# Make script executable (first time only)
chmod +x build_push.sh

# Run the script
./build_push.sh
```

#### Process Flow
1. **Initialization**
   ```bash
   # Checks and validations
   - Command availability check
   - Project verification
   - Resource validation
   ```

2. **Build Phase**
   ```bash
   # Docker build with platform optimization
   docker build --platform linux/amd64 -t ${IMAGE_NAME} .
   ```

3. **Deploy Phase**
   ```bash
   # Cloud Run deployment with GPU
   gcloud run deploy ${SERVICE_NAME} \
     --image ${IMAGE_NAME} \
     --gpu-type=nvidia-tesla-t4
   ```

4. **Verification Phase**
   ```bash
   # Health check and monitoring
   - Service availability check
   - Health endpoint verification
   - Deployment status confirmation
   ```

#### Resource Configuration
- CPU: 4 cores
- Memory: 16GB
- GPU: NVIDIA T4
- Timeout: 3600s

#### Error Handling
```bash
# Example error scenarios and handling
- Build failures → Clean up and exit
- Deploy failures → Automatic rollback
- Health check failures → Warning and verification
```

## Common Tasks

### 1. Deploy to Production
```bash
./build_push.sh
```

### 2. View Deployment Logs
```bash
# Get the latest deployment logs
gcloud run services get-iam-policy ${SERVICE_NAME} \
  --region=${REGION} \
  --format='table(bindings)'
```

### 3. Rollback to Previous Version
```bash
# Get previous versions
gcloud run revisions list --service=${SERVICE_NAME} --region=${REGION}

# Rollback to specific version
gcloud run services update-traffic ${SERVICE_NAME} \
  --region=${REGION} \
  --to-revisions=REVISION_ID=100
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Reauthenticate with GCP
   gcloud auth login
   gcloud auth configure-docker
   ```

2. **Resource Limits**
   ```bash
   # Check current quotas
   gcloud compute project-info describe --project ${PROJECT_ID}
   ```

3. **Deployment Failures**
   ```bash
   # Check service status
   gcloud run services describe ${SERVICE_NAME} --region=${REGION}
   ```

### Health Checks
```bash
# Manual health check
curl -f $(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format='value(status.url)')/health
```

## Best Practices

1. **Before Deployment**
   - Review configuration changes
   - Test locally if possible
   - Check resource requirements

2. **During Deployment**
   - Monitor logs for errors
   - Verify service health
   - Check resource utilization

3. **After Deployment**
   - Verify application functionality
   - Monitor performance metrics
   - Check error rates

## Future Enhancements
- [ ] Add configuration file support
- [ ] Implement blue-green deployments
- [ ] Add performance testing
- [ ] Enhance monitoring integration
- [ ] Add backup procedures

## Contributing
When adding new scripts:
1. Follow existing naming conventions
2. Add appropriate error handling
3. Include logging and monitoring
4. Update documentation
5. Test thoroughly

## Security Notes
- Keep service account keys secure
- Review IAM permissions regularly
- Monitor service access logs
- Update dependencies frequently

## References
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Container Registry Documentation](https://cloud.google.com/container-registry/docs)
- [GPU Support Documentation](https://cloud.google.com/run/docs/using-gpus)