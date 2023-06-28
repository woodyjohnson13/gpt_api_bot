import logging
import os

import threading
from openai_helper import OpenAIHelper, default_max_tokens
from telegram_bot import ChatGPTTelegramBot
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import dotenv_values,set_key,load_dotenv
import json
from datetime import datetime, timedelta

def check_and_remove():
            print('checking.....')
            env_vars = dotenv_values(".env")
            # Retrieve the current value of SAMPLE_VARIABLE from the dictionary
            is_allowed = env_vars.get("ALLOWED_TELEGRAM_USER_IDS")
            #creating json with allowed users_id
            my_dict=json.loads(is_allowed)
            
            keys_to_remove = []

            for key,value in my_dict.items():
                timestamp=datetime.fromisoformat(value)
                # Calculate the difference between the current date and the timestamp
                difference = datetime.now() - timestamp
                
                # Check if a month has passed (30 days or more)
                if difference >= timedelta(days=-3):
                    keys_to_remove.append(key)
                    # Delete the key-value pair from the dictionary
                    
                    
            for key in keys_to_remove:
                del my_dict[key]
                new_value=json.dumps(my_dict)
                set_key(".env", "ALLOWED_TELEGRAM_USER_IDS", new_value)
           

def main():
    # Read .env file
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Check if the required environment variables are set
    required_values = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_values = [value for value in required_values if os.environ.get(value) is None]
    if len(missing_values) > 0:
        logging.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)

    # Setup configurations
    model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    max_tokens_default = default_max_tokens(model=model)
    openai_config = {
        'api_key': os.environ['OPENAI_API_KEY'],
        'show_usage': os.environ.get('SHOW_USAGE', 'false').lower() == 'true',
        'stream': os.environ.get('STREAM', 'true').lower() == 'true',
        'proxy': os.environ.get('PROXY', None),
        'max_history_size': int(os.environ.get('MAX_HISTORY_SIZE', 15)),
        'max_conversation_age_minutes': int(os.environ.get('MAX_CONVERSATION_AGE_MINUTES', 180)),
        'assistant_prompt': os.environ.get('ASSISTANT_PROMPT', 'You are a helpful assistant.'),
        'max_tokens': int(os.environ.get('MAX_TOKENS', max_tokens_default)),
        'n_choices': int(os.environ.get('N_CHOICES', 1)),
        'temperature': float(os.environ.get('TEMPERATURE', 1.0)),
        'image_size': os.environ.get('IMAGE_SIZE', '512x512'),
        'model': model,
        'presence_penalty': float(os.environ.get('PRESENCE_PENALTY', 0.0)),
        'frequency_penalty': float(os.environ.get('FREQUENCY_PENALTY', 0.0)),
        'bot_language': os.environ.get('BOT_LANGUAGE', 'en'),
    }

    # log deprecation warning for old budget variable names
    # old variables are caught in the telegram_config definition for now
    # remove support for old budget names at some point in the future
    if os.environ.get('MONTHLY_USER_BUDGETS') is not None:
        logging.warning('The environment variable MONTHLY_USER_BUDGETS is deprecated. '
                        'Please use USER_BUDGETS with BUDGET_PERIOD instead.')
    if os.environ.get('MONTHLY_GUEST_BUDGET') is not None:
        logging.warning('The environment variable MONTHLY_GUEST_BUDGET is deprecated. '
                        'Please use GUEST_BUDGET with BUDGET_PERIOD instead.')

    telegram_config = {
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
        'admin_user_ids': os.environ.get('ADMIN_USER_IDS', '-'),
        'allowed_user_ids': os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '*'),
        'enable_quoting': os.environ.get('ENABLE_QUOTING', 'true').lower() == 'true',
        'enable_image_generation': os.environ.get('ENABLE_IMAGE_GENERATION', 'true').lower() == 'true',
        'enable_transcription': os.environ.get('ENABLE_TRANSCRIPTION', 'true').lower() == 'true',
        'budget_period': os.environ.get('BUDGET_PERIOD', 'monthly').lower(),
        'user_budgets': os.environ.get('USER_BUDGETS', os.environ.get('MONTHLY_USER_BUDGETS', '*')),
        'guest_budget': float(os.environ.get('GUEST_BUDGET', os.environ.get('MONTHLY_GUEST_BUDGET', '100.0'))),
        'stream': os.environ.get('STREAM', 'true').lower() == 'true',
        'proxy': os.environ.get('PROXY', None),
        'voice_reply_transcript': os.environ.get('VOICE_REPLY_WITH_TRANSCRIPT_ONLY', 'false').lower() == 'true',
        'voice_reply_prompts': os.environ.get('VOICE_REPLY_PROMPTS', '').split(';'),
        'ignore_group_transcriptions': os.environ.get('IGNORE_GROUP_TRANSCRIPTIONS', 'true').lower() == 'true',
        'group_trigger_keyword': os.environ.get('GROUP_TRIGGER_KEYWORD', ''),
        'token_price': float(os.environ.get('TOKEN_PRICE', 0.002)),
        'image_prices': [float(i) for i in os.environ.get('IMAGE_PRICES', "0.016,0.018,0.02").split(",")],
        'transcription_price': float(os.environ.get('TRANSCRIPTION_PRICE', 0.006)),
        'bot_language': os.environ.get('BOT_LANGUAGE', 'en'),
    }
    
    def hi():
        print("Im sheduler")

    # Setup and run ChatGPT and Telegram bot
    openai_helper = OpenAIHelper(config=openai_config)
    telegram_bot = ChatGPTTelegramBot(config=telegram_config, openai=openai_helper)
    # Create a scheduler
    scheduler = BlockingScheduler()

    # Schedule the check to run every morning at 8 AM
    scheduler.add_job(check_and_remove,'cron', hour=13,minute=45)

    scheduler_thread = threading.Thread(target=scheduler.start())
    scheduler_thread.start()


    telegram_bot.run()
    # Start the scheduler
    scheduler_thread.join()

    


if __name__ == '__main__':
    main()
