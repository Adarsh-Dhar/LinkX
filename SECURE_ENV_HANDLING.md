# Production Secrets Management for Alpha Consumer Agent

## Recommendations

- **Never commit .env files or secrets to version control.**
- Use `.gitignore` to exclude all .env and secret files (already configured).
- For production, use a secret manager:
  - **AWS Secrets Manager**
  - **Azure Key Vault**
  - **HashiCorp Vault**
  - **Docker secrets** (for Docker Compose/Swarm)
- In Docker Compose, mount secrets as environment variables or files.
- Rotate keys regularly and restrict access to only necessary services.

## Example: Docker Compose Secret Mount

```
services:
  agent:
    ...
    secrets:
      - wallet_private_key
secrets:
  wallet_private_key:
    file: ./secrets/wallet_private_key.txt
```

## Example: Using AWS Secrets Manager
- Use the AWS SDK in your Python/Node.js code to fetch secrets at runtime.
- Never print or log secrets.

---
**Update your deployment pipeline to fetch and inject secrets securely for all production deployments.**
