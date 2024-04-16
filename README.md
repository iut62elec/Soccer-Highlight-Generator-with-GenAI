
# Soccer Highlight Generator

Automate the creation of soccer match highlights with the power of Generative AI and AWS. This solution leverages AWS Bedrock (Anthropic’s Claude 3 Sonnet model), AWS MediaConvert, Lambda, Step Functions and other AWS services to identify and compile exciting game moments without manual editing.

## Author

Pedram Jahangiri <www.linkedin.com/in/pedram-jahangiri>

## Getting Started

For a detailed explanation of what this solution does and the benefits it offers, please refer to my [blog post].

### Prerequisites

- AWS CLI installed and configured with the necessary permissions
- Node.js and npm
- Python 3.11 and pip
- An AWS account with the required services enabled
- Access to Amazon Bedrock foundation models (Before you can use a foundation model in Amazon Bedrock, you must request access to it. Use this Link for detail <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>)

### Installation

Clone the repository in your local machine:

```bash
git clone https://github.com/iut62elec/Soccer-Highlight-Generator-with-GenAI.git
```


Navigate to the Soccer-Highlight-Generator-with-GenAI directory:

```bash
cd Soccer-Highlight-Generator-with-GenAI
```

Set up a virtual environment and activate it:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install the AWS CDK and required Python packages:

```bash
npm install -g aws-cdk@latest
npm update -g aws-cdk
nvm install 18
nvm use 18
npm install -g aws-cdk@latest
pip install --upgrade pip
pip install aws-cdk.aws-lambda aws-cdk.aws-stepfunctions aws-cdk.aws-stepfunctions-tasks aws-cdk.aws-cloudfront aws_cdk.aws_cloudfront_origins aws-cdk.aws-s3-deployment
```

Deploy the solution using CDK:

- Email subscription: Open the config.json file and add the email address where you want to receive the highlight video link

- Deploy

```bash
aws configure --profile xxx
export AWS_PROFILE=XXX
cdk bootstrap
cdk deploy --profile XXX
```

### Usage

After the solution is deployed:

1. Go to the S3 console and locate the bucket contain "videoassetsbucket".
2. Create a folder named "public" and upload a sample video named "Final_2022.mp4" from "sample_video" folder into the "public" folder.
3. In the AWS Step Functions console, find the "SoccerHighlightsStateMachine" state machine.
4. Start the execution with the following JSON input in str format:

```
"{\"file_name\":\"Final_2022.mp4\"}"
```
5. After completion, you will receive an email at the subscribed address with a link to the highlight video.


This example video highlight was generated using this solution. The tool processed an already extended highlighted video from the 2022 FIFA World Cup final between Argentina and France, originally 5 minutes long, provided by Fox. This game was chosen due to its high-scoring nature, including 6 goals and subsequent penalty shots. The generated highlight effectively removes all unnecessary moments, retaining only the goals and penalty kicks, and reduces the video to ~4 minutes. Feel free to test this tool with other games as well.


<a href="https://vimeo.com/935254589?share=copy">
    <img src="./sample_video/cover.jpg" alt="Watch the video" width="500"/>
</a>

## Contributing

Join the game by implementing and testing the Soccer Highlight Generator. Your feedback and contributions are welcome. Please follow the instructions in the repository and share your experiences to enhance sports entertainment with AWS and Generative AI.

## License

This project is licensed under the MIT License.

## Disclaimer

This repository and its contents are not endorsed by or affiliated with Amazon Web Services (AWS) or any other third-party entities. It represents my personal viewpoints and not those of my past or current employers. All third-party libraries, modules, plugins, and SDKs are the property of their respective owners.


