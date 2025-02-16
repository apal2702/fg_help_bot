from email.mime.text import MIMEText
import smtplib
import sys
import traceback


def send(from_, to, subject, body=None, client=None):
    """Send an email
    :param to: a list of addresses or a single email
    :param to_formatted: a list of formatted names, or a single name
    """

    # if `to` is not a list, make it one.
    to = [to] if type(to) is not list else to

    message = MIMEText(body, "html")
    message["From"] = from_
    message["To"] = ", ".join(to)
    message["Subject"] = subject

    smtp_client = None

    try:
        smtp_client = client or smtplib.SMTP("localhost", 25)
        smtp_client.sendmail(from_, to, message.as_string())
    except Exception as e:
        sys.stderr.write(
            'Caught exception {} \ntrying to send email "{}" to {}.'
            "\nStack trace is {}\n"
            "No emails were sent.\n".format(e, subject, to, traceback.format_exc())
        )
    finally:
        # close connection if smtp_client had to be created
        if client is None and smtp_client is not None:
            smtp_client.quit()


def send_email(subject, message):
    from_ = "donotreply_toll_fraud@twilio.com"
    to = ["apal@twilio.com"] #  "argupta@twilio.com", "saydas@twilio.com"
    #subject = "Toll Fraud Engine Failure"
    send(from_, to, subject, body=str(message))
