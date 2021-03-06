from twilio.rest import Client
from twilio.request_validator import RequestValidator
from twilio.base.exceptions import TwilioRestException


class TwilioClient:
    def __init__(self, account_sid, auth_token):
        self.client = Client(account_sid, auth_token)
        self.request_validator = RequestValidator(auth_token)

    def compute_signature(self, uri, params):
        """proxy twilio.RequestValidator.compute_signature()"""
        return self.request_validator.compute_signature(uri, params)

    def validate_request(self, uri, params, signature):
        """proxy twilio.RequestValidator.validate()"""
        return self.request_validator.validate(uri, params, signature)

    def send_sms(self, to="", from_="", body=""):
        try:
            message = self.client.messages.create(
                to=to,
                from_=from_,
                body=body
            )
        except TwilioRestException:
            # TODO log this original exception for debugging
            raise TwilioClientException('Failed to send SMS')

        return message


class TwilioClientException(Exception):
    pass
