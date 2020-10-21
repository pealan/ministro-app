import json
import tweepy
import locale
import urllib.request
import logging
import sys

from datetime import date

"""Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    # First day without a minister of health
    last_date = date(2020, 5, 15)

    logger.info('## RECEIVED EVENT')
    logger.info(event)

    logger.info('Opening configuration file...')
    with open('ministro_config.json', 'r') as f:
        config = json.load(f)
    logger.info('Configuration file opened')

    logger.info('Calculating days without minister...')
    today = date.today()
    days_without = today - last_date
    logger.info('Days calculated: %s', days_without.days)

    api_string = 'Informações sobre a pandemia indisponíveis no Portal!'
    try:
        logger.info('Trying to get response from COVID-19 API...')
        api_url = config['api_url']
        api_response = urllib.request.urlopen(api_url)
        api_data = json.loads(api_response.read())
        logger.info('API responded:')
        logger.info(api_data)

        logger.info('Retrieving expected information from JSON response..')
        total_confirmados = api_data['confirmados']['total']
        total_obitos = api_data['obitos']['total']
        api_string = ''.join(["Total de casos confirmados de COVID-19: ", "{:n}".format(int(total_confirmados)), "\n",
                "Total de óbitos por COVID-19: ", "{:n}".format(int(total_obitos))])
        logger.info('API data retrieved')
        logger.info('Constructed string %s', api_string)

    except Exception as e: 
        logger.error('Something went wrong trying to get COVID-19 API information:')
        logger.error(e)

    try:
        logger.info('Retrieving Twitter API values from config file...')
        consumer_key = config['consumer_key']
        consumer_secret = config['consumer_secret']
        access_token = config['access_token']
        access_token_secret = config['access_token_secret']
        logger.info('Twitter API data retrieved')

        logger.info('Authenticating for Twitter API...')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        logger.info('Authenticated for Twitter API')

        logger.info('Constructing tweet string and tweeting...')
        message = ''.join(["Estamos há ", str(days_without.days), " dias sem um ministro da Saúde durante uma pandemia!\n\n",
                api_string])
        api.update_status(message)
        logger.info('Tweet successful!')
        logger.info('\n\'%s\'', message)
    except Exception as e:
        logger.error('Something went wrong trying to use the Twitter API:')
        logger.error(e)
        raise

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "MinistroBot successfully tweeted!",
        }),
    }
