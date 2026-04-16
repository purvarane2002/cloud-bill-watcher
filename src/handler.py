import boto3
import os
from datetime import date, timedelta

def get_cost(client, start, end):
    response = client.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
    return round(float(amount), 2)

def lambda_handler(event, context):
    ce_client = boto3.client('ce', region_name='us-east-1')
    sns_client = boto3.client('sns', region_name='eu-west-2')

    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    two_days_ago = str(date.today() - timedelta(days=2))

    cost_today = get_cost(ce_client, yesterday, today)
    cost_yesterday = get_cost(ce_client, two_days_ago, yesterday)

    print(f"Yesterday: ${cost_yesterday} | Today: ${cost_today}")

    if cost_yesterday == 0:
        change_pct = 0
    else:
        change_pct = ((cost_today - cost_yesterday) / cost_yesterday) * 100

    if change_pct > 20:
        subject = "⚠️ AWS Cost Alert — Spike Detected"
        message = (
            f"Hello Purva,\n\n"
            f"Your AWS costs have increased significantly today.\n\n"
            f"Yesterday's spend:  ${cost_yesterday}\n"
            f"Today's spend:      ${cost_today}\n"
            f"Change:             +{round(change_pct, 1)}%\n\n"
            f"Action needed: Log in to AWS Cost Explorer to investigate which service caused the spike.\n\n"
            f"— Cloud Bill Watcher"
        )
        status = "alert_sent"
    else:
        subject = "✅ AWS Daily Cost Report — All Good"
        message = (
            f"Hello Purva,\n\n"
            f"Your AWS costs are normal today. No action needed.\n\n"
            f"Yesterday's spend:  ${cost_yesterday}\n"
            f"Today's spend:      ${cost_today}\n"
            f"Change:             {round(change_pct, 1)}%\n\n"
            f"Everything looks stable. Have a great day!\n\n"
            f"— Cloud Bill Watcher"
        )
        status = "ok"

    sns_client.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject=subject,
        Message=message
    )

    return {"status": status, "cost_today": cost_today, "change_pct": round(change_pct, 1)}