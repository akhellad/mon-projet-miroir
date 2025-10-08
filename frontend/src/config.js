// Configuration de l'application
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // Utilise le même hôte que celui du frontend mais sur le port 8000
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

export const API_BASE_URL = getApiBaseUrl();
