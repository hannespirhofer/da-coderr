import pdb
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.exceptions import NotFound, PermissionDenied, NotAcceptable, ParseError, AuthenticationFailed
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from django.db.models import Q, Avg

from market.pagination import CustomPagination
from market.filters import OfferFilter
from market.permissions import IsCustomer, isOwnerOr405, IsBusiness, isOfferOwner
from market.models import MarketUser, Offer, OfferDetail, Order, Review
from market.serializers import MarketUserRegisterSerializer, MarketUserShortSerializer, MarketUserSerializer, OfferDetailSerializer, OfferWriteSerializer, OfferReadSerializer, OfferListSerializer, OrderSerializer, ReviewSerializer, ReviewWriteSerializer, OfferReadAfterWriteSerializer


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
    
    def get(self, request, *args, **kwargs):
        market_userid = kwargs.get("pk")

        if market_userid is not None:
            try:
                marketuser = MarketUser.objects.get(pk=market_userid)
            except MarketUser.DoesNotExist:
                raise NotFound('User dont exist', code=HTTP_404_NOT_FOUND)
        
        data = self.get_serializer(instance=marketuser)
        return Response(data.data, status=HTTP_200_OK)


class CustomerListView(ListAPIView):
    serializer_class = MarketUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MarketUser.objects.filter(type='customer')
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for item in response.data:
            item.pop('email', None)
            item.pop('created_at', None)
        return response


class BusinessListView(ListAPIView):
    serializer_class = MarketUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MarketUser.objects.filter(type='business')
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for item in response.data:
            item.pop('email', None)
            item.pop('created_at', None)
        return response


class OfferViewset(ModelViewSet):
    # serializer_class = OfferReadSerializer
    queryset = Offer.objects.all()
    filterset_class = OfferFilter
    ordering_fields = ['updated_at', 'min_price']
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'description']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return OfferWriteSerializer
        if self.action in ['list', 'retrieve']:
            return OfferListSerializer
        if self.action == 'update':
            raise PermissionDenied('PUT not allowed', code=HTTP_403_FORBIDDEN)
        return OfferReadSerializer

    def get_permissions(self):
        if self.action in ['list']:
            return [AllowAny()]
        if self.action in ['retrieve']:
            return [IsAuthenticated()]
        if self.action in ['create']:
            return [IsAuthenticated(), IsBusiness()]
        return [IsAuthenticated(), IsBusiness(), isOfferOwner()]
    

    def get_serializer_context(self):
        is_list_action = self.action == 'list'
        context = super().get_serializer_context()
        if is_list_action:
            context['request'] = None #disable absolute urls
        return context
    
    def create(self, request, *args, **kwargs):
        marketuser = MarketUser.objects.get(user=self.request.user)
        details = request.data.pop('details', None)
        
        # Abort early if details not ok
        if len(details) != 3:
            raise ParseError('Details must be a list with 3 items.')
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid() is False:
            raise ParseError('Offer Data is wrong.')

        serializer.save(user=marketuser)
        
        #handle details - validate and save them to the instance
        if details is not None:
            for detail in details:
                detailserializer = OfferDetailSerializer(data=detail)
                detailserializer.is_valid(raise_exception=True)
                detailserializer.save(offer=serializer.instance)

        # get new serializer and send this data back
        res_serializer = OfferReadAfterWriteSerializer(serializer.instance)
        return Response(res_serializer.data, status=HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):
        marketuser = MarketUser.objects.get(user=self.request.user)
        details = request.data.pop('details', None)
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)

        #handle details - validate and save them to the instance
        if details is not None:
            offer_types = []
            for detail in details:
                if 'offer_type' in detail:
                    offer_types.append(detail['offer_type'])
            
            # get the offer - filter the respective details which needs an update
            offer = self.get_object()
            offer_details = OfferDetail.objects.filter(
                Q(offer=offer) & Q(offer_type__in = offer_types)
            )

            # loop the patch list
            type_map = {d.offer_type: d for d in offer_details}
            for patchdetail in details:
                instance = type_map.get(patchdetail['offer_type'])
                detailserializer = OfferDetailSerializer(instance, data=patchdetail, partial=True)
                detailserializer.is_valid(raise_exception=True)
                detailserializer.save()


        # proceed with the offer
        serializer.is_valid(raise_exception=True)
        serializer.save(user=marketuser)
        # get new serializer and send this data back
        res_serializer = OfferReadAfterWriteSerializer(serializer.instance)
        return Response(res_serializer.data, status=HTTP_200_OK)


class OfferDetailView(RetrieveAPIView):
    serializer_class = OfferDetailSerializer
    queryset = OfferDetail.objects.all()


