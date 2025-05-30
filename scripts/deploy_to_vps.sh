#!/bin/bash
set -e
ssh $DEPLOY_SSH <<'EOSSH'
  cd ~/Meme-Maker
  git pull
  docker compose build
  docker compose up -d
  sudo systemctl restart caddy
EOSSH 