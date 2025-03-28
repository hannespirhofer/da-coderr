from json import JSONEncoder
from urllib import response
from django.db import IntegrityError
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated

from market.permissions import isOwnerOr405
from market.models import MarketUser
from market.serializers import MarketUserRegisterSerializer, MarketUserShortSerializer, MarketUserSerializer


class RegisterView(APIView):
    def post(self, request):
        serializer = MarketUserRegisterSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status = HTTP_400_BAD_REQUEST)
        market_user = serializer.save()
        serializer = MarketUserShortSerializer(market_user)

        username = serializer.data.get('username', None)
        if username is None:
            return Response('Error.', status = HTTP_400_BAD_REQUEST)

        user = User.objects.get(username = username)
        token, created = Token.objects.get_or_create(user = user)

        response = serializer.data
        response.update({'token': token.key})

        return Response(response, status = HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username', None)
        password = request.data.get('password', None)

        if username is None or password is None:
            return Response(
                {'error': 'Please submit username and password'},
                status = HTTP_400_BAD_REQUEST
            )
        user = authenticate(username = username, password = password)
        if user:
            [token, created] = Token.objects.get_or_create(user = user)
            return Response({
                'token': token.key,
                'username': username,
                'email': user.email,
                'user_id': user.id,
                }, status = HTTP_201_CREATED)
        else:
            return Response({'error': 'Wrong credentials.'}, status = HTTP_400_BAD_REQUEST)

class ProfileDetailView(RetrieveUpdateAPIView):
    serializer_class = MarketUserSerializer
    http_method_names = ['get', 'patch']
    permission_classes = [IsAuthenticated, isOwnerOr405]

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        queryset = MarketUser.objects.filter(pk=pk)
        return queryset

class CustomerListView(ListAPIView):
    serializer_class = MarketUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MarketUser.objects.filter(type='customer')

class BusinessListView(ListAPIView):
    serializer_class = MarketUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MarketUser.objects.filter(type='business')




