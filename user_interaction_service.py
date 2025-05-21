import time
import sqlite3
import util
import whatsappservice

DATABASE_NAME = "messages.db"

# Follow-up configuration
FOLLOW_UP_MESSAGES = {
    1: "¡Hola! Solo quería confirmar si tuviste oportunidad de revisar la información que te envié. ¿Te gustaría que lo veamos juntos en una llamada?",
    2: "Estoy disponible si deseas avanzar con la solución M2M. ¿Quieres que te ayudemos con una propuesta o demos?",
    3: "Este será mi último mensaje. Si en otro momento deseas conectar tus dispositivos con una solución profesional y confiable, aquí estaré para ayudarte."
}
# Intervals for follow-ups, in seconds.
# Stage 1: 24 hours after last activity if no follow-up sent.
# Stage 2: 72 hours after Stage 1 follow-up.
# Stage 3: 168 hours (7 days) after Stage 2 follow-up.
FOLLOW_UP_INTERVALS_SECONDS = {
    1: 24 * 60 * 60,    # 60 for testing
    2: 3 * 24 * 60 * 60,  # 120 for testing
    3: 7 * 24 * 60 * 60   # 180 for testing
}
MAX_FOLLOW_UPS = 3  # Max number of follow-up messages to send


def connect_db():
    """Connects to the SQLite database."""
    return sqlite3.connect(DATABASE_NAME)


def user_shows_general_interest(text):
    """
    Determines if the user's message indicates general interest in services.
    Used for guiding AI response detail and tone.
    """
    general_interest_keywords = [
        "contratar", "precio", "costo", "información", "más detalles", "info",
        "asesor", "comprar", "adquirir", "ayuda", "soporte",
        "interesado", "cotización", "propuesta", "sí", "ok", "vale", "claro", "quisiera saber",
        "beneficios", "cómo funciona", "qué ofrecen", "cuánto cuesta", "me gustaría"
    ]
    text_lower = text.lower()
    for keyword in general_interest_keywords:
        if keyword in text_lower:
            return True
    return False


def user_explicitly_requests_contact(text):
    """
    Determines if the user's message explicitly requests contact or a meeting.
    This is the primary trigger for providing contact details.
    """
    contact_request_keywords = [
        "agendar reunión", "programar reunión", "quiero una reunión", "necesito una reunión",
        "contactar asesor", "hablar con asesor", "llamar a un asesor", "quiero llamar",
        "programar cita", "agendar llamada", "necesito ayuda para agendar",
        "cómo agendo", "cómo contacto", "dame el teléfono", "número de contacto"
    ]
    text_lower = text.lower()
    for keyword in contact_request_keywords:
        if keyword in text_lower:
            return True
    return False


def user_indicates_completion_after_contact_info(text):
    """
    Determines if the user's message indicates they have what they need 
    after contact info was likely provided, and the conversation can end.
    """
    completion_keywords = [
        "ya tengo el número", "gracias por el número", "listo con el contacto",
        "eso es todo gracias", "no necesito más por ahora", "muy amable, gracias",
        "ok, gracias", "perfecto, gracias", "entendido, gracias", "ya está",
        "suficiente", "gracias"
        # Adding just "gracias" is broad, but in context after contact info, it often means completion.
        # We can refine this if it's too aggressive.
    ]
    text_lower = text.lower()
    # Check for slightly longer phrases first to avoid overly broad matches with just "gracias"
    for keyword in [k for k in completion_keywords if len(k.split()) > 1]:
        if keyword in text_lower:
            return True
    # Then check for standalone "gracias" or similar short confirmations
    if text_lower == "gracias" or text_lower == "ok gracias" or text_lower == "listo gracias":
        return True
    return False


def is_user_explicitly_not_interested(text):
    """
    Determines if the user's message explicitly states disinterest.
    Used to stop follow-ups.
    """
    not_interested_keywords = [
        "no gracias", "no estoy interesado", "no me interesa", "detener", "cancelar",
        "no más mensajes", "ya no", "no necesito", "equivocado"
    ]
    text_lower = text.lower()
    for keyword in not_interested_keywords:
        if keyword in text_lower:
            return True
    return False


def user_confirms_booking(text):
    """
    Checks if the user's text confirms they have booked a meeting.
    """
    confirmation_keywords = [
        "agendado", "ya agendé", "listo", "confirmado", "cita hecha", "reunión lista",
        "sí, pude", "logré agendar", "correcto, agendado"
    ]
    text_lower = text.lower()
    for keyword in confirmation_keywords:
        if keyword in text_lower:
            return True
    return False


