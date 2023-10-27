"""
NOT WORKING AS WENSITE NOT WHITE-LILSTED BY PA
This is the script to collect the latest results and send email notification - if today is Saturday.
Relies on scheduled task on PA.
Run with > python manage.py scheduled_task
Test by setting TESTING=True
"""
import json
import os
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from dotenv import load_dotenv

from app.custom_logger import logger

load_dotenv()
logger.setLevel('DEBUG')

TESTING = False  # Set to True if you want to test the script.
logger.info("Testing: {testing_mode}".format(testing_mode=TESTING))

LOTTO_URL = 'https://www.uk-lotto.com/lotto'
PYTHONANYWHERE_URL = 'https://lottery-app.eu.pythonanywhere.com/'

if TESTING:
    RECIPIENTS = ['email1@example.com']  # for test
    POST_RESULT_URL = 'http://127.0.0.1:8000/post-result/'
    TOKEN = os.getenv("NEW_RESULT_TOKEN_FOR_LOCAL_TEST")
else:
    RECIPIENTS = ['email1@example.com', 'email2@example.uk', 'email3@example.com']
    POST_RESULT_URL = 'https://lottery-app.eu.pythonanywhere.com/post-result/'
    TOKEN = os.getenv("NEW_RESULT_TOKEN_FOR_PA")


class Command(BaseCommand):

    def handle(self, *args, **options):

        def prod_pythonanywhere():
            """Wake up the server"""
            try:
                response = requests.get(PYTHONANYWHERE_URL, timeout=20)
                if response.status_code != 200:
                    logger.error(f"Prod pythonanywhere server response status: {response.status_code}")
                else:
                    logger.debug(f"Prod pythonanywhere server response status: {response.status_code}")
            except Exception as e:
                logger.error(f"Prod pythonanywhere server error: {e}")

        def _get_webpage(url: str, today: str) -> BeautifulSoup:
            """Get saturday bonus ball result"""
            response = requests.get(url, timeout=5)
            logger.debug(f"GET result response status: {response.status_code}")
            doc = BeautifulSoup(response.text, 'lxml')
            return doc.find(string=today)

        def _add_result_to_db(draw_date: str, bonus_ball: str) -> dict or None:
            if bonus_ball and draw_date:
                logger.info(
                    "Response received bonus_ball {bonus_ball} for {draw_date}..."
                    "Attempting to send to database...".format(
                        bonus_ball=bonus_ball, draw_date=draw_date
                    )
                )
                try:
                    response = requests.post(
                        POST_RESULT_URL,
                        headers={'Authorization': f'Token {TOKEN}'},
                        json={'draw_date': draw_date, 'bonus_ball': bonus_ball},
                        timeout=10,
                    )
                    if response.status_code == 201:
                        logger.debug(f"POST Update db response status: {response.status_code}\n{response.text}")
                    if response.status_code != 201:
                        logger.error(f"POST Update db response status: {response.status_code}\n{response.text}")
                        return None

                    return response

                except Exception as e:
                    logger.error(f"Error {e}.  Sending failure email...")
                    _send_failure_email(message=f"Failed to add result to database. \n{e}")
                    return None

        def _send_success_email(context: str) -> None:
            if context:
                context = json.loads(context)
                logger.debug(f"{context=}")
                logger.debug(f"context draw date: {context['draw']['draw_date']}")
                logger.debug(f"context bonus ball: {context['draw']['bonus_ball_id']}")
                draw_date = datetime.strptime(context['draw']['draw_date'], "%Y-%m-%d").date()
                draw_date.strftime("%A %e %b %Y")
                context['draw']['draw_date'] = draw_date
                subject = f'Lottery Result for {draw_date}'
                html_message = render_to_string('app/latest_result.html', context)
                plain_message = strip_tags(html_message)
                from_email = '"WV Lottery" <mmrust515@gmail.com>'
                to_email = RECIPIENTS
                send_mail(subject, plain_message, from_email, to_email, html_message=html_message,
                          fail_silently=False)
                logger.info(f'Email sent to {to_email}.  Process finished.')
                logger.info("Successfully collected latest result and sent email notification!")

        def _send_failure_email(message):
            subject = f'Lottery: Failed to get results for ' \
                      f'{datetime.today().date().strftime("%a %d %b %Y")}'
            from_email = '"Lottery-App" <email1@example.com>'
            to_email = ['email1@example.com']
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
            )
            logger.error(f'Email notification sent to {to_email}. '
                         f'Process finished but failed to get or save latest results.'
                         )

        def check_if_sat_and_fetch_latest_results():
            """
            If today is Saturday (0 = Mon, 1 = Tue, 2 = Wen ... 5 = Sat)
            """
            if not TESTING and datetime.today().weekday() != 5:
                logger.info("Today is not Saturday. Will try again tomorrow.")
            else:
                # If today is present in doc fetch bonus ball
                today = datetime.today().strftime("%a %-d %b %Y")
                if TESTING:  # adjust timedelta days to choose last draw date, e.g. if today sunday then 1
                    today = (datetime.today() - timedelta(days=1)).strftime("%a %-d %b %Y")
                logger.debug(f"Today: {today}")
                sat_result_doc = None
                try_counter = 0

                while not sat_result_doc and try_counter < 10:
                    #  Get bonus ball result for today
                    try_counter += 1
                    prod_pythonanywhere()
                    sat_result_doc = _get_webpage(url=LOTTO_URL, today=today)
                    if not sat_result_doc:
                        logger.info(f"No bonus ball for {today}, trying again in 15 mins...  "
                                    f"Tried {try_counter} times.")

                        if not TESTING:
                            time.sleep(900)  # wait 15 mins
                        else:
                            time.sleep(2)  # testing
                            if try_counter == 3:  # testing
                                today = "Sat 13 May 2023"  # testing

                        logger.info("Trying again now...")
                        if try_counter == 10:
                            message = f"Tried {try_counter} times. No bonus ball for {today}. Giving up."
                            logger.error(f"{message} Sending failure notification...")
                            _send_failure_email(message=message)
                            break
                    else:
                        logger.debug(f"{today} found. Attempting to find bonus ball...")
                        tag = sat_result_doc.parent.parent.parent
                        bonus_ball = tag.find(class_="ball lotto ball bonus-ball")
                        logger.debug(f"[SUCCESS] Bonus ball for {today}: {bonus_ball.string}")
                        draw_date = datetime.strptime(today, "%a %d %b %Y").date()
                        response = _add_result_to_db(
                            bonus_ball=bonus_ball.string,
                            draw_date=draw_date.strftime("%Y-%m-%d"),
                        )
                        if response:
                            if response.status_code == 201:
                                logger.debug(f"Response status code: {response.status_code}\n{response.text}")
                                logger.info(f"[SUCCESS] Bonus ball for {today} saved.")
                                logger.info(f"Sending success email with {response.text}.")
                                _send_success_email(response.text)
                                return
                            else:
                                logger.error(f"[ERROR] {response.status_code}\n{response.text}\n"
                                             f"Bonus ball for {today} not saved.")
                                _send_failure_email(response.text)
                        else:
                            _send_failure_email(response)

        check_if_sat_and_fetch_latest_results()
