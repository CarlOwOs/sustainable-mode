"""
Automated news analysis and sentiment scoring using Bedrock.

@dev Ensure AWS environment variables are set correctly for Bedrock access.
"""

import os
import sys
import dotenv
import requests

from langchain_aws import ChatBedrock
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(_file_))))
import argparse
import asyncio

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller



dotenv.load_dotenv()

controller = Controller()

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
        max_tokens=None
    )

@controller.action('Send a notification of sale')
def notification_of_sale():
    url = "http://128.179.131.122:5001/webhook/notifications"
    payload = {
        "title": "Delivery Notification",
        "message": f"Congrats! Your Mac charger has been sold. You can send it to Giulia at rue de la Frite 11, Pomés.",
        "type": "success",
        "sender": "Delivery Service"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending delivery notification: {e}")
        return None
    return "Message sent"

# Define the task for the agent
task = (""
     "1) Visit facebook with this URL: https://www.facebook.com/messages/e2ee/t/8796227860444726/ , your big picture goal will be to arrange the sale of a charger through facebook marketplace."
     "2) In the conversations, click on 'Marketplace' channel"
     "3) Enter the conversation with Giulia because she's interested in buying the charger."
     "4) Send her one text to tell her that the package is available and she will be receiving it tomorrow at 4pm. "
     "5) Click the blue arrow button to send the text. DO NOT confuse it with the emoji button. "
     "6) Send a notification of sale.")
    #  "4)Now reply to the text and send it by CLICKING THE ARROW"
    #  "5) Have a conversation with her for a few minutes until she accepts to buy, make sure you send each of your texts with the arrow")

    #  "4) Now reply as a salesperson. Don't fprget to click the arrow to send the text "
    #  "5) Wait for her answer and once received, reply again, don't forget to negotiate."
    #  "6) Wait fro her asnwer and if she accepted, ask for her address."
    #  "7) Wait fro her to give her address, when she does, send a last text to explain that it will be shipped to her under 3 days."
    #  "8) You can stop after you sent the last information text")
# task = (
#     "1) Visit messenger  with this URL: https://www.facebook.com/messages/t/9432266156840821/ "
#     "2) In the conversations, click on 'Marketplace' channel"
#     "3) If anyone sent me a text and is interested in buying the CHARGER that I put to sale, enter the conversation - ONLY FOR THE CHARGER."
#     "4) Now read their text and reply, act as a salesperson"
#     "5) Click on the arrow to send the text"
#     "6) Go back to the messages and replay everything from step 1 if there are other interested people in a CHARGER."
#     "7) If someone is sending follow up messages, for example if they want to proceed to buy specifically the CHARGER, talk them through the next steps: ask for their address and close the deal. If they try to negotiate, negotiate back."
# )

#discuss with the person until you get them to agree to come pick it up on a given day and time.

parser = argparse.ArgumentParser()
parser.add_argument('--query', type=str, help='The query for the agent to execute', default=task)
args = parser.parse_args()

llm = get_llm()

browser = Browser(
    config=BrowserConfig(
         chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    )
)

# agent = Agent(
#     task=args.query, llm=llm, controller=Controller(), browser=browser, validate_output=True,
# )

# Create a custom Agent class that uses our BedrockMessageFormatter
class BedrockAgent(Agent):
    async def get_next_action(self, input_messages):
        # Format messages for Bedrock compatibility
        formatted_messages = BedrockMessageFormatter.format_messages(input_messages)
        # Call the parent method with formatted messages
        return await super().get_next_action(formatted_messages)

# extend_system_message = """
# Never wait longer than 5 seconds. Be very responsive.
# """

async def main():
    agent = BedrockAgent(
        task=args.query, 
        llm=llm, 
        controller=controller, 
        browser=browser, 
        validate_output=True,
        tool_calling_method=None,  # Explicitly set to None for Bedrock compatibility
    # extend_system_message = extend_system_message
    )
    await agent.run(max_steps=30)
    await browser.close()


asyncio.run(main())