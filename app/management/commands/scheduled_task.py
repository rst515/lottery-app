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
logger.info("Testing: %s", TESTING)

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
    # pylint: disable=too-many-statements
    def handle(self, *args, **options):

        def prod_pythonanywhere():
            """Wake up the server"""
            try:
                response = requests.get(PYTHONANYWHERE_URL, timeout=20)
                if response.status_code != 200:
                    logger.error("Prod pythonanywhere server response status: %s", response.status_code)
                else:
                    logger.debug("Prod pythonanywhere server response status: %s", response.status_code)
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.error("Prod pythonanywhere server error: %s", err)

        def _get_webpage(url: str, today: str) -> BeautifulSoup:
            """Get saturday bonus ball result"""
            response = requests.get(url, timeout=5)
            logger.debug("GET result response status: %s", response.status_code)
            doc = BeautifulSoup(response.text, 'lxml')
            return doc.find(string=today)

        # pylint:disable=inconsistent-return-statements
        def _add_result_to_db(draw_date: str, bonus_ball: str) -> dict or None:
            if bonus_ball and draw_date:
                logger.info(
                    "Response received bonus_ball %s for %s... Attempting to send to database...",
                    bonus_ball, draw_date
                )
                try:
                    response = requests.post(
                        POST_RESULT_URL,
                        headers={'Authorization': f'Token {TOKEN}'},
                        json={'draw_date': draw_date, 'bonus_ball': bonus_ball},
                        timeout=10,
                    )
                    if response.status_code == 201:
                        logger.debug("POST Update db response status: %s \n %s", response.status_code, response.text)
                    if response.status_code != 201:
                        logger.error("POST Update db response status: %s %s", response.status_code, response.text)
                        return None

                    return response

                except Exception as err:  # pylint: disable=broad-exception-caught
                    logger.error("Error %s. Sending failure email...", err)
                    _send_failure_email(message=f"Failed to add result to database. \n{err}")
                    return None

        def _send_success_email(context: str) -> None:
            if context:
                context = json.loads(context)
                logger.debug(context)
                logger.debug("context draw date: %s", context['draw']['draw_date'])
                logger.debug("context bonus ball: %s", context['draw']['bonus_ball_id'])
                draw_date = datetime.strptime(context['draw']['draw_date'], "%Y-%m-%d").date()
                draw_date.strftime("%A %e %b %Y")
                context['draw']['draw_date'] = draw_date
                subject = 'Lottery Result for ', draw_date
                html_message = render_to_string('app/latest_result.html', context)
                plain_message = strip_tags(html_message)
                from_email = '"Lottery-App" <mmrust515@gmail.com>'
                to_email = RECIPIENTS
                send_mail(subject, plain_message, from_email, to_email, html_message=html_message,
                          fail_silently=False)
                logger.info('Email sent to %s.  Process finished.', to_email)
                logger.info("Successfully collected latest result and sent email notification!")

        def _send_failure_email(message):
            subject = 'Lottery: Failed to get results for %s', datetime.today().date().strftime("%a %d %b %Y")
            from_email = '"Lottery-App" <email1@example.com>'
            to_email = ['email1@example.com']
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
            )
            logger.error(
                'Email notification sent to %s. Process finished but failed to get or save latest results.',
                to_email
            )

        # pylint:disable=too-many-branches
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
                logger.debug("Today: %s", today)
                sat_result_doc = None
                try_counter = 0

                while not sat_result_doc and try_counter < 10:
                    #  Get bonus ball result for today
                    try_counter += 1
                    prod_pythonanywhere()
                    sat_result_doc = _get_webpage(url=LOTTO_URL, today=today)
                    if not sat_result_doc:
                        logger.info("No bonus ball for %s, trying again in 15 mins...  "
                                    "Tried %s times.", today, try_counter)

                        if not TESTING:
                            time.sleep(900)  # wait 15 mins
                        else:
                            time.sleep(2)  # testing
                            if try_counter == 3:  # testing
                                today = "Sat 13 May 2023"  # testing

                        logger.info("Trying again now...")
                        if try_counter == 10:
                            message = "Tried %s times. No bonus ball for %s. Giving up.", try_counter, today
                            logger.error("%s Sending failure notification...", message)
                            _send_failure_email(message=message)
                            break
                    else:
                        logger.debug("%s found. Attempting to find bonus ball...", today)
                        tag = sat_result_doc.parent.parent.parent
                        bonus_ball = tag.find(class_="ball lotto ball bonus-ball")
                        logger.debug("[SUCCESS] Bonus ball for %s: %s", today, bonus_ball.string)
                        draw_date = datetime.strptime(today, "%a %d %b %Y").date()
                        response = _add_result_to_db(
                            bonus_ball=bonus_ball.string,
                            draw_date=draw_date.strftime("%Y-%m-%d"),
                        )
                        if response:
                            if response.status_code == 201:
                                logger.debug("Response status code: %s %s", response.status_code, response.text)
                                logger.info("[SUCCESS] Bonus ball for %s saved.", today)
                                logger.info("Sending success email with %s.", response.text)
                                _send_success_email(response.text)
                                return

                            logger.error(
                                "[ERROR] %s \n %s \n Bonus ball for %s not saved.",
                                response.status_code,
                                response.text,
                                today
                            )
                            _send_failure_email(response.text)
                        else:
                            _send_failure_email(response)

        check_if_sat_and_fetch_latest_results()
