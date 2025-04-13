from django.contrib.auth.models import User
from rest_framework import serializers
from market.models import MarketUser, Offer, OfferDetail, Order

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class MarketUserShortSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.CharField(source='pk', read_only=True)
    class Meta:
        model = MarketUser
        fields = ('username', 'email', 'user_id')

class MarketUserOfferSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    class Meta:
        model = MarketUser
        fields = ('username', 'first_name', 'last_name')

class MarketUserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = MarketUser
        fields = ['username','email','password','repeated_password','type']

    def validate(self, data):
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(username = data["username"]).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return data

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('repeated_password')

        user = User.objects.create_user(username = username, password = password, email = email)
        market_user = MarketUser.objects.create(user = user, **validated_data)
        return market_user

class MarketUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')
    user = serializers.SerializerMethodField()

    class Meta:
        model = MarketUser
        fields = [
            'user',
            'username',
            'first_name',
            'last_name',
            'file',
            'location',
            'tel',
            'description',
            'working_hours',
            'type',
            'email',
            'created_at'
        ]

    def get_user(self, obj):
        return obj.pk

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        email = user_data.get('email', None)
        instance = super().update(instance, validated_data)
        if email:
            instance.user.email = email
            instance.user.save()
        return instance






class OfferDetailHyperLinkSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='offerdetail',
        lookup_field='pk'
    )
    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        # fields = '__all__'
        exclude = ['offer']

class OfferWriteSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"

    def create(self, validated_data):
        details = validated_data.pop('details', [])
        offer = Offer.objects.create(**validated_data)
        for d in details:
            OfferDetail.objects.create(offer=offer, **d)
        return offer

class OfferReadSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    user_details = MarketUserOfferSerializer(source='user', read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"

class OfferListSerializer(serializers.ModelSerializer):
    details = OfferDetailHyperLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"