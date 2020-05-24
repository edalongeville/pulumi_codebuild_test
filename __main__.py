import pulumi
import json
import os
from pulumi_aws import s3, iam, codebuild

config = pulumi.Config("codebuild")
#Token requires permissions: admin:repo_hook, read:packages, repo, write:packages
access_token = os.environ['CODEBUILD_GITHUB_TOKEN']

example_bucket = s3.Bucket(
    resource_name="test-Codebuild-Bucket",
    acl="private"
)

example_role = iam.Role(
    resource_name="test_Codebuild_Role",
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
    resource_name="test_codebuild_policy",
    policy=jsonPolicy,
    role=example_role.name
)
# https://github.com/terraform-providers/terraform-provider-aws/issues/7435
source_credentials = codebuild.SourceCredential(
    resource_name="test_Github_Credentials",
    auth_type="PERSONAL_ACCESS_TOKEN",
    server_type="GITHUB",
    token=access_token)

project = codebuild.Project(
    resource_name="test_CodeBuild_Project",
    name="TestProject",
    artifacts={
        "type": "S3",
        "location": example_bucket.id,
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
        "report_build_status": True,
        "auths": [
            {
                "type": "OAUTH",
                "resource": source_credentials.arn,
            }
        ]
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

webhook = codebuild.Webhook(
    resource_name="test_Codebuild_Webhook",
    filter_groups=[{
        "filter": [
            {
                   "pattern": "PUSH",
                   "type": "EVENT",
                   },
            {
                "pattern": "master",
                "type": "HEAD_REF",
            },
        ],
    }],
    project_name=project.name)
