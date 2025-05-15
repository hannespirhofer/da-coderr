from urllib import response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from django.db.models import Q

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
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        try:
            marketuser = MarketUser.objects.get(user=self.request.user)
        except MarketUser.DoesNotExist:
            return Order.objects.none()
        return Order.objects.filter(
            Q(customer_user=marketuser) | Q(business_user=marketuser)
        )

    def create(self, request, *args, **kwargs):
        try:
            offerdetail = OfferDetail.objects.get(id=request.data["offer_detail_id"])
        except OfferDetail.DoesNotExist:
            return Response({'error': 'Offerdetail not found.'}, status=HTTP_400_BAD_REQUEST)

        try:
            marketuser = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            return Response({'error': 'Only MarketUser are allowed to create Orders.'}, status=HTTP_400_BAD_REQUEST)

        if marketuser.type != "customer":
            return Response({'error': 'Only Customers are allowed to create Orders.'}, status=HTTP_403_FORBIDDEN)


        order = Order.objects.create(
            offerdetail = offerdetail,
            customer_user=marketuser,
            business_user=offerdetail.offer.user,
            status="in progress"
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        order_id = self.kwargs.get('pk')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=HTTP_400_BAD_REQUEST)

        try:
            marketuser = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            return Response({'error': 'MarketUser not found.'}, status=HTTP_400_BAD_REQUEST)

        if order.customer_user != marketuser:
            return Response({'error': 'You are not the owner and cannot perform update on this order.'}, status=HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        order_id = self.kwargs.get('pk')

        if not request.user.is_superuser:
            return Response({'error': 'Only admin can perform this action.'}, status=HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, id=order_id)
        order.delete()

        return Response(status=HTTP_204_NO_CONTENT)

class BusinessOrderCount(APIView):
    permission_classes = [IsAuthenticated, IsBusiness]

    def get(self, request, *args, **kwargs):
        business_user_id = kwargs.get('pk')

        try:
            business_user = MarketUser.objects.get(pk=business_user_id)
        except MarketUser.DoesNotExist:
            return Response({"error": "No business user found with this id."}, status=HTTP_404_NOT_FOUND)

        orders_count = Order.objects.filter(Q(status="in progress") & Q(business_user__pk=business_user_id)).count()
        return Response({"order_count": orders_count}, status=HTTP_200_OK)


