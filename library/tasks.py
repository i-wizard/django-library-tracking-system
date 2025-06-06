from celery import shared_task
from django.utils import timezone

from .models import Loan
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task(name="send_overdue_reminders")
def send_overdue_reminders():
    today = timezone.now().date()
    overdue_loans = Loan.objects.filter(is_returned=False, due_date__lt=today).select_related("book", "member__user")
    if not overdue_loans.exists():
        return
    for loan in overdue_loans:
        try:
            member_email = loan.member.user.email
            book_title = loan.book.title
            send_mail(
                subject='Return Book',
                message=f'Hello {loan.member.user.username},\n\nReturn "{book_title}".\n the due date was {loan.due_date.strftime("%d %B, %Y")}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[member_email],
                fail_silently=False,
            )
        except Exception:
            pass