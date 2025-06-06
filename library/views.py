from datetime import timedelta

from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.response import Response

from library_system.settings import CustomPagination
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Book.objects.all().select_related("author")

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        due_date = Loan.calc_due_date()
        loan = Loan.objects.create(book=book, member=member, due_date=due_date)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=False, methods=["get"])
    def top_active(self, request, pk=None, url_path='top-active'):
        qs = Member.objects.annotate(
            active_loan_count=Count('loans', filter=Q(loans__is_returned=False))
        ).order_by('-active_loan_count').filter(active_loan_count__gt=0)
        data = []
        for member in qs:
            data.append({
                "member_id": member.id,
                "username": member.user.username,
                "email": member.user.email,
                "number_of_active_loans": member.active_loan_count
            })
        return Response(data)


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=["post"])
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()
        if loan.is_over_due():
            return Response({'error': 'Loan overdue.'}, status=status.HTTP_400_BAD_REQUEST)
        additional_days = request.data.get("additional_days")
        if not isinstance(additional_days, int):  # validation should be done in a serializer
            return Response({'error': 'additional days must be int.'}, status=422)
        loan.due_date = loan.due_date + timedelta(days=additional_days)
        loan.save()
        return Response(data=LoanSerializer(loan).data)
