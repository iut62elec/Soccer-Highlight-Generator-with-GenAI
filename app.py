#!/usr/bin/env python3

import os
from aws_cdk import core
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
import os
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
import json
from aws_cdk import aws_s3_deployment as s3deploy
import tempfile


class SoccerHighlightsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Read the config file
        with open("config.json") as config_file:
            config = json.load(config_file)

        # Create an SNS topic
    
        self.highlight_link_topic = sns.Topic(
        self, "SoccerHighlightLink",
        topic_name="soccer_highlight_link"
)

        # Subscribe the user email to the topic
        user_email = config.get("user_email")
        if user_email:
            self.highlight_link_topic.add_subscription(subscriptions.EmailSubscription(user_email))

        
        # Create an S3 bucket
        self.video_assets_bucket = s3.Bucket(self, "VideoAssetsBucket") # Be careful with this in production
       
        oai = cloudfront.OriginAccessIdentity(self, "OAI")

        # Update S3 bucket policy to be accessible from CloudFront OAI
        self.video_assets_bucket.grant_read(oai)

        # Create a CloudFront web distribution
        self.video_assets_distribution = cloudfront.CloudFrontWebDistribution(self, "VideoAssetsDistribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=self.video_assets_bucket,
                        origin_access_identity=oai
                    ),
                    behaviors=[cloudfront.Behavior(
                        is_default_behavior=True,
                        # Default behavior settings can be adjusted here
                    )]
                ),
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=self.video_assets_bucket,
                        origin_access_identity=oai
                    ),
                    behaviors=[cloudfront.Behavior(
                        path_pattern="/public/HighlightClips/*",
                        # Settings specific to this path can be adjusted here
                    )]
                ),
                # Additional path as needed
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=self.video_assets_bucket,
                        origin_access_identity=oai
                    ),
                    behaviors=[cloudfront.Behavior(
                        path_pattern="/public/*",
                        # Settings specific to this path can be adjusted here
                    )]
                )
            ]
        )
                
        self.mediaconvert_role = iam.Role(self, 'MediaConvertRole',
                                     assumed_by=iam.ServicePrincipal('mediaconvert.amazonaws.com'),
                                     managed_policies=[
                                         iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                                         iam.ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                                         iam.ManagedPolicy.from_aws_managed_policy_name('AWSElementalMediaConvertFullAccess')
                                     ],
                                     role_name='mediaconvert_role')

        # Add trust relationship
        self.mediaconvert_role.assume_role_policy.add_statements(iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            principals=[iam.ServicePrincipal("mediaconvert.amazonaws.com")]
        ))
        # IAM Role for Lambda Functions
        lambda_role = self.create_lambda_execution_role()
        full_access_policy = iam.ManagedPolicy(
            self, 'LambdaFullAccessPolicy',
            statements=[
                iam.PolicyStatement(
                    actions=["s3:*"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["dynamodb:*"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath","ssm:PutParameter"], # Full access may not be advisable depending on your use case
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["sqs:*"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["logs:*", "cloudwatch:*"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                # Assuming 'bedrock:*' is a placeholder for actual actions for a service named 'Bedrock'
                iam.PolicyStatement(
                    actions=["bedrock:*"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                        actions=["lambda:*"],
                        resources=["*"],
                        effect=iam.Effect.ALLOW
                    ),
                # Additional permission for CreateEventSourceMapping
                iam.PolicyStatement(
                    actions=["lambda:CreateEventSourceMapping"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=[
                        "lambda:InvokeFunction",
                        "lambda:CreateEventSourceMapping",  # Add this line to include the required permission
                        # Add other lambda related permissions as needed
                    ],
                    resources=["*"]  # Adjust this as necessary for your use case
                ),
                iam.PolicyStatement(
                        actions=[
                            "mediaconvert:*",
                        ],
                        resources=["*"],
                        effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=['iam:PassRole'],
                    resources=['*'],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    actions=["sns:Publish"],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                )
            ]
        )

        # Attach the policy to the lambda_role
        lambda_role.add_managed_policy(full_access_policy)
        #lambda_role.add_to_policy()
        # IAM Role for Step Functions
        step_functions_role = self.create_step_functions_role()
        step_functions_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "lambda:InvokeFunction",
                "states:StartExecution",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=["*"]
        ))
        # Define the Lambda functions
        self.lambda_functions = self.create_lambda_functions(lambda_role)

        # Define State Machine
        self.state_machine = self.define_state_machine(step_functions_role)

    def create_lambda_execution_role(self):
        lambda_role = iam.Role(
            self, 'LambdaExecutionRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        # Add policies to lambda_role as necessary...
        return lambda_role


    def create_step_functions_role(self):
        step_functions_role = iam.Role(
            self, 'StepFunctionsExecutionRole',
            assumed_by=iam.ServicePrincipal('states.amazonaws.com')
        )
        # Add policies to step_functions_role as necessary...
        return step_functions_role

    def create_lambda_functions(self, role):
        functions = {}
        function_names = [
        'receive_message',  # 
        'create_assets',
        'create_thumbnails',
        'check_sqs',
        'create_short_clips',
        'create_large_clips',
        'merge_clips',
        'mediaconvert_check',
        'stepfunction_status',  
        'send_email',
        'delete_s3_sqs_ddb',
    ]
        
        for name in function_names:
        # Check if the function is either 'receive_message' or 'create_assets'
            if name in ['receive_message']:
                timeout = core.Duration.minutes(15)  # Set timeout to 15 minutes
                memory_size = 10240  # Set memory size to 10240 MB
            else:
                # For all other functions, use default values (or any other values you prefer)
                timeout = core.Duration.minutes(15)  # Default timeout
                memory_size = 512  # Default memory size
                
            if name == 'receive_message': 
                functions[name] = lambda_.Function(
                    self, f'{name}Lambda',
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    handler='index.lambda_handler',
                    code=lambda_.Code.from_asset(f'lambda/{name}'),
                    role=role,
                    timeout=timeout,  # Apply custom or default timeout
                    memory_size=memory_size,  # Apply custom or default memory size
                )   
                receive_message_lambda_arn = functions[name].function_arn
            elif name == 'create_assets':
                 functions[name] = lambda_.Function(
                    self, f'{name}Lambda',
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    handler='index.lambda_handler',
                    code=lambda_.Code.from_asset(f'lambda/{name}'),
                    role=role,
                    timeout=timeout,  # Apply custom or default timeout
                    memory_size=memory_size,  # Apply custom or default memory size
                    environment={
                    'RECEIVE_MESSAGE_LAMBDA_ARN': receive_message_lambda_arn,
                    'VIDEO_ASSETS_BUCKET_NAME': self.video_assets_bucket.bucket_name
                }
                )
            elif name == 'send_email':
                 functions[name] = lambda_.Function(
                    self, f'{name}Lambda',
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    handler='index.lambda_handler',
                    code=lambda_.Code.from_asset(f'lambda/{name}'),
                    role=role,
                    timeout=timeout,  # Apply custom or default timeout
                    memory_size=memory_size,  # Apply custom or default memory size
                    environment={
                    'CLOUDFRONT_ENDPOINT_URL': self.video_assets_distribution.distribution_domain_name,
                    'VIDEO_ASSETS_BUCKET_NAME': self.video_assets_bucket.bucket_name,
                    'TOPIC_ARN': self.highlight_link_topic.topic_arn,
                    #'MEDIA_CONVERT_ROLE_ARN': self.mediaconvert_role.role_arn 
                }
                )    
            else:     
                functions[name] = lambda_.Function(
                    self, f'{name}Lambda',
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    handler='index.lambda_handler',
                    code=lambda_.Code.from_asset(f'lambda/{name}'),
                    role=role,
                    timeout=timeout,  # Apply custom or default timeout
                    memory_size=memory_size,  # Apply custom or default memory size
                    environment={
                    'MEDIA_CONVERT_ROLE_ARN': self.mediaconvert_role.role_arn}

            )

        return functions

    def define_state_machine(self, role):
     
        create_assets_task = tasks.LambdaInvoke(
            self, 'create assets',
            lambda_function=self.lambda_functions['create_assets'],
             payload=sfn.TaskInput.from_object({
                    "Executionid.$": "$$.Execution.Id",
                    "entireInput.$": "$"
                }),
            retry_on_service_exceptions=True,
            output_path="$.Payload"
        )
        create_thumbnails_task = tasks.LambdaInvoke(
            self, 'Create Thumbnails',
            lambda_function=self.lambda_functions['create_thumbnails'],
            result_path="$.guid",
         retry_on_service_exceptions=True,
        )

        check_sqs_empty_task = tasks.LambdaInvoke(
            self, 'sqs empty?',
            lambda_function=self.lambda_functions['check_sqs'],
            result_path="$.status1",
             retry_on_service_exceptions=True,
        )

        create_short_clips_task = tasks.LambdaInvoke(
            self, 'Start clipping jobs',
            lambda_function=self.lambda_functions['create_short_clips'],
            result_path="$.guid1",
             retry_on_service_exceptions=True,
        )

        Thumbnails_Status_task = tasks.LambdaInvoke(
            self, 'Thumbnails Status?',
            lambda_function=self.lambda_functions['mediaconvert_check'],
            result_path="$.status",
            retry_on_service_exceptions=True,
        )
        ShortClips_status_task = tasks.LambdaInvoke(
            self, 'ShortClips status',
            lambda_function=self.lambda_functions['mediaconvert_check'],
            result_path="$.status2",
             retry_on_service_exceptions=True,
        )
        final_clips_status_task = tasks.LambdaInvoke(
            self, 'final clips status',
            lambda_function=self.lambda_functions['mediaconvert_check'],
            result_path="$.status3",
             retry_on_service_exceptions=True,
        )
        merge_clips_status_task = tasks.LambdaInvoke(
            self, 'merge clips status',
            lambda_function=self.lambda_functions['mediaconvert_check'],
            result_path="$.status4",
             retry_on_service_exceptions=True,
        )
        
        
        create_large_clips_task = tasks.LambdaInvoke(
            self, 'Final long clips',
            lambda_function=self.lambda_functions['create_large_clips'],
            result_path="$.guid2",
             retry_on_service_exceptions=True,
        )
        merge_clips_task = tasks.LambdaInvoke(
            self, 'Merge long clips',
            lambda_function=self.lambda_functions['merge_clips'],
            result_path="$.guid3",
             retry_on_service_exceptions=True,
        )
        write_status_task = tasks.LambdaInvoke(
            self, 'write status',
            lambda_function=self.lambda_functions['stepfunction_status'],
            result_path="$.status_write",
            retry_on_service_exceptions=True,
        )
        
        send_email_task = tasks.LambdaInvoke(
            self, 'Get Highlight Link',
            lambda_function=self.lambda_functions['send_email'],
            result_path="$.outputs",
            retry_on_service_exceptions=True,
        )
        def add_custom_retry_policy(task):
            task.add_retry(
                errors=["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
                interval=core.Duration.seconds(10),
                max_attempts=300,
                backoff_rate=2
            )
        # Apply the retry policy
        add_custom_retry_policy(Thumbnails_Status_task)
        add_custom_retry_policy(check_sqs_empty_task)
        add_custom_retry_policy(ShortClips_status_task)
        add_custom_retry_policy(final_clips_status_task)
        add_custom_retry_policy(merge_clips_status_task)
        # Waits
        wait_for_thumbnail = sfn.Wait(
            self, 'Wait for Thumbnail',
            time=sfn.WaitTime.duration(core.Duration.seconds(10))
        )
        
        wait_for_classification = sfn.Wait(
            self, 'Wait for classification',
            time=sfn.WaitTime.duration(core.Duration.seconds(10))
        )
        
        wait_for_short_clip = sfn.Wait(
            self, 'Wait short clip',
            time=sfn.WaitTime.duration(core.Duration.seconds(10))
        )
        
        wait_for_long_clips = sfn.Wait(
            self, 'Wait for long clips',
            time=sfn.WaitTime.duration(core.Duration.seconds(10))
        )

        wait_for_merge_long = sfn.Wait(
            self, 'Wait for merge long',
            time=sfn.WaitTime.duration(core.Duration.seconds(10))
        )
        
        
            # Define the success state

        success_state = sfn.Succeed(self, "Success")

        # Define fail state
        failed_state = sfn.Fail(self, "Failed")

        # Define Choice states, these should direct the flow within the choice itself
        thumbnails_finish_choice = sfn.Choice(self, "Thumbnails Finish?")\
            .when(sfn.Condition.string_equals("$.status.Payload", "COMPLETE"), wait_for_classification)\
            .when(sfn.Condition.string_equals("$.status.Payload", "ERROR"), failed_state)\
            .otherwise(wait_for_thumbnail)

        all_classified_choice = sfn.Choice(self, "all classified?")\
            .when(sfn.Condition.string_equals("$.status1.Payload", "COMPLETE"), create_short_clips_task)\
            .when(sfn.Condition.string_equals("$.status1.Payload", "ERROR"), failed_state)\
            .otherwise(wait_for_classification)

        wait_for_classification.next(check_sqs_empty_task)
        check_sqs_empty_task.next(all_classified_choice)
        
        
        
        create_short_clips_task.next(wait_for_short_clip)
        wait_for_short_clip.next(ShortClips_status_task)
        
        short_clips_finish_choice = sfn.Choice(self, "short clips Finish?")\
            .when(sfn.Condition.string_equals("$.status2.Payload", "COMPLETE"),create_large_clips_task )\
            .when(sfn.Condition.string_equals("$.status2.Payload", "ERROR"), failed_state)\
            .otherwise(wait_for_short_clip)

        ShortClips_status_task.next(short_clips_finish_choice)

        create_large_clips_task.next(wait_for_long_clips)
        wait_for_long_clips.next(final_clips_status_task)
        

        final_clips_finish_choice = sfn.Choice(self, "final clips Finish?")\
            .when(sfn.Condition.string_equals("$.status3.Payload", "COMPLETE"), merge_clips_task)\
            .when(sfn.Condition.string_equals("$.status3.Payload", "ERROR"), failed_state)\
            .otherwise(wait_for_long_clips)
        final_clips_status_task.next(final_clips_finish_choice)
        merge_clips_task.next(wait_for_merge_long)
        wait_for_merge_long.next(merge_clips_status_task)
        
        
        final_merge_finish_choice = sfn.Choice(self, "final merge finish")\
            .when(sfn.Condition.string_equals("$.status4.Payload", "COMPLETE"), send_email_task)\
            .when(sfn.Condition.string_equals("$.status4.Payload", "ERROR"), failed_state)\
            .otherwise(wait_for_merge_long)

        merge_clips_status_task.next(final_merge_finish_choice)
        send_email_task.next(write_status_task)
        write_status_task.next(success_state)
     
        
        # Define the complete state machine definition
        definition = create_assets_task\
            .next(create_thumbnails_task)\
            .next(wait_for_thumbnail)\
            .next(Thumbnails_Status_task)\
            .next(thumbnails_finish_choice)\
          
        state_machine = sfn.StateMachine(
            self, 'SoccerHighlightsStateMachine',
            definition=definition,
            timeout=core.Duration.hours(5),
            role=role
        )

        return state_machine



app = core.App()
SoccerHighlightsStack(app, "SoccerHighlightsStack")

app.synth()
