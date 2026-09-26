# AWS (phase 2)

Terraform modules for the AWS deployment at milestone M5. Nothing is written yet. The mapping from local components to AWS services is in [docs/TECH_STACK.md](../../../docs/TECH_STACK.md), section 10.

**Owner:** Lane A.

## Start with the low-cost test deployment

For M5 and M6, one EC2 GPU instance running the same `compose.yaml` with the `gpu` profile is enough, and it keeps cost to the hours the instance runs. Details and prices are in [docs/TECH_STACK.md](../../../docs/TECH_STACK.md), section 11. The modules below are the full design, if the Institution wants it after testing.

## Modules to write

- `network`: VPC, private subnets, security groups. The code sandbox gets a subnet with no egress.
- `data`: S3 buckets (`raw`, `uploads`, `external`, `exports`, `mlflow`) with KMS encryption, RDS PostgreSQL with pgvector. Postgres is the only database, there is no catalog or query service to add.
- `compute`: one ECR repository for the app image, an ECS service for the api container, the code sandbox as an ECS task with no egress, one EC2 GPU host for vLLM and TEI.
- `edge`: ALB with ACM certificates in front of the public routes of the api service, Cognito for identity.
- `ops`: CloudWatch or Amazon Managed Prometheus and Grafana, SES for expert email, KMS keys for pseudonyms and text encryption, Secrets Manager.

## Rules

- State in an S3 backend. Never commit state files or `.tfvars` with secrets.
- One workspace per environment.
- GPU instances are not free-tier eligible. Agree on cost with the Institution before `apply`.
