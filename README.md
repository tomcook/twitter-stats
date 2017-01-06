# twitter-stats
All-in-one Lambda function for scraping key metrics for a list of twitter accounts and sending them to DataDog for graphing. This lets you generate nice graphs to monitor account activity over time, and isn't limited to accounts you control.

![tweets over time](http://i.imgur.com/rgXpuSk.png)

## How to use this

1. Fork a copy of this repo to your account.

2. Create an AWS account if you don't already have one. [Sign up here](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html).

3. Create a new "app" on twitter and collect its Consumer Key/Secret and Access Token/Secret. For this app the privileges can be read-only. [Go here to make your app](https://apps.twitter.com).

4. Create a DataDog account if you don't already have one. [Sign up here](https://www.datadoghq.com/).

5. Create new API and App keys in DataDog. [Get them here](https://app.datadoghq.com/account/settings#api) once your account is set up.

6. Generate a new _Personal Access Key_ in GitHub. [You can do that here](https://github.com/settings/tokens).

7. Download the CloudFormation template in this repo to your local system. [It's here](../master/cloudformation/twitter-stats.yaml).

8. [Login to the AWS console](https://console.aws.amazon.com/).

9. Load the [CloudFormation console](https://console.aws.amazon.com/cloudformation/). Note that this will be in your default AWS Region, so be sure to select whatever region you want this tool to live long-term. `us-west-2` (Oregon) and `us-east-1` (Virginia) are good choices for most people.

10. Click __Create New Stack__

11. Check __Upload a template to Amazon S3__ then use the file picker to find the `twitter-stats.yaml` file you downloaded in step five.

12. This next page will have a lot of text fields to fill out, and you'll be pasting in all the twitter, github, and datadog access keys you created in the above steps. Note that the access keys will only display as asterisks; you also won't be able to retrieve them later via CloudFormation. Additionally, some key fields to fill out:

  - __Stack name__: This needs to be unique to your account & AWS region. A good value here would be `twitter-stats`, but you can make it anything.
  - __Accounts__: A semicolon-separated list of accounts you want to gather stats for. For example: `jack;hillaryclinton;clickhole`. The reason this is semicolon-separated and not comma-separated is boring but in the FAQ below.
  - __Frequency__: This is the interval, in minutes, that your Lambda will run to gather stats. Minimum is five minutes, since more aggressive checking might annoy the twitter API. This will also determine how much you pay in Lambda costs; the more frequent you check, the more you pay (although Lambda is really cheap, so it will cost almost nothing to run every five minutes)
  - __GitHub Settings__: You should clone this repo, then fill in these details with your username and the repo. Strongly advise against linking to the primary copy of this repo, since I might change code at any time and your AWS account would auto-deploy it with whatever I put in there (!)
  - __DataDog Metric Name Prefix__: The lambda is going to create new metrics in DataDog for each of the monitored twitter metrics. This string will be a prefix on all of the metrics it creates, so if you have an existing namespace then add it here. Created metrics will look like `{prefix}.status_count` plus a tag with the twitter account on the metrics.
  - __S3 Log Bucket__: This CloudFormation is going to create two S3 buckets. Since we follow security-conscious best practices in AWS, those new buckets will be configured to log all read/write activity to another S3 bucket. The log bucket must be in the same region as this CloudFormation template it deployed. You have a few options here:
    - Use an existing bucket in your account
    - Manually create a new S3 bucket
    - Use another one of my CloudFormation templates ([available here](https://github.com/tomcook/cloudformation/blob/master/logging/Baseline-S3.yaml)) to setup a brand new S3 bucket preconfigured for logging. This is what I do.
  - __FunctionName__: Best to leave this as `twitter-stats` in case you have a good reason to change it.

13. Click __Next__.

14. Don't fill anything out on the "Options" page. Click __Next__.

15. On the next page ("Review") check __I acknowledge that AWS CloudFormation might create IAM resources__ then click __Create__.

16. CloudFormation will begin creating all of your resources, linking them together, compiling the Lambda function, and setting up its invocation timer. If all goes well then after 5-10 minutes you should have a full functioning Lambda function, diligently gathering Twitter stats until the Earth crashes into the Sun, or until you stop paying your Amazon bill.

## Services Used

These are all of the services and libraries assembled to make this work. If you deploy this service into your AWS account it __will incur costs__ although they should be very minimal. DataDog offers a free trial and a "lite" tier, so they are mostly free to use.

### AWS

- [CloudFormation](https://aws.amazon.com/cloudformation/)
- [Lambda](https://aws.amazon.com/lambda/)
- [CodePipeline](https://aws.amazon.com/codepipeline/)
- [CodeBuild](https://aws.amazon.com/codebuild/)
- [SAM](http://docs.aws.amazon.com/lambda/latest/dg/deploying-lambda-apps.html)
- [S3](https://aws.amazon.com/s3/)

### DataDog

- [Python library](https://github.com/DataDog/datadogpy)
- [API](http://docs.datadoghq.com/api/)

### Twitter

- [tweepy](http://docs.tweepy.org/en/v3.5.0/)
- [Twitter REST API](https://dev.twitter.com/rest/public)

## What does this actually do, though?

When you run this CloudFormation template it creates a number of resources from scratch and links them all together. The rough order of operations:

1. It creates a couple S3 buckets to store files that will be generated by other parts of the process
2. It creates a CodePipeline....pipeline, which is the overall system that manages the fetching, building, and deployment of everything else.
3. That pipeline connects to GitHub and fetches the contents of the repo you specified at setup. It will also monitor that repo for any future commits and re-run the following steps automatically.
4. The repo contents are passed along to AWS CodeBuild, which creates a temporary build environment to download the python dependencies using `pip`. It then uses the `samTemplate.yaml` CloudFormation template to package the Lambda, upload it to one of the S3 buckets we created at the start, and generate a bespoke CloudFormation template for the next step.
5. Pipeline then takes the generated CloudFormation template (called `NewSamTemplate.yaml`) and runs it as a _new_ CloudFormation deploy. This creates a separate CloudFormation stack and a "Change Set" describing all the things it'll create to wire up the actual Lambda function.
6. The new CloudFormation Change Set will now be "deployed", which creates the Lambda function with our code and the CloudWatch Events cron-like trigger to make it run on a schedule.

Along the way a number of IAM Roles will also be created to allow each of these tools to do what they need. I've tried to scope the IAM policy grants to be as restrictive as possible to minimize malicious/accidental access, but IAM is an imperfect system so it's still looser than I'd like to maintain functionality.


## FAQ

- __Q:__ _I'm a cool person, web GUIs are lame, and I only want to use CLIs!_

  __A:__ Install the [AWS CLI](https://aws.amazon.com/cli/) and follow the instructions [here](http://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-stack.html) to get going. How to adapt the above instructions is left as an exercise for the reader.

- __Q:__ _How do I delete all of this once I've set it up?_

  __A:__ In the CloudFormation console, right click on both of the stacks created by this template and select "Delete Stack". Some resources that they create might not be possible to auto-purge and you may need to do that manually. S3 buckets will need to be empty, for example.

- __Q:__ _This should be in [Terraform](https://github.com/hashicorp/terraform) instead of CloudFormation_

  __A:__ I agree, Terraform is a much better system overall, but my goals here were to keep this simple and self-contained into as few moving parts as possible. Terraform would have introduced, at minimum, a CLI component and state management. CloudFormation is much simpler and allows all non-code components to fit into a single file. I also wanted to build something complex with CloudFormation as a challenge, since I'm less familiar with it.

- __Q:__ _This seems awfully complicated for less than 50 lines of python and a twitter API client._

  __A:__ It is quite a bit, but I wanted to experiment with some of the features announced at AWS's re:Invent 2016 conference (notably CodeBuild), and since the function depends on a third-party library the only other option would be to check-in a compiled zip, which is even more gross. In the past I've used tools like [Apex](https://apex.run) for managing small Lambda projects, but with CodeBuild announced I'm migrating all of my projects off of it onto this workflow.

- __Q:__ _Why did you write this in Python? Also your code is awful_

  __A:__ Python is what I'm most confortable with. The code isn't very optimized, does no error handling, and probably has bugs. I'm not worried about this.

- __Q:__ _Why is the account list semicolon-separated and not comma-separated?_

  __A:__ CloudFormation has a data type `CommaDelimitedList` that would be perfect here, but because of the wonky way I push the values entered at the CF configuration layer all the way into the Lambda function, it's challenging to convert back and forth from `CommaDelimitedList` to `String` cleanly. I punted on this for now, but it would be a good enhancement in the future.

- __Q:__ _How can I run this on [Google Cloud Functions](https://cloud.google.com/functions/) or [Microsoft Azure Functions](https://azure.microsoft.com/en-us/services/functions/) instead of AWS Lambda?_

  __A:__ I have absolutely no idea, but if you port this to another system please let me know!

## Caveats

- Credentials for Twitter, DataDog, and GitHub are __NOT__ stored in an encrypted format and may be accessible to others with access to your AWS account, and allow takeover or data leakage for the linked accounts. Although they aren't viewable in CloudFormation, they are in the Lambda function's environment variables as plaintext. In the future encrypting these values would be a great enhancement, but it wasn't a priority for the initial release.

## Contact

If you've got questions or want to chat about this project, the best bet is to @mention me on twitter. My handle is [@ywxwy](https://twitter.com/ywxwy). All other public contact info is on [tom.horse](https://tom.horse).
