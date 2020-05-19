import pulumi
import json
from pulumi_aws import s3, iam, codebuild

example_bucket = s3.Bucket("exampleBucket", acl="private")

example_role = iam.Role(
    resource_name="exampleRole",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["codebuild.amazonaws.com"]
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    )
)

jsonPolicy = example_bucket.arn.apply(
    lambda arn: json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Resource": [
                        "*"
                    ],
                    "Action": [
                        "*",
                    ]
                },
            ]
        }
    )
)

codebuild_policy = iam.RolePolicy(
    "codebuild_policy",
    policy=jsonPolicy,
    role=example_role.name
)

project = codebuild.Project(
    resource_name="CodeBuild_Project",
    name="TestProject",
    artifacts={
        "type": "NO_ARTIFACTS",
    },
    environment={
        "computeType": "BUILD_GENERAL1_SMALL",
        "environmentVariable": [
            {
                "name": "SOME_KEY1",
                "value": "SOME_VALUE1",
            },
        ],
        "image": "aws/codebuild/standard:1.0",
        "imagePullCredentialsType": "CODEBUILD",
        "type": "LINUX_CONTAINER",
    },
    service_role=example_role.arn,
    source={
        "gitCloneDepth": 1,
        "gitSubmodulesConfig": {
            "fetchSubmodules": True,
        },
        "location": "https://github.com/edalongeville/codebuild_test.git",
        "type": "GITHUB",
    },
    logs_config={
        "cloudwatchLogs": {
            "groupName": "cloudwatch",
            "streamName": "cloudwatch-example-build",
        },
        "s3Logs": {
            "location": example_bucket.id.apply(lambda id: f"{id}/build-log"),
            "status": "ENABLED",
        },
    },
)
