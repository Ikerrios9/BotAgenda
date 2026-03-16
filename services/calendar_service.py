import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .config import CALENDAR_ID

# Si modificas estos 'scopes', debes borrar el archivo token.json para volver a autenticarte.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_calendar_service():
    """Muestra el uso básico de la API de Google Calendar.
    Crea y devuelve el servicio autenticado.
    """
    creds = None
    # El archivo token.json almacena los tokens de acceso y actualización del usuario,
    # y se crea automáticamente cuando el flujo de autorización se completa por primera vez.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # Si no hay credenciales (válidas) disponibles, permite al usuario iniciar sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Guarda las credenciales para la próxima vez que se ejecute el programa
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"Ha ocurrido un error al conectar con Calendar: {error}")
        return None

def create_calendar_event(title: str, start_time: str, end_time: str, description: str = ""):
    """
    Crea un evento en Google Calendar con un recordatorio "pop-up" de 30 minutos por defecto.
    Las horas deben ser cadenas de texto en formato ISO (isoformat).
    """
    service = get_calendar_service()
    if not service:
        return False, "Error de conexión con Google Calendar."

    event = {
      'summary': title,
      'description': description,
      'start': {
        'dateTime': start_time,
      },
      'end': {
        'dateTime': end_time,
      },
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'popup', 'minutes': 30},
        ],
      },
    }

    try:
        event_result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True, event_result.get('htmlLink')
    except HttpError as error:
        print(f"Ha ocurrido un error al crear el evento: {error}")
        return False, str(error)

if __name__ == "__main__":
    # Función de prueba
    get_calendar_service()

