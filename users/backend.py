# users/backend.py
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend

class FixedEmailBackend(DjangoEmailBackend):
    """
    A fix for Django 3.2 + Python 3.12 on Windows, avoids keyfile/certfile error with starttls()
    """
    def open(self):
        if self.connection:
            return False
        try:
            import smtplib
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                self.connection.starttls()  # <-- no keyfile/certfile
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False
