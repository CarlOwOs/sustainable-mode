"""
Automated news analysis and sentiment scoring using Bedrock.

@dev Ensure AWS environment variables are set correctly for Bedrock access.

Note on Bedrock compatibility:
Amazon Bedrock models (like Nova Pro) have specific requirements for tool calling.
They cannot mix conversation content and tool results in the same message turn.
To ensure compatibility, we explicitly set tool_calling_method=None when initializing the Agent
and use a custom message format for Bedrock.
"""

import os
import sys
import logging
import json
import boto3
from langchain_aws import ChatBedrock
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import asyncio

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

controller = Controller()

class LoggingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("llm_callback")
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.logger.info(f"LLM Start - Prompts: {prompts}")
    
    def on_llm_end(self, response, **kwargs):
        self.logger.info(f"LLM Response: {response}")
    
    def on_llm_error(self, error, **kwargs):
        self.logger.error(f"LLM Error: {error}")


class BedrockMessageFormatter:
    """
    Custom message formatter for Bedrock models.
    
    This class helps format messages in a way that's compatible with Bedrock's requirements,
    specifically avoiding mixing conversation content and tool results in the same turn.
    """
    @staticmethod
    def format_messages(messages):
        """
        Format messages for Bedrock compatibility.
        
        This method ensures that tool results and conversation content are not mixed
        in the same message turn, which is a requirement for Bedrock models.
        """
        formatted_messages = []
        
        for i, message in enumerate(messages):
            # Skip tool messages as they'll be incorporated into the next human message
            if message.type == "tool":
                continue
                
            # For AI messages with tool calls, remove content to avoid mixing
            if message.type == "ai" and hasattr(message, "tool_calls") and message.tool_calls:
                # Create a new AI message with just the tool calls
                formatted_message = AIMessage(
                    content="",  # Empty content to avoid mixing with tool calls
                    tool_calls=message.tool_calls
                )
                formatted_messages.append(formatted_message)
            else:
                formatted_messages.append(message)
                
        return formatted_messages


def get_llm():
    return ChatBedrock(
        model_id="us.amazon.nova-pro-v1:0",
        temperature=0.0,
        max_tokens=None,
        callbacks=[LoggingCallbackHandler()]
    )

@controller.action('Read the most recent image from my S3 bucket')
async def read_most_recent_image_from_s3():
    print("Reading the most recent image from my S3 bucket")
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")

    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        # Get the most recent image by sorting by last modified date
        most_recent_image = max(response['Contents'], key=lambda x: x['LastModified'])
        image_key = most_recent_image['Key']
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
        return image_url
    else:
        return "No images found in the S3 bucket"

# Define the task for the agent
task = (
    "Read the most recent image from my S3 bucket."
    "Do reverse image search with the image url from the previous action."
    # "Find the most similar image in the search results."
    # "Click on the most similar image."
    # "Open the website of the image in a new tab."
    # "Extract the text from the website."
    # "Summarize the text in 3-4 sentences."
)

parser = argparse.ArgumentParser()
parser.add_argument('--query', type=str, help='The query for the agent to execute', default=task)
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args = parser.parse_args()

# Set debug level if requested
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

llm = get_llm()
logger.info("LLM initialized with model: us.amazon.nova-pro-v1:0")

browser = Browser(
    config=BrowserConfig(
        # chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    )
)

# Create a custom Agent class that uses our BedrockMessageFormatter
class BedrockAgent(Agent):
    async def get_next_action(self, input_messages):
        # Format messages for Bedrock compatibility
        formatted_messages = BedrockMessageFormatter.format_messages(input_messages)
        # Call the parent method with formatted messages
        return await super().get_next_action(formatted_messages)

agent = BedrockAgent(
    task=args.query, 
    llm=llm, 
    controller=controller, 
    browser=browser, 
    validate_output=True,
    tool_calling_method=None,  # Explicitly set to None for Bedrock compatibility
)
logger.info(f"Agent initialized with task: {args.query}")


async def main():
    logger.info("Starting agent execution")
    await agent.run(max_steps=30)
    logger.info("Agent execution completed")
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())