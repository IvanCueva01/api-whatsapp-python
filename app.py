import os
from flask import Flask, request
from dotenv import load_dotenv
from flask_apscheduler import APScheduler  # Import APScheduler
import util
import whatsappservice
from openaiservice import GetAIResponse
from db_setup import init_db
import user_interaction_service  # Import the new service
import db_utils  # Import db_utils for conversation history

app = Flask(__name__)

# Configure APScheduler
app.config["SCHEDULER_API_ENABLED"] = True
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


init_db()  # Initializes the main messages.db for conversation history
# Initialize user_activity table if it doesn't exist (idempotent)

load_dotenv()

# Schedule the follow-up task


# minutes=1, misfire_grace_time=30 for testing
@scheduler.task('interval', id='send_follow_ups', hours=1, misfire_grace_time=900)
def scheduled_task_job():
    print("Scheduler is running follow_up_job")
    # with app.app_context(): # Not strictly needed if service doesn't use Flask features directly
    user_interaction_service.scheduled_follow_up_task()


@app.route('/welcome', methods=['GET'])
def index():
    return "Welcome developer"


@app.route('/whatsapp', methods=['GET'])
def VerifyToken():
    try:
        accessToken = os.getenv("WHATSAPP_ACCESS_TOKEN")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token != None and challenge != None and token == accessToken:
            return challenge
        return "", 400
    except ValueError:
        return "", 400


@app.route('/whatsapp', methods=['POST'])
def ReceivedMessage():
    try:
        body = request.get_json()
        print(body)

        entry = (body["entry"])[0]
        changes = (entry["changes"])[0]
        value = changes["value"]

        message = (value["messages"])[0]
        if not message:
            return "NO_MESSAGES"

        number = message["from"]
        text = util.GetTextUser(message)

        # Update user activity: this resets follow-up if user becomes active and hasn't booked.
        user_interaction_service.update_user_activity(number)

        # Check if we are pending a booking confirmation from the user
        if user_interaction_service.get_pending_booking_confirmation_status(number):
            user_interaction_service.clear_pending_booking_confirmation(
                number)  # Clear flag first
            if user_interaction_service.user_confirms_booking(text):
                user_interaction_service.set_meeting_booked_status(
                    number, booked=True)
                confirmation_booked_msg = "¡Excelente! Toda la información de la reunión agendada llegará al correo que registraste. ¡Te esperamos pronto!"
                whatsappservice.SendMessageWhatsapp(
                    util.TextMessage(confirmation_booked_msg, number))
                db_utils.save_message(
                    number, "assistant", confirmation_booked_msg)
                print(
                    f"User {number} confirmed booking after prompt. Follow-ups stopped.")
            else:
                # User did not confirm booking after being asked.
                # We can send a generic message or let GetAIResponse handle it.
                # For now, let ProcessMessage continue to get a standard AI response.
                print(
                    f"User {number} did not confirm booking after prompt. Proceeding with standard response.")
                # Optionally, send a message like: "Entendido. Si necesitas ayuda para agendar o tienes otra consulta, no dudes en preguntar."
                # For now, falling through to ProcessMessage for a general AI response.
            # In either case of pending confirmation, we've handled it, so proceed to ProcessMessage for user text or just return
            # If they confirmed booking, we might want to return EVENT_RECEIVED early.
            # Let's refine this: if they confirmed, we're done for this interaction.
            # Check again as flag was cleared
            if user_interaction_service.user_confirms_booking(text):
                return "EVENT_RECEIVED"

        # Check if the user is replying to a follow-up or explicitly states disinterest / confirms booking (initial)
        if user_interaction_service.is_user_explicitly_not_interested(text):
            user_interaction_service.mark_user_disinterested(number)
            # Optionally, send a confirmation like "Entendido. No recibirás más mensajes de seguimiento."
            # For now, just stop follow-ups silently based on this flag.
            print(
                f"User {number} marked as disinterested. No further processing for this message.")
            return "EVENT_RECEIVED"  # Stop further processing if user is not interested

        if user_interaction_service.user_confirms_booking(text):
            user_interaction_service.set_meeting_booked_status(
                number, booked=True)
            # Optionally, send a confirmation message through WhatsApp
            confirmation_booked_msg = "¡Excelente! Hemos registrado tu reunión. Recibirás los detalles en tu correo si proporcionaste uno al agendar. ¡Hasta pronto!"
            whatsappservice.SendMessageWhatsapp(
                util.TextMessage(confirmation_booked_msg, number))
            db_utils.save_message(number, "assistant", confirmation_booked_msg)
            print(f"User {number} confirmed booking. Follow-ups stopped.")
            return "EVENT_RECEIVED"  # Stop further processing if booking is confirmed here

        # NEW: Check if user indicates completion after potentially receiving contact info
        # This should ideally be checked if contact info was indeed provided in the *previous* turn.
        # For simplicity now, checking if their message is a common completion phrase.
        # A more robust check would involve knowing if the last bot message contained contact info.
        text_lower = text.lower()

        if user_interaction_service.user_indicates_completion_after_contact_info(text_lower):
            closing_message = "Entendido. ¡Que tengas un buen día!"
            whatsappservice.SendMessageWhatsapp(
                util.TextMessage(closing_message, number))
            db_utils.save_message(number, "assistant", closing_message)
            print(f"User {number} indicated conversation completion.")
            return "EVENT_RECEIVED"
        elif user_interaction_service.user_explicitly_requests_contact(text_lower):
            # If they are again asking for contact, let it proceed to ProcessMessage
            pass  # Let it go to ProcessMessage to get contact info again if needed

        ProcessMessage(text, number)
        print(text)
        return "EVENT_RECEIVED"
    except Exception as e:
        print(f"Webhook error: {e}")
        return "EVENT_RECEIVED"


