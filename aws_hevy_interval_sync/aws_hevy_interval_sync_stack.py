from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_lambda_python_alpha as alambda_
)
from constructs import Construct


class AwsHevyIntervalSyncStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hevy_webhook_handler = alambda_.PythonFunction(
            self,
            "hevy_wh_lambda",
            entry="lambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            index="hevy_wh.py",
            handler="hevy_webhook_handler",
        )
        api = apigateway.LambdaRestApi(
            self,
            "hevy_wh_api",
            handler=hevy_webhook_handler,
            proxy=False,
        )

        hevy_wh_resource = api.root.add_resource("hevy_wh")
        hevy_wh_resource.add_method("POST", apigateway.LambdaIntegration(hevy_webhook_handler))
        CfnOutput(self, "HevyWebhookHandlerLambdaFname", value=hevy_webhook_handler.function_name, description="HevyWebhookHandler Lambda Function Name")
