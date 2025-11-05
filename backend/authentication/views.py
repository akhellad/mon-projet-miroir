from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .services.auth_service import AuthService
from .serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer
)
from .models import User
from .permissions import IsAdmin


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint de connexion.

    POST /api/auth/login/
    Body: {
        "username": "admin",
        "password": "password123"
    }

    Response: {
        "user": {...},
        "tokens": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 28800
        }
    }
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Données invalides', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    success, data, error = AuthService.login(username, password)

    if not success:
        return Response(
            {'error': error},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Endpoint de rafraîchissement de token.

    POST /api/auth/refresh/
    Body: {
        "refresh_token": "eyJ..."
    }

    Response: {
        "access_token": "eyJ...",
        "token_type": "Bearer",
        "expires_in": 28800
    }
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Données invalides', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    refresh_token = serializer.validated_data['refresh_token']
    success, token_data, error = AuthService.refresh(refresh_token)

    if not success:
        return Response(
            {'error': error},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(token_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Endpoint de déconnexion.

    POST /api/auth/logout/
    Body: {
        "refresh_token": "eyJ..."
    }
    Headers: {
        "Authorization": "Bearer <access_token>" (optionnel)
    }

    Response: {
        "message": "Déconnexion réussie"
    }

    Note: AllowAny permet la déconnexion même avec un token expiré,
    ce qui est important pour le UX. Le refresh_token est utilisé
    pour la révocation côté serveur.
    """
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response(
            {'error': 'Refresh token requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    success = AuthService.logout(refresh_token)

    if not success:
        return Response(
            {'warning': 'Token déjà révoqué ou invalide'},
            status=status.HTTP_200_OK
        )

    return Response(
        {'message': 'Déconnexion réussie'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Endpoint pour récupérer les informations de l'utilisateur connecté.

    GET /api/auth/me/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }

    Response: {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "role_display": "Administrateur",
        "is_admin": true,
        "is_contributeur": true,
        ...
    }
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Endpoint pour mettre à jour son propre profil.

    PUT/PATCH /api/auth/profile/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }
    Body: {
        "email": "newemail@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "newpassword123",  // Optionnel
        "password_confirm": "newpassword123"  // Requis si password fourni
    }

    Response: {
        "id": 1,
        "username": "admin",
        "email": "newemail@example.com",
        ...
    }

    Note: Les utilisateurs ne peuvent pas modifier leur username ou role
    """
    user = request.user
    partial = request.method == 'PATCH'

    # Créer une copie des données sans username et role (non modifiables)
    data = request.data.copy()
    data.pop('username', None)
    data.pop('role', None)
    data.pop('is_active', None)  # Les utilisateurs ne peuvent pas se désactiver

    serializer = UserUpdateSerializer(user, data=data, partial=partial)

    if not serializer.is_valid():
        return Response(
            {'error': 'Données invalides', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    updated_user = serializer.save()
    response_serializer = UserSerializer(updated_user)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def accept_password_view(request):
    """
    Endpoint pour accepter le mot de passe généré automatiquement.

    PATCH /api/auth/profile/accept-password/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }

    Response: {
        "message": "Mot de passe accepté avec succès"
    }

    Met must_change_password à False pour permettre l'accès à l'application
    sans changer le mot de passe généré.
    """
    user = request.user

    # Marquer que l'utilisateur a accepté son mot de passe
    user.must_change_password = False
    user.save()

    return Response(
        {'message': 'Mot de passe accepté avec succès'},
        status=status.HTTP_200_OK
    )


# ============================================================================
# ENDPOINTS DE GESTION DES UTILISATEURS (Admin uniquement)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAdmin])
def users_list_view(request):
    """
    Liste tous les utilisateurs (Admin uniquement).

    GET /api/auth/users/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }

    Query params (optionnels):
        - role: Filtrer par rôle (admin, contributeur, lecteur)
        - search: Rechercher par username, email, first_name, last_name

    Response: [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            ...
        },
        ...
    ]
    """
    users = User.objects.all().order_by('-date_joined')

    # Filtrage par rôle
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)

    # Recherche
    search = request.query_params.get('search')
    if search:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def user_detail_view(request, user_id):
    """
    Récupère les détails d'un utilisateur (Admin uniquement).

    GET /api/auth/users/{user_id}/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }

    Response: {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        ...
    }
    """
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdmin])
def user_create_view(request):
    """
    Crée un nouvel utilisateur (Admin uniquement).

    POST /api/auth/users/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }
    Body: {
        "username": "newuser",
        "email": "newuser@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "lecteur",
        "password": "password123",
        "password_confirm": "password123"
    }

    Response: {
        "id": 2,
        "username": "newuser",
        "email": "newuser@example.com",
        "role": "lecteur",
        ...
    }
    """
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Données invalides', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = serializer.save()

    # Retourner les données de l'utilisateur avec le mot de passe généré
    response_data = UserSerializer(user).data
    response_data['generated_password'] = user.generated_password

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdmin])
def user_update_view(request, user_id):
    """
    Met à jour un utilisateur (Admin uniquement).

    PUT/PATCH /api/auth/users/{user_id}/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }
    Body: {
        "email": "newemail@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "contributeur",
        "is_active": true,
        "password": "newpassword123",  // Optionnel
        "password_confirm": "newpassword123"  // Requis si password fourni
    }

    Response: {
        "id": 2,
        "username": "newuser",
        "email": "newemail@example.com",
        "role": "contributeur",
        ...
    }
    """
    user = get_object_or_404(User, id=user_id)

    # Empêcher un admin de se désactiver lui-même
    if user.id == request.user.id and request.data.get('is_active') is False:
        return Response(
            {'error': 'Vous ne pouvez pas désactiver votre propre compte'},
            status=status.HTTP_400_BAD_REQUEST
        )

    partial = request.method == 'PATCH'
    serializer = UserUpdateSerializer(user, data=request.data, partial=partial)

    if not serializer.is_valid():
        return Response(
            {'error': 'Données invalides', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    updated_user = serializer.save()
    response_serializer = UserSerializer(updated_user)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdmin])
def user_delete_view(request, user_id):
    """
    Supprime un utilisateur (Admin uniquement).

    DELETE /api/auth/users/{user_id}/
    Headers: {
        "Authorization": "Bearer <access_token>"
    }

    Response: {
        "message": "Utilisateur supprimé avec succès"
    }
    """
    user = get_object_or_404(User, id=user_id)

    # Empêcher un admin de se supprimer lui-même
    if user.id == request.user.id:
        return Response(
            {'error': 'Vous ne pouvez pas supprimer votre propre compte'},
            status=status.HTTP_400_BAD_REQUEST
        )

    username = user.username
    user.delete()

    return Response(
        {'message': f'Utilisateur "{username}" supprimé avec succès'},
        status=status.HTTP_200_OK
    )