def ProcessMessage(text, number):
    if not text or not number:
        return

    try:
        print(f"Mensaje recibido de {number}: {text}")
        text_lower = text.lower()  # Use a different variable for the lowercase version

        # conversation_history is not directly used here anymore as GetAIResponse fetches its own history.
        # conversation_history = db_utils.get_recent_messages(number)

        # Determine if the user is interested based on the current message or recent history
        # General interest can be used by AI for context, explicit request for contact details.
        # general_interest = user_interaction_service.user_shows_general_interest(text_lower)
        should_provide_contact = user_interaction_service.user_explicitly_requests_contact(
            text_lower)

        # Pass explicit request flag
        ai_response = GetAIResponse(text_lower, number, should_provide_contact)

        data = util.TextMessage(ai_response, number)
        whatsappservice.SendMessageWhatsapp(data)

        # Log messages
        db_utils.save_message(number, "assistant", ai_response)
        db_utils.save_message(number, "user", text)

        # If AI was prompted to give contact info and the response includes the meeting link, set pending confirmation
        if should_provide_contact and "meetings.hubspot.com/angel40" in ai_response:
            user_interaction_service.set_meeting_link_offered(number)

        # The primary way to detect booking is if the user explicitly states it
        # in a message, which is handled at the beginning of ReceivedMessage.
        # The AI will offer the link if user_is_interested. If the user books and then confirms
        # in a subsequent message, it will be caught by user_confirms_booking.

    except Exception as e:
        print(f"Error procesando mensaje de {number}: {e}")


# Generate message is for testing


def GenerateMessage(text, number):

    text_lower = text.lower()  # Use a different variable for the lowercase version
    if "text" in text_lower:
        data = util.TextMessage("Text", number)
    elif "format" in text_lower:
        data = util.TextFormatMessage(number)
    elif "image" in text_lower:
        data = util.ImageMessage(number)
    elif "video" in text_lower:
        data = util.VideoMessage(number)
    elif "audio" in text_lower:
        data = util.AudioMessage(number)
    elif "document" in text_lower:
        data = util.DocumentMessage(number)
    elif "location" in text_lower:
        data = util.LocationMessage(number)
    elif "button" in text_lower:
        data = util.ButtonsMessage(number)
    elif "list" in text_lower:
        data = util.ListMessage(number)
    else:
        data = None  # Ensure data is None if no condition is met

    if data:  # Check if data is not None before sending
        whatsappservice.SendMessageWhatsapp(data)


if (__name__ == "__main__"):
    # Added debug=True and use_reloader=False for scheduler
    app.run(debug=True, use_reloader=False)
