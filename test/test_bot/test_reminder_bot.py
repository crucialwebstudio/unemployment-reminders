import json
from datetime import datetime
from unittest import TestCase, mock
from lib.twilio import TwilioClientException
from bot import ReminderBot, ReminderBotException

twilio_request_prototype = {
    'CurrentTask':           'remind_me',
    'CurrentInput':          'Remind me ',
    'Channel':               'sms',
    'NextBestTask':          '',
    'CurrentTaskConfidence': '1.0',
    'AssistantSid':          '{SOME_GUID}',
    'AccountSid':            '{SOME_GUID}',
    'UserIdentifier':        '+17735551234',
    'DialoguePayloadUrl':    'https://autopilot.twilio.com/v1/Assistants/{GUID_1}/Dialogues/{GUID_2}',
    'Memory':                json.dumps({
        'twilio': {
            'sms':            {
                'To':         '+17735554321',
                'From':       '+17735551234',
                'MessageSid': '{SOME_GUID}'
            },
            'collected_data': {
                'next_alert_date': {
                    'answers': {
                        'next_alert_date': {
                            'answer': 'next monday'
                        }
                    }
                }
            }
        }
    })
}


class BotTests(TestCase):
    def setUp(self):
        self.bot = ReminderBot()

    def tearDown(self):
        pass

    @mock.patch('bot.collect.next_alert.get_utc_now')
    def test_create_alert_model(self, mock_utc_now):
        mock_utc_now.return_value = datetime.fromisoformat('2020-06-01T10:00:00+00:00')

        self.bot.receive_message(twilio_request_prototype)

        expected = {
            'phone_number':  '+17735551234',
            'timezone':      'America/Chicago',
            'alert_day':     'monday',
            'alert_time':    '09:30:00',
            'in_progress':   0,
            'next_alert_at': '2020-06-15T14:30:00+00:00'
        }
        actual = self.bot.create_alert_model()

        self.assertEqual(expected, actual)

    @mock.patch('bot.reminder_bot.twilio_client.send_sms')
    def test_say_intro(self, mock_create_message):
        expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
        expected_error_code = None

        mock_create_message.return_value.sid = expected_sid
        mock_create_message.return_value.error_code = expected_error_code

        actual = self.bot.say_intro('+17735551234')

        self.assertTrue(mock_create_message.called)
        self.assertEqual(expected_sid, actual.sid)
        self.assertEqual(expected_error_code, actual.error_code)

    @mock.patch('bot.reminder_bot.twilio_client.send_sms')
    def test_say_intro_raises_exception(self, mock_send_sms):
        mock_send_sms.side_effect = ReminderBotException()

        self.bot.receive_message(twilio_request_prototype)
        with self.assertRaises(ReminderBotException):
            self.bot.say_intro('+17735551234')

    @mock.patch('bot.reminder_bot.twilio_client.send_sms')
    def test_say_reminder(self, mock_create_message):
        expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
        expected_error_code = None

        mock_create_message.return_value.sid = expected_sid
        mock_create_message.return_value.error_code = expected_error_code

        actual = self.bot.say_reminder('+17735551234')

        self.assertTrue(mock_create_message.called)
        self.assertEqual(expected_sid, actual.sid)
        self.assertEqual(expected_error_code, actual.error_code)

    @mock.patch('bot.reminder_bot.twilio_client.send_sms')
    def test_say_reminder_raises_exception(self, mock_send_sms):
        mock_send_sms.side_effect = ReminderBotException()

        self.bot.receive_message(twilio_request_prototype)
        with self.assertRaises(ReminderBotException):
            self.bot.say_reminder('+17735551234')

    def test_say_thanks(self):
        self.bot.receive_message(twilio_request_prototype)
        actual = self.bot.say_thanks()

        # make sure 'say' is in the list of actions
        self.assertTrue(any(x['say'] is not None for x in actual['actions']))

    def test_next_alert_valid(self):
        # change the form post to something valid
        form_post = twilio_request_prototype
        form_post['CurrentInput'] = 'Monday'

        self.bot.receive_message(form_post)
        expected = {'valid': True}
        actual = self.bot.validate_next_alert()

        self.assertEqual(expected, actual)

    def test_next_alert_invalid(self):
        # change the form post to something invalid
        form_post = twilio_request_prototype
        form_post['CurrentInput'] = 'this is wrong'
        self.bot.receive_message(form_post)
        expected = {'valid': False}
        actual = self.bot.validate_next_alert()

        self.assertEqual(expected, actual)

    @mock.patch('bot.reminder_bot.alerts.create_alert')
    def test_subscribe(self, mock_create_alert):
        self.bot.receive_message(twilio_request_prototype)
        actual = self.bot.subscribe()

        self.assertTrue(mock_create_alert.called)
        self.assertIsNone(actual)

    @mock.patch('bot.reminder_bot.alerts.delete_alert')
    def test_unsubscribe(self, mock_delete_alert):
        self.bot.receive_message(twilio_request_prototype)
        actual = self.bot.unsubscribe()

        self.assertTrue(mock_delete_alert.called)
        self.assertIsNone(actual)


if __name__ == "__main__":
    unittest.main()
