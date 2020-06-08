import boto3
import smtplib
from datetime import date
from datetime import datetime
import datetime

from config import *


def data_chunk(paragraph):
    """
    Break up the text into 5000 byte chunks
    :param paragraph:
    :return: text_list
    """
    text_list = []
    while paragraph:
        text_list.append(str(paragraph[:5000]))
        paragraph = paragraph[5000:]

    return text_list[:25]


def sentiment_analysis():
    """
    Gets text and performs comprehend batch operations
    :return: key_phrases, entities, sentiment
    """
    s3 = boto3.client("s3")
    bucket_name = "lambda-comprehend-sent-diego"
    key = "blob/blob.txt"
    file = s3.get_object(Bucket=bucket_name, Key=key)
    paragraph = str(file['Body'].read())

    comprehend = boto3.client("comprehend")
    key_phrases = comprehend.batch_detect_key_phrases(TextList=data_chunk(paragraph), LanguageCode="en")
    entities = comprehend.batch_detect_entities(TextList=data_chunk(paragraph), LanguageCode="en")
    sentiment = comprehend.batch_detect_sentiment(TextList=data_chunk(paragraph), LanguageCode="en")

    return key_phrases, entities, sentiment


def break_sentiment(sentiment_dictionary):
    """
    Breaks up the sentiment result json object to make the results easier to read
    :param sentiment_dictionary:
    :return: negative, mixed, neutral, positive
    """
    ResultList = list(sentiment_dictionary.values())[0]
    sentiment_list = []

    for dictionary in ResultList:
        sentiment_list.append(list(dictionary.values())[1])

    negative = 0
    mixed = 0
    neutral = 0
    positive = 0
    for sentiment in sentiment_list:
        if sentiment == "NEGATIVE":
            negative = negative + 1
        if sentiment == "MIXED":
            mixed = mixed + 1
        if sentiment == "NEUTRAL":
            neutral = neutral + 1
        if sentiment == "POSITIVE":
            positive = positive + 1

    return negative, mixed, neutral, positive


# def email(negative, mixed, neutral, positive):
#     """
#     :param negative:
#     :param mixed:
#     :param neutral:
#     :param positive:
#     """
#     with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
#         smtp.ehlo()
#         smtp.starttls()
#         smtp.ehlo()
#
#         smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#
#         today = date.today()
#         date_text = today.strftime("%B %d, %Y")
#         currentDT = datetime.datetime.now()
#
#         subject = "Sentiment Analysis Results"
#         body = f"Sentiment Analysis Results of the wallstreetbets subreddit on {date_text} at {currentDT.strftime('%I:%M:%S %p')}\n" \
#                f"Negative Sentiment Score: {negative}\n" \
#                f"Mixed Sentiment Score: {mixed}\n" \
#                f"Neutral Sentiment Score: {neutral}\n" \
#                f"Positive Sentiment Score: {positive}"
#
#         msg = f"Subject: {subject}\n\n{body}"
#
#         smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg)


def publish(negative, mixed, neutral, positive):
    today = date.today()
    date_text = today.strftime("%B %d, %Y")

    negative = (negative / 25) * 100
    mixed = (mixed / 25) * 100
    neutral = (neutral / 25) * 100
    positive = (positive / 25) * 100


    currentDT = datetime.datetime.now()
    arn = "arn:aws:sns:us-east-1:743362587039:RedditTopic"
    sns_client = boto3.client("sns",
                              aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key,
                              region_name='us-east-1')
    message = f"Sentiment Analysis Results of the wallstreetbets subreddit on {date_text} at {currentDT.strftime('%I:%M:%S %p')}\n" \
              f"Amount of Negative Sentiment: {negative}%\n" \
              f"Amount of Mixed Sentiment: {mixed}%\n" \
              f"Amount of Neutral Sentiment: {neutral}%\n" \
              f"Amount of Positive Sentiment: {positive}%"
    response = sns_client.publish(TopicArn=arn, Message=message)
    print(response)


def add_done():
    s3 = boto3.resource('s3')
    bucket_name = 'lambda-comprehend-sent-diego'
    key = 'done/done.txt'
    text = 'analysis done'
    object = s3.Object(bucket_name, key)
    object.put(Body=text)


if __name__ == '__main__':
    # phrases = sentiment_analysis()[0]
    # entities = sentiment_analysis()[1]

    sentiment = sentiment_analysis()[2]

    publish(break_sentiment(sentiment)[0], break_sentiment(sentiment)[1], break_sentiment(sentiment)[2],
            break_sentiment(sentiment)[3])

    add_done()
