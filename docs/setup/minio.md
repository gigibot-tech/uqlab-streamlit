# MinIO Local Storage Setup

This document describes how to use local MinIO as the default storage backend for uqlab-streamlit.

## Overview

MinIO is an S3-compatible object storage server that runs locally via Docker. It provides:
- **S3-compatible API**: Works with standard S3 clients
- **Local development**: No cloud dependencies
- **Web console**: Easy bucket management at http://localhost:9001
- **Persistent storage**: Data survives container restarts
- **Graceful fallback**: Automatically falls back to filesystem if MinIO is unavailable

## Quick Start

### Option 1: Using the Startup Script (Recommended)

The easiest way to start both MinIO and the backend:

```bash
cd uqlab-streamlit
./start-with-minio.sh
```

This script will:
1. Start MinIO via docker-compose
2. Wait for MinIO to be healthy
3. Initialize the default bucket (`uqlab-artifacts`)
4. Start the uvicorn backend with `--reload`
5. Display connection information

### Option 2: Manual Start

Start MinIO separately, then run uvicorn:

```bash
# Start MinIO
cd uqlab-streamlit
docker-compose up -d minio

# Wait for MinIO to be ready (check health)
docker-compose ps minio

# Initialize bucket (first time only)
docker-compose up minio-init

# Start backend
cd backend
uvicorn app.main:app --reload
```

## MinIO Access

Once MinIO is running, you can access:

- **API Endpoint**: http://localhost:9000
- **Web Console**: http://localhost:9001
- **Username**: `minioadmin`
- **Password**: `minioadmin`
- **Default Bucket**: `uqlab-artifacts`

### Web Console Features

Visit http://localhost:9001 to:
- Browse uploaded files
- Create/delete buckets
- Manage access policies
- Monitor storage usage
- View access logs

## Configuration

### Default Configuration

The backend is pre-configured to use local MinIO with these defaults (in `backend/app/core/config.py`):

```python
STORAGE_BACKEND = "s3"  # Default to S3 (local MinIO)
STORAGE_S3_ENDPOINT_URL = "http://localhost:9000"
STORAGE_S3_BUCKET = "uqlab-artifacts"
STORAGE_S3_ACCESS_KEY_ID = "minioadmin"
STORAGE_S3_SECRET_ACCESS_KEY = "minioadmin"
STORAGE_S3_REGION = "us-east-1"
STORAGE_S3_SECURE = False  # HTTP for local development
```

### Override Configuration

You can override these settings via environment variables or `.env` file:

```bash
# Use a different bucket
export STORAGE_S3_BUCKET=my-custom-bucket

# Use remote S3 instead of local MinIO
export STORAGE_S3_ENDPOINT_URL=https://s3.amazonaws.com
export STORAGE_S3_ACCESS_KEY_ID=your-aws-key
export STORAGE_S3_SECRET_ACCESS_KEY=your-aws-secret
export STORAGE_S3_SECURE=true
```

### Fall Back to Filesystem

To temporarily use filesystem storage instead of S3:

```bash
export STORAGE_BACKEND=filesystem
uvicorn app.main:app --reload
```

Or create a `.env` file in the project root:

```env
STORAGE_BACKEND=filesystem
```

## Docker Compose Configuration

The `docker-compose.yml` defines two services:

### 1. MinIO Service

```yaml
minio:
  image: minio/minio:latest
  ports:
    - "9000:9000"  # API
    - "9001:9001"  # Console
  volumes:
    - minio_data:/data  # Persistent storage
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
```

### 2. MinIO Init Service

Automatically creates the default bucket on first run:

```yaml
minio-init:
  image: minio/mc:latest
  depends_on:
    minio:
      condition: service_healthy
  # Creates uqlab-artifacts bucket
```

## Verifying Storage Backend

When you start the backend, check the logs for:

```
INFO:     Storage backend: s3 (local MinIO at http://localhost:9000)
```

If MinIO is unavailable, you'll see:

```
WARNING:  S3 storage configured but unavailable. Falling back to filesystem.
INFO:     Storage backend: filesystem
```

## Managing MinIO

### Start MinIO

```bash
docker-compose up -d minio
```

### Stop MinIO

```bash
docker-compose stop minio
```

### View Logs

```bash
docker-compose logs -f minio
```

### Restart MinIO

```bash
docker-compose restart minio
```

### Remove MinIO (keeps data)

```bash
docker-compose down
```

### Remove MinIO and Data

```bash
docker-compose down -v  # WARNING: Deletes all stored data
```

## Troubleshooting

### MinIO Won't Start

**Check if port is already in use:**
```bash
lsof -i :9000
lsof -i :9001
```

**View detailed logs:**
```bash
docker-compose logs minio
```

### Backend Can't Connect to MinIO

**Verify MinIO is healthy:**
```bash
docker-compose ps minio
# Should show "healthy" status
```

**Test MinIO API:**
```bash
curl http://localhost:9000/minio/health/live
# Should return: OK
```

**Check backend logs:**
```bash
# Look for S3 connection errors
```

### Bucket Not Found

**Manually create bucket:**
```bash
docker-compose up minio-init
```

Or via web console at http://localhost:9001

### Permission Denied

**Check MinIO credentials:**
- Default username: `minioadmin`
- Default password: `minioadmin`

**Verify environment variables:**
```bash
echo $STORAGE_S3_ACCESS_KEY_ID
echo $STORAGE_S3_SECRET_ACCESS_KEY
```

## Development Workflow

### Typical Development Session

1. **Start MinIO** (once per session):
   ```bash
   docker-compose up -d minio
   ```

2. **Start backend** (with auto-reload):
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **Make changes** - uvicorn will auto-reload

4. **Stop when done**:
   ```bash
   # Stop backend: Ctrl+C
   # Stop MinIO: docker-compose stop minio
   ```

### Using the Convenience Script

For a streamlined workflow:

```bash
# Start everything
./start-with-minio.sh

# Make changes - uvicorn auto-reloads

# Stop everything: Ctrl+C
```

## Production Considerations

For production deployments:

1. **Use strong credentials**: Change from default `minioadmin/minioadmin`
2. **Enable HTTPS**: Set `STORAGE_S3_SECURE=true` and configure TLS
3. **Use remote S3**: Consider AWS S3, MinIO cluster, or other S3-compatible storage
4. **Backup strategy**: Implement regular backups of MinIO data volume
5. **Access control**: Configure bucket policies and IAM

## Architecture

```
┌─────────────────┐
│  FastAPI Backend│
│  (uvicorn)      │
└────────┬────────┘
         │
         │ S3 API (aioboto3)
         │
         ▼
┌─────────────────┐
│  MinIO Server   │
│  localhost:9000 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Docker Volume  │
│  (persistent)   │
└─────────────────┘
```

## Dependencies

The following Python packages are required (now included by default):

- `aioboto3>=13.1.1` - Async S3 client
- `aiobotocore>=2.13.1` - Async AWS SDK core
- `aiofiles>=24.1.0` - Async file operations

These are automatically installed with the backend dependencies.

## Additional Resources

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [MinIO Docker Hub](https://hub.docker.com/r/minio/minio)
- [S3 API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)
- [aioboto3 Documentation](https://aioboto3.readthedocs.io/)

## Support

For issues or questions:
1. Check MinIO logs: `docker-compose logs minio`
2. Check backend logs for S3 connection errors
3. Verify MinIO health: `curl http://localhost:9000/minio/health/live`
4. Try filesystem fallback: `export STORAGE_BACKEND=filesystem`