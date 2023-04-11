from django.shortcuts import render

# Create your views here.
#### 1
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer,UserProfileSerializer
#### 2
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

#### view

def generate_token_in_serialized_data(user:User, user_profile:UserProfile) -> UserSerializer.data:
    token = RefreshToken.for_user(user)
    refresh_token, access_token = str(token), str(token.access_token)
    serialized_data = UserProfileSerializer(user_profile).data
    serialized_data['token']={"access":access_token, "refresh":refresh_token}
    return serialized_data

def set_token_on_response_cookie(user: User) -> Response:
    token = RefreshToken.for_user(user)
    user_profile = UserProfile.objects.get(user=user)
    user_profile_serializer = UserProfileSerializer(user_profile)
    res = Response(user_profile_serializer.data, status=status.HTTP_200_OK)
    res.set_cookie('refresh_token', value=str(token), httponly=True)
    res.set_cookie('access_token', value=str(token.access_token), httponly=True)
    return res

class SignupView(APIView):
    def post(self, request):
        college=request.data.get('college')
        major=request.data.get('major')
        user_serialier = UserSerializer(data=request.data)
        if user_serialier.is_valid(raise_exception=True):
            user = user_serialier.save()
            
        user_profile = UserProfile.objects.create(
            user=user,
            college=college,
            major=major
        )
        return set_token_on_response_cookie(user)


class SigninView(APIView):
    def post(self, request):
        try:
            user = User.objects.get(
                username=request.data['username'],
                password=request.data['password']
            )
        except:
            return Response({"detail": "아이디 또는 비밀번호를 확인해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        return set_token_on_response_cookie(user)

class LogoutView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인 후 다시 시도해주세요."}, status=status.HTTP_401_UNAUTHORIZED)
        RefreshToken(request.data['refresh']).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RefreshView(APIView):
    def post(self, request):
        try:
            refreshtoken = request.data['refresh']
        except: 
            return Response({"error: invalid token"}, stattus=status.HTTP_400_BAD_REQUEST)
        new_access_token = RefreshToken(refreshtoken).access_token
        res = Response(status=status.HTTP_200_OK)
        res.set_cookie('access_token', value=str(new_access_token), httponly=True)
        return res