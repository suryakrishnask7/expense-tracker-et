#!/bin/sh
set -e

# Prepare SSH private key
mkdir -p ~/.ssh
printf "%s\n" "$DEPLOY_SSH_KEY" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

TARGET_PORT="${DEPLOY_PORT:-22}"
ssh-keyscan -p "$TARGET_PORT" -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts 2>/dev/null || true

echo "Initiating deployment to $DEPLOY_HOST on port $TARGET_PORT..."
ssh -i ~/.ssh/id_rsa -p "$TARGET_PORT" -o StrictHostKeyChecking=no "$DEPLOY_USER@$DEPLOY_HOST" "mkdir -p /tmp/expense-tracker-src"

rsync -avz -e "ssh -i ~/.ssh/id_rsa -p $TARGET_PORT -o StrictHostKeyChecking=no" \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='instance/*.db' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='.coverage' \
  ./ "$DEPLOY_USER@$DEPLOY_HOST:/tmp/expense-tracker-src/"

ssh -i ~/.ssh/id_rsa -p "$TARGET_PORT" -o StrictHostKeyChecking=no "$DEPLOY_USER@$DEPLOY_HOST" \
  "DEPLOY_SOURCE_DIR=/tmp/expense-tracker-src bash /tmp/expense-tracker-src/deploy/deploy.sh"