class OrderViewset(ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            marketuser = MarketUser.objects.get(user=self.request.user)
        except MarketUser.DoesNotExist:
            return Order.objects.none()
        return Order.objects.filter(
            Q(customer_user=marketuser) | Q(business_user=marketuser)
        )

    def create(self, request, *args, **kwargs):
        detailid = request.data.get("offer_detail_id", None)

        if detailid is None or not isinstance(detailid, int):
            raise ParseError('Only numbers allowed.')

        try:
            offerdetail = OfferDetail.objects.get(id=detailid)
        except OfferDetail.DoesNotExist:
            raise NotFound('Offerdetail not found.')

        try:
            marketuser = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            raise NotFound('User not found.')

        if marketuser.type != "customer":
            return PermissionDenied('Only Customers are allowed to create Orders.')


        order = Order.objects.create(
            offerdetail = offerdetail,
            customer_user=marketuser,
            business_user=offerdetail.offer.user,
            status="in_progress"
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        order_id = self.kwargs.get('pk')

        if order_id is not None:
            try:
                order_id = int(order_id)
            except ValueError:
                raise ParseError('Order pk must be an int')

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise NotFound('Order not found.')

        try:
            marketuser = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            raise NotFound('User not found.')

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
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        business_user_id = kwargs.get('pk')

        try:
            business_user = MarketUser.objects.get(pk=business_user_id)
        except MarketUser.DoesNotExist:
            return Response({"error": "No user found with this id."}, status=HTTP_404_NOT_FOUND)

        orders_count = Order.objects.filter(Q(status="in_progress") & Q(business_user__pk=business_user_id)).count()
        return Response({"order_count": orders_count}, status=HTTP_200_OK)


class BusinessCompletedOrderCount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        business_user_id = kwargs.get('pk')

        try:
            business_user = MarketUser.objects.get(pk=business_user_id)
        except MarketUser.DoesNotExist:
            return Response({"error": "No business user found with this id."}, status=HTTP_404_NOT_FOUND)

        orders_count = Order.objects.filter(Q(status="completed") & Q(business_user__pk=business_user_id)).count()
        return Response({"completed_order_count": orders_count}, status=HTTP_200_OK)


class ReviewViewset(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')
        ordering = self.request.query_params.get('ordering')

        q = Q()
        if (business_user_id is not None):
            q &= Q(business_user=business_user_id)
        if (reviewer_id is not None):
            q &= Q(reviewer=reviewer_id)

        queryset = Review.objects.filter(q)

        if ordering and ordering in ["updated_at", "rating"]:
            queryset = queryset.order_by(ordering)

        return queryset


    def get_serializer_class(self):
        if (self.action in ['create', 'update', 'partial_update']):
            return ReviewWriteSerializer
        return ReviewSerializer

    def create(self, request, *args, **kwargs):
        try:
            reviewer = MarketUser.objects.get(user=request.user)
        except MarketUser.DoesNotExist:
            raise ParseError('No customer account found with this id.')

        if reviewer.type != 'customer':
            raise AuthenticationFailed('Only customers can leave reviews')

        try:
            business_user = MarketUser.objects.get(pk=request.data.get("business_user"))
        except MarketUser.DoesNotExist:
            raise ParseError('No business account found with this id.')

        reviews = Review.objects.filter(business_user=business_user.pk, reviewer=reviewer.pk)
        if len(reviews) >= 1:
            raise PermissionDenied("You already made a review on this user. Delete or patch this one.")

        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(reviewer=reviewer)

        full_review = ReviewSerializer(review).data

        return Response(full_review, status=HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        review_id = self.kwargs.get("pk")
        request.data.pop("business_user", None)

        if review_id is not None:
            try:
                review = Review.objects.get(pk=review_id)
            except Review.DoesNotExist:
                raise ParseError('Review not found')
        
        try:
            request_marketuser = MarketUser.objects.get(user=self.request.user)
        except MarketUser.DoesNotExist:
            raise ParseError('Profile not found.')
        
        review_user = review.reviewer
        if not review_user:
            raise NotFound('Reviewer not found', code=HTTP_400_BAD_REQUEST)
        
        if request_marketuser != review_user:
            raise PermissionDenied('Only Creators can update the review', code=HTTP_403_FORBIDDEN)
        
        # checks passed - update/patch the instance

        serializer = self.get_serializer(review, data=self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        review_full = ReviewSerializer(review)

        return Response(review_full.data, status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        try:
            review = Review.objects.get(pk=self.kwargs.get("pk"))
        except Review.DoesNotExist:
            raise NotFound('Review not found', code=HTTP_400_BAD_REQUEST)
        
        request_marketuser = MarketUser.objects.get(pk=self.request.user.pk)

        if review.reviewer != request_marketuser:
            raise PermissionDenied('Only Creator can perform this action', code=HTTP_403_FORBIDDEN)
        
        review.delete()

        return Response('Review deleted', status=HTTP_204_NO_CONTENT)


class BaseInfoView(APIView):

    def get(self, request, format=None):
        review_count = Review.objects.count()
        average_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
        business_profile_count = MarketUser.objects.filter(type='business').count()
        offer_count = Offer.objects.count()

        data_dict = {k: locals()[k] for k in ["review_count", "average_rating", "business_profile_count", "offer_count"]}
        return Response(data_dict, status=HTTP_200_OK)