def update_user_activity(user_id, is_initial_contact=False):
    """
    Updates the last activity timestamp for a user.
    If the user becomes active and hasn't booked a meeting, reset follow-up stage.
    """
    conn = connect_db()
    cursor = conn.cursor()
    current_time = int(time.time())
    try:
        cursor.execute(
            "SELECT meeting_booked_status, follow_up_stage FROM user_activity WHERE user_id = ?", (user_id,))
        user_status = cursor.fetchone()

        meeting_booked = user_status[0] if user_status else 0

        if not meeting_booked:  # Only reset follow-up if no meeting is booked
            # For a new interaction or if user re-engages, reset follow-up process
            cursor.execute("""
                INSERT INTO user_activity (user_id, last_active_timestamp, last_follow_up_timestamp, follow_up_stage, meeting_booked_status, pending_booking_confirmation)
                VALUES (?, ?, NULL, 0, 0, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_active_timestamp = excluded.last_active_timestamp,
                    last_follow_up_timestamp = NULL, 
                    follow_up_stage = 0,
                    pending_booking_confirmation = 0, -- Reset pending confirmation too
                    meeting_booked_status = excluded.meeting_booked_status 
            """, (user_id, current_time))
        else:
            # If meeting is booked, just update last_active_timestamp
            cursor.execute("""
                INSERT INTO user_activity (user_id, last_active_timestamp, meeting_booked_status)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_active_timestamp = excluded.last_active_timestamp
            """, (user_id, current_time))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_user_activity for {user_id}: {e}")
    finally:
        conn.close()


def set_meeting_booked_status(user_id, booked=True):
    """Marks that a user has booked a meeting, stopping further follow-ups."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # Set meeting_booked_status to 1 (or 0 if unbooked)
        # And set follow_up_stage to MAX_FOLLOW_UPS to prevent further scheduling.
        # Or set to a specific stage e.g. 4, to indicate booked.
        final_follow_up_stage = MAX_FOLLOW_UPS if booked else 0  # if unbooked, reset to 0

        cursor.execute("""
            UPDATE user_activity
            SET meeting_booked_status = ?, follow_up_stage = ?
            WHERE user_id = ?;
        """, (1 if booked else 0, final_follow_up_stage, user_id))

        # If the table or user doesn't exist, it might be an initial contact confirming booking.
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO user_activity (user_id, last_active_timestamp, last_follow_up_timestamp, follow_up_stage, meeting_booked_status, pending_booking_confirmation)
                VALUES (?, ?, NULL, ?, ?, 0);
            """, (user_id, int(time.time()), final_follow_up_stage, 1 if booked else 0))
        conn.commit()
        print(
            f"Meeting booked status for {user_id} set to {booked}. Follow-up stage set to {final_follow_up_stage}.")
    except sqlite3.Error as e:
        print(
            f"Database error in set_meeting_booked_status for {user_id}: {e}")
    finally:
        conn.close()


def mark_user_disinterested(user_id):
    """Marks a user as disinterested, stopping further follow-ups."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE user_activity
            SET follow_up_stage = ? 
            WHERE user_id = ?;
        """, (MAX_FOLLOW_UPS, user_id))  # Set to max stage to stop follow-ups
        if cursor.rowcount == 0:  # User might not be in activity table yet
            cursor.execute("""
                INSERT INTO user_activity (user_id, last_active_timestamp, follow_up_stage, meeting_booked_status, pending_booking_confirmation)
                VALUES (?, ?, ?, 0, 0);
            """, (user_id, int(time.time()), MAX_FOLLOW_UPS))
        conn.commit()
        print(f"User {user_id} marked as disinterested. Follow-ups stopped.")
    except sqlite3.Error as e:
        print(f"Database error in mark_user_disinterested for {user_id}: {e}")
    finally:
        conn.close()


