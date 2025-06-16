# The Ridges API

This repo contains the source code for Ridges (SN62) public API. It includes POST and GET methods, including 
- Methods for validators to upload records of problems solved to our database
- Endpoints for our (coming soon) public dashboard to query and display leaderboard rankings, problems solved, miner profiles, etc
- API methods for data analysis teams, miners, or whoever else is interested to query activity on the subnet and verify the quality of miners

If you have an endpoint you'd like to see implemented, reach out on the Bittensor discord. Our channel is Ridges - 62.

## To run this API locally
- `uv venv`
- `source .venv/bin/activate`
- `uv pip install -e .`
- `uvicorn src.main:app --reload`

## 🚀 Operating the Ridges API on EC2

This repository ships as a single Docker image stored in Amazon ECR.
Production runs on one t3.small EC2 instance named **ridges-api-prod**.  Any git
branch can be tested in isolation by launching another EC2 box and pointing it
at a differently-tagged image.

---

### 1  Update the existing prod instance to the latest code

```bash
# 0. build & push from your laptop or CI
BRANCH_TAG=latest   # always update the prod tag

docker buildx build --platform linux/amd64,linux/arm64 \
  -t 160684124315.dkr.ecr.us-east-1.amazonaws.com/ridges-api:$BRANCH_TAG \
  --push .

# 1. SSH into prod
ssh -i ~/.ssh/ridges-ssh.pem ubuntu@<PROD_PUBLIC_IP>

# 2. pull and restart
aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin 160684124315.dkr.ecr.us-east-1.amazonaws.com

docker pull 160684124315.dkr.ecr.us-east-1.amazonaws.com/ridges-api:latest
sudo systemctl restart ridges-api

# 3. verify
curl http://<PROD_PUBLIC_IP>/docs     # Swagger loads
```

---

### 2  Spin up a throw-away EC2 to test a branch

#### 2.1  Build & push the branch image

```bash
BRANCH_TAG=$(git rev-parse --abbrev-ref HEAD)   # e.g. im-experiment

docker buildx build --platform linux/amd64,linux/arm64 \
  -t 160684124315.dkr.ecr.us-east-1.amazonaws.com/ridges-api:$BRANCH_TAG \
  --push .
```

#### 2.2  Launch an EC2 (console)

| Setting          | Value |
|------------------|-------|
| AMI              | Amazon Linux 2023 (x86-64) *or* Ubuntu 24.04 |
| Instance type    | t3.small |
| Key pair         | `ridges-ssh` |
| Security group   | HTTP 80 from 0.0.0.0/0, SSH 22 from **My IP** |
| IAM role         | `ec2-ecr-readonly` |
| User-data (Ubuntu)| see snippet below |

Ubuntu user-data:
```bash
#!/bin/bash
apt-get update -y
apt-get install -y docker.io
systemctl enable --now docker
usermod -aG docker ubuntu
```

Wait for **2/2 status checks**; note the public IPv4 address.

#### 2.3  Run the container on the new box

```bash
ssh -i ~/.ssh/ridges-ssh.pem ubuntu@<NEW_IP>

aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin 160684124315.dkr.ecr.us-east-1.amazonaws.com

docker pull 160684124315.dkr.ecr.us-east-1.amazonaws.com/ridges-api:$BRANCH_TAG

cat > prod.env <<'EOF'
AWS_RDS_PLATFORM_ENDPOINT=platform.cqnsk0q6war0.us-east-1.rds.amazonaws.com
AWS_MASTER_USERNAME=ridges_master
AWS_MASTER_PASSWORD=<password>
AWS_RDS_PLATFORM_DB_NAME=platform_db
PYTHONUNBUFFERED=1
EOF

docker run --rm --env-file prod.env -p 80:8080 \
  160684124315.dkr.ecr.us-east-1.amazonaws.com/ridges-api:$BRANCH_TAG
```

Browse `http://<NEW_IP>/docs` to explore the test API.

#### 2.4  Promote or discard

* **Promote** → merge the branch, tag `latest`, update prod via section 1.
* **Discard** → terminate the EC2 instance to stop charges.

---

### Appendix A  Key & role cheat-sheet

* **SSH key**   `ridges-ssh.pem` ( `chmod 400` )
* **Instance role**  `ec2-ecr-readonly`
  * Policies: `AmazonEC2ContainerRegistryReadOnly` (+ optional `AmazonSSMReadOnlyAccess`)

---
