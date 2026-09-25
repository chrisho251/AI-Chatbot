"""Send notifications to experts. Stub owned by Lane A.

Purpose
Real time notification of the on duty expert. Mailpit captures the mail locally, SES sends it on
AWS.

What to build
A Notifier protocol with notify, an SMTP implementation for Mailpit using smtplib, and an SES
implementation with boto3 for phase 2. The message holds the ticket id and a link, never the
student identity.

How to test
Run a local SMTP debugging server in the test or fake smtplib.
"""

from typing import Protocol


class Notifier(Protocol):
    def notify(self, to: str, subject: str, body: str) -> None: ...


class SmtpNotifier:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def notify(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError("SMTP notifications are not written yet")