def get_users_for_follow_up():
    """
    Retrieves users who need a follow-up message.
    Considers their current follow_up_stage, last_active_timestamp, 
    last_follow_up_timestamp, and meeting_booked_status.
    """
    conn = connect_db()
    cursor = conn.cursor()
    users_to_follow_up = []
    current_time = int(time.time())

    try:
        # Ensure user_activity table exists (idempotent)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id TEXT PRIMARY KEY,
            last_active_timestamp INTEGER,
            last_follow_up_timestamp INTEGER,
            follow_up_stage INTEGER DEFAULT 0,
            meeting_booked_status INTEGER DEFAULT 0,
            pending_booking_confirmation INTEGER DEFAULT 0
        );
        """)
        conn.commit()

        cursor.execute("""
            SELECT user_id, last_active_timestamp, last_follow_up_timestamp, follow_up_stage
            FROM user_activity
            WHERE meeting_booked_status = 0 AND follow_up_stage < ? AND pending_booking_confirmation = 0
        """, (MAX_FOLLOW_UPS,))
        potential_users = cursor.fetchall()

        for user_id, last_active, last_follow_up, stage in potential_users:
            next_stage_to_send = stage + 1
            if next_stage_to_send > MAX_FOLLOW_UPS:
                continue

            required_interval = FOLLOW_UP_INTERVALS_SECONDS.get(
                next_stage_to_send)
            if not required_interval:  # Should not happen if next_stage_to_send <= MAX_FOLLOW_UPS
                continue

            time_since_event = 0
            if stage == 0:  # First follow-up, based on last activity
                if last_active:
                    time_since_event = current_time - last_active
            else:  # Subsequent follow-ups, based on last follow-up time
                if last_follow_up:
                    time_since_event = current_time - last_follow_up

            if time_since_event >= required_interval:
                users_to_follow_up.append(
                    {"id": user_id, "next_stage": next_stage_to_send})

    except sqlite3.Error as e:
        print(f"Database error in get_users_for_follow_up: {e}")
    finally:
        conn.close()
    return users_to_follow_up


def send_follow_up_message(user_id, stage_to_send):
    """Sends a specific follow-up message to a user for a given stage."""
    follow_up_text = FOLLOW_UP_MESSAGES.get(stage_to_send)
    if not follow_up_text:
        print(
            f"No follow-up message defined for stage {stage_to_send} for user {user_id}")
        return

    print(
        f"Sending follow-up stage {stage_to_send} to {user_id}: {follow_up_text}")
    data = util.TextMessage(follow_up_text, user_id)
    whatsappservice.SendMessageWhatsapp(data)

    # Update database
    conn = connect_db()
    cursor = conn.cursor()
    current_time = int(time.time())
    try:
        cursor.execute("""
            UPDATE user_activity
            SET last_follow_up_timestamp = ?, follow_up_stage = ?
            WHERE user_id = ?;
        """, (current_time, stage_to_send, user_id))
        conn.commit()
        print(
            f"Follow-up stage {stage_to_send} sent to {user_id} and DB updated.")
    except sqlite3.Error as e:
        print(
            f"Database error updating follow-up status for {user_id} after sending stage {stage_to_send}: {e}")
    finally:
        conn.close()


def scheduled_follow_up_task():
    """Scheduled task to check for and send follow-up messages."""
    print("Running scheduled_follow_up_task...")
    users_needing_follow_up = get_users_for_follow_up()

    if not users_needing_follow_up:
        print("No users to follow up with at this time.")
        return

    for user_data in users_needing_follow_up:
        user_id = user_data["id"]
        next_stage = user_data["next_stage"]
        print(
            f"Processing follow-up for user: {user_id}, scheduled for stage {next_stage}")
        send_follow_up_message(user_id, next_stage)
        # time.sleep(1) # Optional delay
    print("Scheduled follow-up task completed.")


def set_meeting_link_offered(user_id):
    """Marks that a meeting link was offered, so we can ask for confirmation next."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE user_activity
            SET pending_booking_confirmation = 1, last_active_timestamp = ?
            WHERE user_id = ?;
        """, (int(time.time()), user_id))
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO user_activity (user_id, last_active_timestamp, pending_booking_confirmation, follow_up_stage, meeting_booked_status)
                VALUES (?, ?, 1, 0, 0);
            """, (user_id, int(time.time())))
        conn.commit()
        print(f"User {user_id} marked as pending_booking_confirmation.")
    except sqlite3.Error as e:
        print(f"Database error in set_meeting_link_offered for {user_id}: {e}")
    finally:
        conn.close()


def get_pending_booking_confirmation_status(user_id):
    """Checks if we are waiting for booking confirmation from the user."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT pending_booking_confirmation FROM user_activity WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result and result[0] == 1 else 0
    except sqlite3.Error as e:
        print(
            f"Database error in get_pending_booking_confirmation_status for {user_id}: {e}")
        return 0
    finally:
        conn.close()


def clear_pending_booking_confirmation(user_id):
    """Clears the pending booking confirmation status, e.g., after user confirms or denies."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE user_activity
            SET pending_booking_confirmation = 0
            WHERE user_id = ?;
        """, (user_id,))
        conn.commit()
        print(f"Cleared pending_booking_confirmation for user {user_id}.")
    except sqlite3.Error as e:
        print(
            f"Database error in clear_pending_booking_confirmation for {user_id}: {e}")
    finally:
        conn.close()
