#!/usr/bin/env node

// This script launches all demo provider microservices as described in demo_providers.js
const { spawn } = require('child_process');
const path = require('path');

const PROVIDERS_PATH = path.join(__dirname, 'demo_providers.js');

const child = spawn('node', [PROVIDERS_PATH], {
  stdio: 'inherit',
  env: process.env,
});

child.on('close', (code) => {
  process.exit(code);
});
