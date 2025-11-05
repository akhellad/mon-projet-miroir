from rest_framework import serializers
from .models import User
from .utils import generate_secure_password, validate_password_strength


class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les données utilisateur (sans informations sensibles).
    """
    is_admin = serializers.BooleanField(read_only=True)
    is_contributeur = serializers.BooleanField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'is_admin', 'is_contributeur',
            'must_change_password', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class LoginSerializer(serializers.Serializer):
    """
    Sérialiseur pour la requête de login.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """
    Sérialiseur pour la requête de refresh token.
    """
    refresh_token = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    """
    Sérialiseur pour la réponse de login.
    """
    user = UserSerializer()
    tokens = serializers.DictField()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'utilisateur.

    Le mot de passe est généré automatiquement de manière sécurisée (20+ caractères).
    L'utilisateur devra le changer à sa première connexion.
    """
    # Le mot de passe généré sera retourné dans la réponse
    generated_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'generated_password'
        ]

    def create(self, validated_data):
        """
        Créer un utilisateur avec un mot de passe auto-généré.
        """
        # Générer un mot de passe sécurisé
        password = generate_secure_password(20)

        # Créer l'utilisateur
        user = User.objects.create(
            **validated_data,
            must_change_password=True  # Forcer le changement à la première connexion
        )
        user.set_password(password)
        user.save()

        # Stocker le mot de passe généré pour le retourner (seulement dans la réponse)
        user.generated_password = password

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la modification d'utilisateur.
    Le mot de passe est optionnel mais doit respecter les critères de sécurité (20 caractères minimum).
    """
    password = serializers.CharField(write_only=True, required=False, min_length=20)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'password', 'password_confirm'
        ]

    def validate(self, data):
        """
        Vérifier que les mots de passe correspondent et respectent les critères de sécurité.
        """
        password = data.get('password')
        password_confirm = data.get('password_confirm')

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({
                    'password_confirm': 'Les mots de passe ne correspondent pas.'
                })

            # Valider la force du mot de passe
            if password:
                is_valid, error_message = validate_password_strength(password)
                if not is_valid:
                    raise serializers.ValidationError({
                        'password': error_message
                    })

        return data

    def update(self, instance, validated_data):
        """
        Mettre à jour l'utilisateur avec un mot de passe hashé si fourni.
        """
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        # Mettre à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Mettre à jour le mot de passe si fourni
        if password:
            instance.set_password(password)
            # Réinitialiser le flag de changement obligatoire
            instance.must_change_password = False

        instance.save()
        return instance
