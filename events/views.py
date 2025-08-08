from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Event
from .serializers import EventSerializer

class EventListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        event_type = request.query_params.get("type")
        if event_type == "created":
            events = Event.objects.filter(created_by=request.user)
        elif event_type == "registered":
            events = Event.objects.filter(participants=request.user)
        else:
            events = Event.objects.all()

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Validate future date
        event_date_str = request.data.get("date")
        if event_date_str:
            event_date = timezone.datetime.fromisoformat(
                event_date_str.replace("Z", "+00:00")
            )
            if event_date <= timezone.now():
                raise ValidationError({"date": "Event date must be in the future."})

        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventRegisterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        # Prevent registering for past events
        if event.date <= timezone.now():
            return Response(
                {"message": "You cannot register for a past event."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent duplicate registration
        if request.user in event.participants.all():
            return Response(
                {"message": "You are already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.participants.add(request.user)
        return Response(
            {"message": f"Registered for event '{event.title}'"},
            status=status.HTTP_200_OK
        )
