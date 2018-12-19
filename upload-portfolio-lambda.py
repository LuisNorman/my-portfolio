import json
import boto3
from io import BytesIO
import zipfile
import mimetypes

def lambda_handler(event, context):

    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:272734013131:deployPortfolioTopic')

    location = {
        "bucketName": "portfoliobuild.luis-norman.com",
        "objectKey": "portfoliobuild.zip"
    }

    try:
        job = event.get("CodePipeline.job")
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "BuildArtif":
                    location = artifact["location"]["s3Location"]
        print("Building portfolio from "+str(location))
        s3 = boto3.resource('s3')

        portfolio_bucket =s3.Bucket('portfolio.luis-norman.com')
        build_bucket = s3.Bucket(location["bucketName"])


        portfolio_zip = BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        topic.publish(Subject="Portfolio Deployed!", Message="Your portfolio has deployed successfully.")

        if job:
            codepipeline = boto3.client('codepipeline')

            return codepipeline.put_job_success_result(jobId=job["id"])

    except:
        topic.publish(Subject="Portfolio Not Deployed!", Message="Your portfolio was NOT deployed successfully.")
        raise
