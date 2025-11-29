import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_hevy_interval_sync.aws_hevy_interval_sync_stack import AwsHevyIntervalSyncStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_hevy_interval_sync/aws_hevy_interval_sync_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsHevyIntervalSyncStack(app, "aws-hevy-interval-sync")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
