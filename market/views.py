from json import JSONEncoder
from urllib import response
from django.db import IntegrityError
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from market.pagination import CustomPagination
from market.filters import OfferFilter
from market.permissions import isOwnerOr405, IsBusiness, isOfferOwner
from market.models import MarketUser, Offer, OfferDetail, Order
from market.serializers import MarketUserRegisterSerializer, MarketUserShortSerializer, MarketUserSerializer, OfferDetailSerializer, OfferWriteSerializer, OfferReadSerializer, OfferListSerializer, OrderSerializer


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

class OfferViewset(ModelViewSet):
    serializer_class = OfferReadSerializer
    queryset = Offer.objects.all()
    filterset_class = OfferFilter
    ordering_fields = ['updated_at', 'min_price']
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return OfferWriteSerializer
        if self.action in ['list', 'retrieve']:
            return OfferListSerializer
        return OfferReadSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsBusiness(), isOfferOwner()]

    def get_serializer_context(self):
        is_list_action = self.action == 'list'
        context = super().get_serializer_context()
        if is_list_action:
            context['request'] = None #disable absolute urls
        return context

    def perform_create(self, serializer):
        marketuser = MarketUser.objects.get(user=self.request.user)
        serializer.save(user=marketuser)

class OfferDetailView(RetrieveAPIView):
    serializer_class = OfferDetailSerializer
    queryset = OfferDetail.objects.all()
    permission_classes = [IsAuthenticated]

class OrderViewset(ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()


