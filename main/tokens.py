from datetime import date

from django.conf import settings
from django.utils import six
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from django.utils.dateformat import format


class UserActivateTokenGenerator:
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """
    key_salt = "main.tokens.UserActivateTokenGenerator"

    def make_token(self, user):
        """
        Returns a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token_with_timestamp(user)

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user), token):
            return False

        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS:
            return False

        return True

    def _make_token_with_timestamp(self, user):
        timestamp = int(format(user.date_joined, 'U'))
        ts_b36 = int_to_base36(timestamp)
        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(user),
        ).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _make_hash_value(self, user):
        # Ensure results are consistent across DB backends
        timestamp = int(format(user.date_joined, 'U'))
        return (
            six.text_type(user.pk) + user.password +
            six.text_type(timestamp)
        )

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        # Used for mocking in tests
        return date.today()

