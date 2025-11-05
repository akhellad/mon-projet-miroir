"""
Utilitaires pour l'authentification
"""
import secrets
import string


def generate_secure_password(length=20):
    """
    Génère un mot de passe sécurisé aléatoire.

    Le mot de passe contient :
    - Au moins 20 caractères (par défaut)
    - Des lettres majuscules
    - Des lettres minuscules
    - Des chiffres
    - Des caractères spéciaux

    Args:
        length: Longueur du mot de passe (minimum 20)

    Returns:
        str: Mot de passe généré
    """
    if length < 20:
        length = 20

    # Définir les caractères disponibles
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # S'assurer qu'au moins un caractère de chaque type est présent
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Remplir le reste avec des caractères aléatoires
    all_chars = lowercase + uppercase + digits + special
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Mélanger pour éviter un pattern prévisible
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return ''.join(password_list)


def validate_password_strength(password):
    """
    Valide la force d'un mot de passe.

    Règles :
    - Minimum 20 caractères
    - Au moins une lettre majuscule
    - Au moins une lettre minuscule
    - Au moins un chiffre
    - Au moins un caractère spécial

    Args:
        password: Mot de passe à valider

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 20:
        return False, "Le mot de passe doit contenir au moins 20 caractères"

    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule"

    if not any(c.islower() for c in password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule"

    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"

    special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%...)"

    return True, None
