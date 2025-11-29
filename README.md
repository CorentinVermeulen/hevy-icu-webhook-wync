# aws-hevy-interval-webhook-sync
Synchronize your **Hevy** workouts to **Intervals.icu** automatically.

This project provides:
- A local **backfill** utility to sync your previous **Hevy** workouts to **Intervals.icu**.
- An AWS **Lambda** + API Gateway endpoint to receive **Hevy webhooks** and seamlessly sync future workouts to **Intervals.icu**.

Works on the AWS Free Tier.

---

## Setup Notes
1. You need to have a **PRO Hevy account**, otherwise you won't be able to access **developer features** (**`api_key`** and **`webhook`**).
2. To set up the synchronization of all future workouts posted on **Hevy** to **Intervals.icu**, you will also need to have an AWS **Free Tier** account.

### Environment variables

1. On **Intervals.icu**, you will need to get your **athlete ID** and **API key** (Settings > Developer Settings).
2. On **Hevy**, you will need to get your **API key** (Settings > **Developer**).
3. On **Hevy**, paste the **Hevy API key** as the **webhook authorization header** as well.

```bash
cp .env.example .env
```

Then edit the .env file with your keys.

## Synchronize all your previous activities from Hevy to Intervals.icu (Locally)
A small runner script is provided at the project root: local_sync_all.py. It will read your environment variables (and .env if present) and backfill workouts to Intervals.icu.

1) Create and activate the virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate # use '.\.venv\Scripts\activate' for Windows PowerShell
pip install -r requirements.txt
```

2) Check `.env` file is present and contains your keys. Example:
```
HEVY_API_KEY=hevy_api_key_here
ICU_ATHLETE_ID=123456
ICU_API_KEY=intervals_api_key_here
```

3. Run the script with the following parameters to test if it works (it will only sync 1 activity):
```
# Test to sync only 1 activity
python local_sync_all.py --max-page 1 --page-size 1
```
4) If everything is OK and you saw the activity on Intervals.icu, you can run the script with the following parameters to sync all your previous activities from Hevy to Intervals.icu. It can take some time.

```
# Sync all past activities
python local_sync_all.py
```

## Set up the webhook with an AWS Lambda + API Gateway endpoint
### General Information
The CDK stack (`aws_hevy_interval_sync/aws_hevy_interval_sync_stack.py`) deploys:
- A Python Lambda function.
- An API Gateway REST API with POST /hevy_wh to trigger the Lambda.

### Prerequisites
- Node.js 18+ and AWS CDK v2 (installed globally: npm i -g aws-cdk)
- An AWS account with credentials configured (e.g., via aws configure) You can follow the tutorial documentation link Or follow this tutorial on YouTube link (recommended)

1) Bootstrap CDK (first time per account/region):
```
cdk bootstrap aws://ACCOUNT_NUMBER/REGION
```

2) Synth the stack:
```
cdk synth
```

3) Deploy the stack:
```
cdk deploy
```
4) Set Lambda environment variables:
After deployment, locate the Lambda function named in the stack output `HevyWebhookHandlerLambdaFname` (or in the AWS Console under Lambda).

Set the following environment variables on that function:
- HEVY_API_KEY
- ICU_ATHLETE_ID
- ICU_API_KEY

You can do this in the AWS Console (`Lambda > Configuration > Environment variables`) or via the AWS CLI:
```
aws lambda update-function-configuration \
  --function-name <YourLambdaName> \
  --environment "Variables={HEVY_API_KEY=...,ICU_ATHLETE_ID=...,ICU_API_KEY=}"
```

5) Find your webhook URL:
Locate the API Gateway endpoint in the stack output with a `POST /hevy_wh` resource. You can find the exact URL in API Gateway (Stages > prod), or by running cdk synth and inspecting outputs, or via the AWS Console.

6) Configure Hevy webhook:
- Set the webhook URL to the API Gateway endpoint above. (add the webhook URL + /hevy_wh in Hevy Developer Settings).
- Set the Authorization header to your HEVY_API_KEY.

---
Done