from flask import Blueprint, render_template, request, jsonify, g
from flask_login import current_user, login_required
from extensions import db
from models import User, Message
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/widget_data')
@login_required
def widget_data():
    """
    Dohvata osnovne podatke za inicijalizaciju chat widgeta.
    Za admina, pronalazi sve korisnike sa kojima postoji razgovor.
    Za korisnika, pronalazi admina.
    """
    if current_user.role == 'admin':
        users_with_chats = db.session.query(User).join(Message, or_(
            Message.sender_id == User.id, Message.recipient_id == User.id
        )).filter(
            User.role != 'admin',
            or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
        ).distinct().all()

        users_list = []
        for user in users_with_chats:
            unread_count = Message.query.filter(
                Message.sender_id == user.id,
                Message.recipient_id == current_user.id,
                Message.is_read == False
            ).count()
            users_list.append({
                'id': user.id,
                'username': user.username,
                'unread_count': unread_count
            })

        return jsonify({'is_admin': True, 'users': users_list})
    else:
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            return jsonify({'is_admin': False, 'admin_id': None})

        unread_count = Message.query.filter(
            Message.sender_id == admin.id,
            Message.recipient_id == current_user.id,
            Message.is_read == False
        ).count()

        return jsonify({
            'is_admin': False,
            'admin_id': admin.id,
            'admin_username': admin.username,
            'unread_count': unread_count
        })


@chat_bp.route('/history/<int:other_user_id>')
@login_required
def get_chat_history(other_user_id):
    """Dohvata istoriju razgovora sa određenim korisnikom i označava poruke kao pročitane."""
    # Prevent users from reading their own messages endpoint with wrong ID
    if other_user_id == current_user.id:
        return jsonify({'error': 'Neispravan zahtjev'}), 400

    # Authorization: regular users can only chat with admin
    if current_user.role != 'admin':
        admin = User.query.filter_by(role='admin').first()
        if not admin or other_user_id != admin.id:
            return jsonify({'error': 'Nemate dozvolu'}), 403
    else:
        # Admin can only view chats where they are a participant
        other_user = User.query.get(other_user_id)
        if not other_user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404

    # Only fetch messages where current_user is a participant
    messages = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.recipient_id == other_user_id),
            (Message.sender_id == other_user_id) & (Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    unread_messages = Message.query.filter(
        Message.sender_id == other_user_id,
        Message.recipient_id == current_user.id,
        Message.is_read == False
    ).all()

    for msg in unread_messages:
        msg.is_read = True
    db.session.commit()

    return jsonify([{
        'id': msg.id,
        'sender_id': msg.sender_id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M')
    } for msg in messages])


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Prima i čuva novu poruku."""
    data = request.json
    recipient_id = data.get('recipient_id')
    content = data.get('content', '').strip()

    # --- NOVI KOD ZA PROVJERU DUŽINE ---
    MAX_MESSAGE_LENGTH = 1000
    if len(content) > MAX_MESSAGE_LENGTH:
        return jsonify({'error': f'Poruka ne može biti duža od {MAX_MESSAGE_LENGTH} karaktera.'}), 400
    # --- KRAJ NOVOG KODA ---

    if not all([recipient_id, content]):
        return jsonify({'error': 'Nedostaju podaci'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Primalac nije pronađen'}), 404

    if current_user.role != 'admin' and recipient.role != 'admin':
        return jsonify({'error': 'Nemate dozvolu za slanje poruke ovom korisniku'}), 403

    msg = Message(sender_id=current_user.id, recipient_id=recipient_id, content=content)
    db.session.add(msg)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Poruka poslata.'})


@chat_bp.route('/unread_check')
@login_required
def unread_check():
    """
    Provjerava da li ima novih nepročitanih poruka od zadnjeg poznatog ID-a poruke.
    """
    last_known_id = request.args.get('last_id', 0, type=int)

    new_messages = Message.query.filter(
        Message.recipient_id == current_user.id,
        Message.is_read == False,
        Message.id > last_known_id
    ).all()

    if new_messages:
        senders = {}
        max_id = last_known_id
        for msg in new_messages:
            if msg.sender_id not in senders:
                senders[msg.sender_id] = []
            senders[msg.sender_id].append({
                'id': msg.id,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%H:%M')
            })
            if msg.id > max_id:
                max_id = msg.id

        return jsonify({'has_new': True, 'senders': senders, 'last_id': max_id})

    return jsonify({'has_new': False})


@chat_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_conversation(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Nemate dozvolu'}), 403

    # Brisanje svih poruka između admina i odabranog korisnika
    Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.recipient_id == user_id),
            (Message.sender_id == user_id) & (Message.recipient_id == current_user.id)
        )
    ).delete()

    db.session.commit()
    return jsonify({'success': True, 'message': 'Razgovor je obrisan.'})