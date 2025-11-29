# aws-hevy-interval-webhook-sync
(*README AI GENERATED*)

Synchronize your Hevy workouts to Intervals.icu automatically.

This project provides:
- An AWS Lambda + API Gateway endpoint to receive Hevy webhooks and seamlessly sync future workouts to Intervals.icu.
- A local backfill utility to sync your previous Hevy workouts to Intervals.icu.

Works on the AWS Free Tier.

## General information

- Incoming webhooks from Hevy are authenticated using the `Authorization` header. Set it to your Hevy API key.
- The Lambda validates the header, fetches the workout from Hevy, and posts an activity to Intervals.icu.
- The local backfill utility can page through your Hevy history and upload activities to Intervals.icu.

Core code lives under `lambda/`:
- `lambda/hevy_wh.py` — webhook handler that processes a single workout (`POST /hevy_wh`).
- `lambda/utils.py` — API clients and helpers, including `local_sync_all()` to backfill workouts.

The CDK stack (`aws_hevy_interval_sync/aws_hevy_interval_sync_stack.py`) deploys:
- A Python Lambda function.
- An API Gateway REST API with `POST /hevy_wh` to trigger the Lambda.

## Prerequisites

- Python 3.11+
- Node.js 18+ and AWS CDK v2 (installed globally: `npm i -g aws-cdk`)
- An AWS account with credentials configured (e.g., via `aws configure`)

## Environment variables

Create a `.env` file (use `.env.example` as a template) with the following keys:

- `HEVY_API_KEY` — Your Hevy API key. Also used as the webhook `Authorization` secret.
- `ICU_ATHLETE_ID` — Your Intervals.icu athlete ID (a number).
- `ICU_API_KEY` — Your Intervals.icu API key.

Example:

```
HEVY_API_KEY=hevy_api_key_here
ICU_ATHLETE_ID=123456
ICU_API_KEY=intervals_api_key_here
```

These variables are used both locally and must be configured on the deployed Lambda (see below).

## Setup (local)

```
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then edit .env with your keys
```

## Run a local backfill (sync previous workouts)

A small runner script is provided at the project root: `local_sync_all.py`. It will read your environment variables (and `.env` if present) and backfill workouts to Intervals.icu.

Usage examples:

```
# Sync the first page only (default page_size=10)
python local_sync_all.py

# Sync up to 5 pages, with a page size of 10
python local_sync_all.py --max-page 5 --page-size 10
```

Notes:
- Hevy’s API limits page size to 10.
- The script prints progress as activities are posted.

## Deploy the webhook to AWS (Free Tier)

1) Bootstrap CDK (first time per account/region):

```
cdk bootstrap
```

2) Deploy the stack:

```
cdk deploy
```

3) Set Lambda environment variables:

After deployment, locate the Lambda function named in the stack output `HevyWebhookHandlerLambdaFname` (or in the AWS Console under Lambda).

Set the following environment variables on that function:
- `HEVY_API_KEY`
- `ICU_ATHLETE_ID`
- `ICU_API_KEY`

You can do this in the AWS Console (Lambda > Configuration > Environment variables) or via the AWS CLI:

```
aws lambda update-function-configuration \
  --function-name <YourLambdaName> \
  --environment "Variables={HEVY_API_KEY=...,ICU_ATHLETE_ID=...,ICU_API_KEY=}"
```

4) Find your webhook URL:

The stack creates an API Gateway with a `POST /hevy_wh` resource. The invoke URL typically looks like:

```
https://<api-id>.execute-api.<region>.amazonaws.com/prod/hevy_wh
```

You can find the exact URL in API Gateway (Stages > prod), or by running `cdk synth` and inspecting outputs, or via the AWS Console.

5) Configure Hevy webhook:

- Set the webhook URL to the API Gateway endpoint above.
- Set the `Authorization` header to your `HEVY_API_KEY`.

6) Test the webhook manually (optional):

```
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: $HEVY_API_KEY" \
  -d '{
        "id": "test-event-id",
        "payload": { "workoutId": "<hevy-workout-id>" }
      }' \
  https://<api-id>.execute-api.<region>.amazonaws.com/prod/hevy_wh
```

Expected response: `200` if authorized and the workout exists; otherwise `401` (unauthorized) or `400` (missing `workoutId`).

## Useful CDK commands

- `cdk ls` — list all stacks in the app
- `cdk synth` — synthesize a CloudFormation template
- `cdk deploy` — deploy the stack
- `cdk diff` — compare deployed stack with current state
