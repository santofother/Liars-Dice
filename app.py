from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
from collections import Counter
import string
import os
import secrets
import time
from database import (
    create_user, authenticate_user, get_user_by_username,
    increment_user_wins, update_last_login, get_top_pirates,
    reset_user_wins, reset_all_wins, get_all_users,
    increment_user_coins, get_user_coins, get_top_by_coins,
    update_user_avatar, set_user_coins, get_user_rank
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store all active games
games = {}

# Store user sessions (token -> user data)
user_sessions = {}
SESSION_EXPIRY = 86400  # 24 hours in seconds

def create_session(username, avatar, wins, coins=50):
    """Create a new session token for a user."""
    token = secrets.token_urlsafe(32)
    user_sessions[token] = {
        'username': username,
        'avatar': avatar,
        'wins': wins,
        'coins': coins,
        'created_at': time.time()
    }
    return token

def validate_session(token):
    """Validate a session token and check expiration."""
    if not token or token not in user_sessions:
        return None

    session_data = user_sessions[token]
    # Check if expired (24 hours)
    if time.time() - session_data['created_at'] > SESSION_EXPIRY:
        del user_sessions[token]
        return None

    return session_data

def invalidate_session(token):
    """Remove a session token."""
    if token in user_sessions:
        del user_sessions[token]

def broadcast_leaderboard_update():
    """Broadcast updated leaderboard (Most Treasure) to all connected clients."""
    leaderboard = get_top_by_coins(5)
    socketio.emit('leaderboard_update', {
        'top_pirates': leaderboard
    }, broadcast=True)

def generate_room_code():
    """Generate a 4-letter room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in games:
            return code

def create_game(room_code, host_name, num_ai=0, is_private=False):
    """Create a new game state."""
    game = {
        'room_code': room_code,
        'players': [],
        'current_bid': None,
        'current_bidder': None,
        'current_player': 0,
        'phase': 'lobby',  # lobby, rolling, bidding, reveal, game_over
        'message': 'Waiting for players...',
        'round_history': [],
        'host': host_name,
        'num_ai': num_ai,
        'min_players': 2,
        'max_players': 6,
        'is_private': is_private
    }

    # Add host as first player
    game['players'].append({
        'name': host_name,
        'dice': [],
        'num_dice': 5,
        'is_human': True,
        'sid': None,
        'connected': True
    })

    return game

def add_ai_players(game):
    """Add AI players to the game."""
    pirate_names = ['Davy Jones', 'Blackbeard', 'Red Beard', 'Salty Pete', 'One-Eyed Willy']
    random.shuffle(pirate_names)

    difficulties = ['easy', 'medium', 'hard', 'impossible']

    for i in range(game['num_ai']):
        if len(game['players']) < game['max_players']:
            # Assign individual difficulty for random mode
            if game.get('ai_difficulty') == 'random':
                ai_difficulty = random.choice(difficulties)
            else:
                ai_difficulty = game.get('ai_difficulty', 'hard')

            game['players'].append({
                'name': pirate_names[i],
                'dice': [],
                'num_dice': 5,
                'is_human': False,
                'sid': None,
                'connected': True,
                'avatar': ['🦑', '🏴‍☠️', '⚓', '💀', '🦜'][i],
                'ai_difficulty': ai_difficulty  # Individual AI difficulty
            })

def roll_all_dice(game):
    """Roll dice for all alive players. Clear dice for eliminated players."""
    for player in game['players']:
        if player['num_dice'] > 0:
            player['dice'] = [random.randint(1, 6) for _ in range(player['num_dice'])]
        else:
            player['dice'] = []

def total_dice_in_play(game):
    """Count total dice across all players."""
    return sum(p['num_dice'] for p in game['players'] if p['num_dice'] > 0)

def count_actual_dice(game, face_value):
    """Count dice showing face value (1s are wild except when bidding on 1s)."""
    total = 0
    for player in game['players']:
        if player['num_dice'] > 0:
            for die in player['dice']:
                if die == face_value or (die == 1 and face_value != 1):
                    total += 1
    return total

def is_valid_bid(game, quantity, face_value):
    """Check if bid is valid."""
    if quantity < 1 or face_value < 1 or face_value > 6:
        return False
    if quantity > total_dice_in_play(game):
        return False
    if game['current_bid'] is None:
        return True

    curr_qty, curr_face = game['current_bid']
    if quantity > curr_qty:
        return True
    if quantity == curr_qty and face_value > curr_face:
        return True
    return False

def get_ai_action(game, player):
    """AI decides to bid or challenge based on difficulty."""
    # Use individual AI difficulty if set, otherwise fall back to game difficulty
    difficulty = player.get('ai_difficulty', game.get('ai_difficulty', 'hard'))

    # Handle random mode fallback (shouldn't happen but just in case)
    if difficulty == 'random':
        difficulty = random.choice(['easy', 'medium', 'hard', 'impossible'])

    if difficulty == 'impossible':
        return get_ai_action_impossible(game, player)
    elif difficulty == 'hard':
        return get_ai_action_hard(game, player)
    elif difficulty == 'medium':
        return get_ai_action_medium(game, player)
    else:  # easy
        return get_ai_action_easy(game, player)

def get_ai_action_easy(game, player):
    """Easy AI - basic strategy, makes mistakes."""
    my_dice = Counter(player['dice'])
    ones_count = my_dice.get(1, 0)

    if game['current_bid'] is None:
        best_face = max(range(2, 7), key=lambda f: my_dice.get(f, 0) + ones_count)
        count = my_dice.get(best_face, 0) + ones_count
        quantity = max(1, count)
        return 'bid', quantity, best_face

    curr_qty, curr_face = game['current_bid']
    total = total_dice_in_play(game)
    expected = total / 3
    my_matching = my_dice.get(curr_face, 0) + (ones_count if curr_face != 1 else 0)

    if curr_qty > expected + 2 and my_matching < 2:
        challenge_chance = min(0.7, (curr_qty - expected) / total)
        if random.random() < challenge_chance:
            return 'challenge', None, None

    possible_bids = []
    for face in range(1, 7):
        matching = my_dice.get(face, 0)
        if face != 1:
            matching += ones_count
        new_qty = curr_qty + 1
        if new_qty <= total and is_valid_bid(game, new_qty, face):
            confidence = matching / max(1, new_qty)
            possible_bids.append((new_qty, face, confidence))

    for face in range(curr_face + 1, 7):
        matching = my_dice.get(face, 0) + ones_count
        if is_valid_bid(game, curr_qty, face):
            confidence = matching / max(1, curr_qty)
            possible_bids.append((curr_qty, face, confidence))

    if possible_bids:
        possible_bids.sort(key=lambda x: x[2], reverse=True)
        chosen = random.choice(possible_bids[:3])
        return 'bid', chosen[0], chosen[1]

    return 'challenge', None, None

def get_ai_action_medium(game, player):
    """Medium AI - better statistics, fewer mistakes."""
    my_dice = Counter(player['dice'])
    ones_count = my_dice.get(1, 0)
    total = total_dice_in_play(game)
    other_dice = total - len(player['dice'])

    if game['current_bid'] is None:
        # Start with a reasonable bid based on own dice + expected others
        best_face = max(range(2, 7), key=lambda f: my_dice.get(f, 0) + ones_count)
        my_count = my_dice.get(best_face, 0) + ones_count
        expected_others = other_dice / 3  # ~1/3 chance for any face (with wilds)
        quantity = max(1, int(my_count + expected_others * 0.5))
        return 'bid', quantity, best_face

    curr_qty, curr_face = game['current_bid']

    # Calculate probability the bid is true
    my_matching = my_dice.get(curr_face, 0) + (ones_count if curr_face != 1 else 0)
    expected_others = other_dice / 3
    expected_total = my_matching + expected_others

    # Challenge if bid seems too high
    if curr_qty > expected_total + 1:
        challenge_prob = min(0.85, (curr_qty - expected_total) / (total * 0.5))
        if random.random() < challenge_prob:
            return 'challenge', None, None

    # Find best bid
    possible_bids = []
    for face in range(1, 7):
        my_count = my_dice.get(face, 0)
        if face != 1:
            my_count += ones_count
        expected = my_count + (other_dice / 3)

        for qty in [curr_qty, curr_qty + 1]:
            if is_valid_bid(game, qty, face) and qty <= total:
                safety = expected / max(1, qty)
                possible_bids.append((qty, face, safety))

    if possible_bids:
        possible_bids.sort(key=lambda x: x[2], reverse=True)
        # Pick from top 2 best options
        chosen = random.choice(possible_bids[:2]) if len(possible_bids) > 1 else possible_bids[0]
        return 'bid', chosen[0], chosen[1]

    return 'challenge', None, None

def get_ai_action_hard(game, player):
    """Hard AI - near-perfect statistics with some calculated risks."""
    my_dice = Counter(player['dice'])
    ones_count = my_dice.get(1, 0)
    total = total_dice_in_play(game)
    other_dice = total - len(player['dice'])

    if game['current_bid'] is None:
        # Optimal opening: bid based on statistical expectation
        best_face = None
        best_expected = 0
        for face in range(2, 7):
            my_count = my_dice.get(face, 0) + ones_count
            # Expected value: my dice + (other_dice * probability of face or 1)
            # P(face or 1) = 2/6 = 1/3
            expected = my_count + (other_dice * (1/3))
            if expected > best_expected:
                best_expected = expected
                best_face = face

        # Bid slightly under expected for safety, but take some risk
        quantity = max(1, int(best_expected * 0.85))
        return 'bid', quantity, best_face or 6

    curr_qty, curr_face = game['current_bid']

    # Precise probability calculation
    my_matching = my_dice.get(curr_face, 0) + (ones_count if curr_face != 1 else 0)
    prob_per_die = 1/3 if curr_face != 1 else 1/6  # 1s are less common when bidding on 1s
    expected_others = other_dice * prob_per_die
    expected_total = my_matching + expected_others

    # Standard deviation for binomial distribution
    variance = other_dice * prob_per_die * (1 - prob_per_die)
    std_dev = variance ** 0.5

    # Challenge if bid is more than 1.5 std devs above expected
    if curr_qty > expected_total + (1.5 * std_dev):
        # High confidence challenge
        if random.random() < 0.9:
            return 'challenge', None, None
    elif curr_qty > expected_total + (0.5 * std_dev):
        # Medium confidence - sometimes challenge
        if random.random() < 0.4:
            return 'challenge', None, None

    # Find optimal bid
    best_bid = None
    best_score = -1

    for face in range(1, 7):
        my_count = my_dice.get(face, 0)
        if face != 1:
            my_count += ones_count

        prob = 1/3 if face != 1 else 1/6
        expected = my_count + (other_dice * prob)
        std = (other_dice * prob * (1 - prob)) ** 0.5

        for qty in range(curr_qty, min(curr_qty + 3, total + 1)):
            if is_valid_bid(game, qty, face):
                # Score based on how safe the bid is
                z_score = (expected - qty) / max(0.1, std)
                safety_score = z_score + random.uniform(-0.3, 0.3)  # Small randomness
                if safety_score > best_score:
                    best_score = safety_score
                    best_bid = (qty, face)

    if best_bid and best_score > -1:
        return 'bid', best_bid[0], best_bid[1]

    return 'challenge', None, None

def get_ai_action_impossible(game, player):
    """Impossible AI - sees all dice, plays perfectly."""
    curr_bid = game['current_bid']
    total = total_dice_in_play(game)

    # Count ALL dice on the table (cheating!)
    all_dice = Counter()
    for p in game['players']:
        if p['num_dice'] > 0:
            for die in p['dice']:
                all_dice[die] += 1

    if curr_bid is None:
        # Open with exact count of most common face
        best_face = None
        best_count = 0
        for face in range(2, 7):
            count = all_dice.get(face, 0) + all_dice.get(1, 0)  # Include wilds
            if count > best_count:
                best_count = count
                best_face = face
        return 'bid', best_count, best_face or 6

    curr_qty, curr_face = curr_bid

    # Count actual matching dice
    actual = all_dice.get(curr_face, 0)
    if curr_face != 1:
        actual += all_dice.get(1, 0)  # Add wilds

    # If current bid is a lie, challenge immediately
    if actual < curr_qty:
        return 'challenge', None, None

    # Find the safest true bid
    best_bid = None
    for face in range(1, 7):
        count = all_dice.get(face, 0)
        if face != 1:
            count += all_dice.get(1, 0)

        for qty in range(curr_qty, count + 1):
            if is_valid_bid(game, qty, face):
                best_bid = (qty, face)
                break  # Take lowest valid bid for this face

        if best_bid:
            break

    if best_bid:
        return 'bid', best_bid[0], best_bid[1]

    # No safe bid possible, must challenge
    return 'challenge', None, None

def get_alive_players(game):
    """Get indices of alive players."""
    return [i for i, p in enumerate(game['players']) if p['num_dice'] > 0]

def next_alive_player(game, current):
    """Get next alive player index, following the round's turn order."""
    turn_order = game.get('turn_order')
    if turn_order:
        # Filter turn_order to only alive players
        alive = get_alive_players(game)
        if len(alive) <= 1:
            return None
        alive_order = [p for p in turn_order if p in alive]
        if current in alive_order:
            current_pos = alive_order.index(current)
            next_pos = (current_pos + 1) % len(alive_order)
            return alive_order[next_pos]
    # Fallback to original logic
    alive = get_alive_players(game)
    if len(alive) <= 1:
        return None
    current_pos = alive.index(current) if current in alive else 0
    next_pos = (current_pos + 1) % len(alive)
    return alive[next_pos]

def get_game_state_for_player(game, player_sid):
    """Get sanitized game state for a specific player."""
    players_data = []
    player_index = -1

    for i, p in enumerate(game['players']):
        if p.get('sid') == player_sid:
            player_index = i

        player_data = {
            'name': p['name'],
            'num_dice': p['num_dice'],
            'is_human': p['is_human'],
            'connected': p.get('connected', True),
            'avatar': p.get('avatar', '⚓' if p['is_human'] else '🏴‍☠️')
        }

        # Show dice only to the owner, or during reveal/game_over
        if p.get('sid') == player_sid or game['phase'] in ['reveal', 'game_over']:
            player_data['dice'] = p['dice']
        elif not p['is_human'] and game['phase'] in ['reveal', 'game_over']:
            player_data['dice'] = p['dice']
        else:
            player_data['dice'] = [0] * p['num_dice']  # Hidden

        players_data.append(player_data)

    # Check if this player is in waiting list
    is_waiting = False
    for wp in game.get('waiting_players', []):
        if wp.get('sid') == player_sid:
            is_waiting = True
            break

    # Get waiting players data
    waiting_data = []
    for wp in game.get('waiting_players', []):
        waiting_data.append({
            'name': wp['name'],
            'avatar': wp.get('avatar', '⚓'),
            'connected': wp.get('connected', True)
        })

    return {
        'room_code': game['room_code'],
        'players': players_data,
        'current_bid': game['current_bid'],
        'current_player': game['current_player'],
        'phase': game['phase'],
        'message': game['message'],
        'total_dice': total_dice_in_play(game),
        'round_history': game['round_history'],
        'reveal_data': game.get('reveal_data'),
        'player_index': player_index,
        'is_host': player_index == 0,
        'host': game['host'],
        'waiting_players': waiting_data,
        'is_waiting': is_waiting,
        'ai_difficulty': game.get('ai_difficulty', 'hard'),
        'is_private': game.get('is_private', False),
        'num_ai': game.get('num_ai', 0)
    }

def broadcast_game_state(room_code):
    """Send game state to all players in room."""
    game = games.get(room_code)
    if not game:
        return

    # Send to active players
    for player in game['players']:
        if player.get('sid') and player['is_human']:
            state = get_game_state_for_player(game, player['sid'])
            socketio.emit('game_state', state, room=player['sid'])

    # Send to waiting players
    for player in game.get('waiting_players', []):
        if player.get('sid'):
            state = get_game_state_for_player(game, player['sid'])
            socketio.emit('game_state', state, room=player['sid'])

def process_ai_turns(game):
    """Process AI player turns."""
    import time

    while game['phase'] == 'bidding':
        current = game['current_player']
        if current is None:
            break

        player = game['players'][current]

        if player['is_human']:
            game['message'] = f"Waiting for {player['name']}..."
            break

        if player['num_dice'] <= 0:
            next_player = next_alive_player(game, current)
            if next_player is None:
                break
            game['current_player'] = next_player
            continue

        # Broadcast that AI is thinking
        game['message'] = f"{player['name']} is thinking..."
        broadcast_game_state(game['room_code'])

        socketio.sleep(1.5)  # AI thinking delay

        action, qty, face = get_ai_action(game, player)

        if action == 'challenge':
            game['round_history'].append({
                'player': player['name'],
                'action': 'challenge'
            })
            resolve_challenge(game, current, game['current_bidder'])
            break
        else:
            game['current_bid'] = (qty, face)
            game['current_bidder'] = current
            game['round_history'].append({
                'player': player['name'],
                'action': 'bid',
                'bid': f"{qty}x {face}s"
            })
            game['message'] = f"{player['name']} bids {qty}x {face}s"
            next_idx = next_alive_player(game, current)
            if next_idx is None:
                break
            game['current_player'] = next_idx
            broadcast_game_state(game['room_code'])

def resolve_challenge(game, challenger_idx, bidder_idx):
    """Resolve a challenge."""
    qty, face = game['current_bid']
    actual = count_actual_dice(game, face)

    game['phase'] = 'reveal'
    game['reveal_data'] = {
        'bid_qty': qty,
        'bid_face': face,
        'actual': actual,
        'challenger': game['players'][challenger_idx]['name'],
        'bidder': game['players'][bidder_idx]['name']
    }

    challenger = game['players'][challenger_idx]
    bidder = game['players'][bidder_idx]

    if actual >= qty:
        challenger['num_dice'] -= 1
        loser_idx = challenger_idx
        game['message'] = f"The bid was TRUE! {challenger['name']} loses a die!"
    else:
        bidder['num_dice'] -= 1
        loser_idx = bidder_idx
        game['message'] = f"LIAR! {bidder['name']} loses a die!"

    alive = get_alive_players(game)
    if len(alive) <= 1:
        game['phase'] = 'game_over'
        winner = game['players'][alive[0]] if alive else None
        if winner:
            game['message'] = f"{winner['name']} WINS! The treasure is theirs!"

            # Record win and award coins if user is logged in
            try:
                if winner.get('user_token'):
                    session_data = validate_session(winner['user_token'])
                    if session_data:
                        increment_user_wins(session_data['username'])
                        # Only award coins on hard+ difficulty
                        diff = game.get('ai_difficulty', 'hard')
                        if diff in ('hard', 'impossible', 'random'):
                            increment_user_coins(session_data['username'], 100)
                        user_data = get_user_by_username(session_data['username'])
                        if user_data:
                            session_data['wins'] = user_data['wins']
                            session_data['coins'] = user_data.get('coins', 0)
                            if winner.get('sid'):
                                socketio.emit('coins_update', {'coins': user_data.get('coins', 0)}, room=winner['sid'])
                        broadcast_leaderboard_update()
            except Exception as e:
                print(f"Error recording win: {e}")
    # Round starter rotation is handled in roll_dice

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

# Socket events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")

    # Find and update player status
    for room_code, game in list(games.items()):
        # Check active players
        for player in game['players']:
            if player.get('sid') == sid:
                player['connected'] = False
                print(f"Player {player['name']} marked as disconnected in room {room_code}")
                broadcast_game_state(room_code)
                return

        # Check waiting players
        if 'waiting_players' in game:
            for waiting_player in game['waiting_players']:
                if waiting_player.get('sid') == sid:
                    waiting_player['connected'] = False
                    print(f"Waiting player {waiting_player['name']} marked as disconnected in room {room_code}")
                    broadcast_game_state(room_code)
                    return

@socketio.on('create_game')
def handle_create_game(data):
    player_name = data.get('name', 'Captain')[:20]
    num_ai = int(data.get('num_ai', 2))
    avatar = data.get('avatar', '🏴‍☠️')
    ai_difficulty = data.get('ai_difficulty', 'hard')
    user_token = data.get('user_token')

    # Validate difficulty
    if ai_difficulty not in ['easy', 'medium', 'hard', 'impossible', 'random']:
        ai_difficulty = 'hard'

    is_private = bool(data.get('is_private', False))

    room_code = generate_room_code()
    game = create_game(room_code, player_name, num_ai, is_private)
    game['players'][0]['sid'] = request.sid
    game['players'][0]['avatar'] = avatar
    game['ai_difficulty'] = ai_difficulty

    # Store user token if logged in
    if user_token:
        session_data = validate_session(user_token)
        if session_data:
            game['players'][0]['user_token'] = user_token
            game['players'][0]['username'] = session_data['username']

    games[room_code] = game
    join_room(room_code)

    emit('game_created', {'room_code': room_code})
    emit('game_state', get_game_state_for_player(game, request.sid))

@socketio.on('join_game')
def handle_join_game(data):
    room_code = data.get('room_code', '').upper()
    player_name = data.get('name', 'Sailor')[:20]
    avatar = data.get('avatar', '🏴‍☠️')
    user_token = data.get('user_token')

    game = games.get(room_code)
    if not game:
        emit('game_not_found', {'message': "No ship sails under that flag, matey! Check yer code or browse the tavern board."})
        return

    # Check if this player is reconnecting (matching name)
    reconnecting_player = None
    for player in game['players']:
        if player['is_human'] and player['name'].lower() == player_name.lower():
            reconnecting_player = player
            break

    # If reconnecting to an existing player slot
    if reconnecting_player:
        reconnecting_player['sid'] = request.sid
        reconnecting_player['connected'] = True
        if avatar:
            reconnecting_player['avatar'] = avatar

        # Update user token if provided (preserves win tracking after reconnect)
        if user_token:
            session_data = validate_session(user_token)
            if session_data:
                reconnecting_player['user_token'] = user_token
                reconnecting_player['username'] = session_data['username']

        join_room(room_code)
        game['message'] = f"{reconnecting_player['name']} has rejoined the crew!"

        emit('game_created', {'room_code': room_code})  # So client knows they're in
        broadcast_game_state(room_code)
        return

    # Check if this player is reconnecting to waiting list
    if 'waiting_players' in game:
        for waiting_player in game['waiting_players']:
            if waiting_player['name'].lower() == player_name.lower():
                waiting_player['sid'] = request.sid
                waiting_player['connected'] = True
                if avatar:
                    waiting_player['avatar'] = avatar
                if user_token:
                    sd = validate_session(user_token)
                    if sd:
                        waiting_player['user_token'] = user_token
                        waiting_player['username'] = sd['username']

                join_room(room_code)
                game['message'] = f"{waiting_player['name']} has rejoined the waiting list!"

                emit('game_created', {'room_code': room_code})
                emit('waiting_status', {'message': 'You are spectating. You will join when the game returns to lobby!'})
                broadcast_game_state(room_code)
                return

    # If game is in progress, check for disconnected players or add as waiting
    if game['phase'] != 'lobby':
        # Look for disconnected human players
        disconnected_player = None
        for player in game['players']:
            if player['is_human'] and not player.get('connected', True):
                disconnected_player = player
                break

        if disconnected_player:
            # Take over disconnected player's slot
            old_name = disconnected_player['name']
            disconnected_player['sid'] = request.sid
            disconnected_player['connected'] = True
            disconnected_player['name'] = player_name
            if avatar:
                disconnected_player['avatar'] = avatar
            if user_token:
                sd = validate_session(user_token)
                if sd:
                    disconnected_player['user_token'] = user_token
                    disconnected_player['username'] = sd['username']

            join_room(room_code)
            game['message'] = f"{player_name} took over for {old_name}!"

            emit('game_created', {'room_code': room_code})
            broadcast_game_state(room_code)
            return
        else:
            # Add as waiting player (will join next game)
            if 'waiting_players' not in game:
                game['waiting_players'] = []

            # Check if already waiting
            existing_waiting = [p['name'].lower() for p in game['waiting_players']]
            if player_name.lower() in existing_waiting:
                emit('game_error', {'message': 'You are already in the waiting list!'})
                return

            if len(game['waiting_players']) >= 4:  # Limit waiting players
                emit('game_error', {'message': 'Waiting list is full!'})
                return

            waiting_player = {
                'name': player_name,
                'dice': [],
                'num_dice': 5,
                'is_human': True,
                'sid': request.sid,
                'connected': True,
                'avatar': avatar,
                'is_waiting': True
            }

            # Store user token if logged in
            if user_token:
                session_data = validate_session(user_token)
                if session_data:
                    waiting_player['user_token'] = user_token
                    waiting_player['username'] = session_data['username']

            game['waiting_players'].append(waiting_player)

            join_room(room_code)
            game['message'] = f"{player_name} is waiting to join next game!"

            emit('game_created', {'room_code': room_code})
            emit('waiting_status', {'message': 'You are spectating. You will join when the game returns to lobby!'})
            broadcast_game_state(room_code)
            return

    # Normal join during lobby phase
    if len([p for p in game['players'] if p['is_human']]) >= game['max_players'] - game['num_ai']:
        emit('game_error', {'message': 'Game is full!'})
        return

    # Check if name already taken (add suffix if so)
    existing_names = [p['name'].lower() for p in game['players']]
    original_name = player_name
    counter = 1
    while player_name.lower() in existing_names:
        player_name = f"{original_name}_{counter}"
        counter += 1

    new_player = {
        'name': player_name,
        'dice': [],
        'num_dice': 5,
        'is_human': True,
        'sid': request.sid,
        'connected': True,
        'avatar': avatar
    }

    # Store user token if logged in
    if user_token:
        session_data = validate_session(user_token)
        if session_data:
            new_player['user_token'] = user_token
            new_player['username'] = session_data['username']

    game['players'].append(new_player)

    join_room(room_code)
    game['message'] = f"{player_name} joined the crew!"

    emit('game_created', {'room_code': room_code})  # So client stores room code
    broadcast_game_state(room_code)

@socketio.on('start_game')
def handle_start_game(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game:
        return

    # Verify sender is host
    if game['players'][0].get('sid') != request.sid:
        emit('game_error', {'message': 'Only the host can start the game!'})
        return

    # Add AI players
    add_ai_players(game)

    human_count = len([p for p in game['players'] if p['is_human']])
    if human_count + game['num_ai'] < 2:
        emit('game_error', {'message': 'Need at least 2 players!'})
        return

    game['phase'] = 'rolling'
    game['message'] = 'Game starting! Roll the dice!'

    broadcast_game_state(room_code)

@socketio.on('roll_dice')
def handle_roll_dice(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game or game['phase'] not in ['rolling', 'reveal']:
        return

    roll_all_dice(game)
    game['current_bid'] = None
    game['current_bidder'] = None
    game['round_history'] = []

    alive = get_alive_players(game)

    if len(alive) <= 1:
        # Game should be over, don't start a new round
        game['phase'] = 'game_over'
        if alive:
            winner = game['players'][alive[0]]
            game['message'] = f"{winner['name']} WINS! The treasure is theirs!"
            # Record win and award coins
            try:
                if winner.get('user_token'):
                    session_data = validate_session(winner['user_token'])
                    if session_data:
                        increment_user_wins(session_data['username'])
                        diff = game.get('ai_difficulty', 'hard')
                        if diff in ('hard', 'impossible', 'random'):
                            increment_user_coins(session_data['username'], 100)
                        user_data = get_user_by_username(session_data['username'])
                        if user_data:
                            session_data['wins'] = user_data['wins']
                            session_data['coins'] = user_data.get('coins', 0)
                            if winner.get('sid'):
                                socketio.emit('coins_update', {'coins': user_data.get('coins', 0)}, room=winner['sid'])
                        broadcast_leaderboard_update()
            except Exception as e:
                print(f"Error recording win: {e}")
        broadcast_game_state(room_code)
        return

    game['phase'] = 'bidding'

    # Set first player for the round
    if game.get('round_starter') is not None:
        # Rotate clockwise from last round's starter
        last_starter = game['round_starter']
        if last_starter in alive:
            starter_pos = alive.index(last_starter)
            next_pos = (starter_pos + 1) % len(alive)
            game['current_player'] = alive[next_pos]
        else:
            # Last starter was eliminated, find next alive player clockwise
            for i in range(1, len(game['players']) + 1):
                next_idx = (last_starter + i) % len(game['players'])
                if next_idx in alive:
                    game['current_player'] = next_idx
                    break
    else:
        # First round of the game - random starting player
        game['current_player'] = random.choice(alive)

    # Remember who started this round for next rotation
    game['round_starter'] = game['current_player']

    # Build randomized turn order: first player stays, rest are shuffled
    first_player = game['current_player']
    others = [p for p in alive if p != first_player]
    random.shuffle(others)
    game['turn_order'] = [first_player] + others

    current_player = game['players'][game['current_player']]
    game['message'] = f"{current_player['name']}'s turn to bid!"

    broadcast_game_state(room_code)

    # If first player is AI, process their turn
    if not current_player['is_human']:
        socketio.start_background_task(process_ai_turns_async, room_code)

def process_ai_turns_async(room_code):
    """Background task for AI turns."""
    game = games.get(room_code)
    if game:
        process_ai_turns(game)
        broadcast_game_state(room_code)

@socketio.on('make_bid')
def handle_make_bid(data):
    room_code = data.get('room_code')
    quantity = data.get('quantity')
    face = data.get('face')

    game = games.get(room_code)
    if not game or game['phase'] != 'bidding':
        return

    current_player = game['players'][game['current_player']]
    if current_player.get('sid') != request.sid:
        emit('game_error', {'message': "It's not your turn!"})
        return

    if not is_valid_bid(game, quantity, face):
        emit('game_error', {'message': 'Invalid bid! Must be higher than current bid.'})
        return

    game['current_bid'] = (quantity, face)
    game['current_bidder'] = game['current_player']
    game['round_history'].append({
        'player': current_player['name'],
        'action': 'bid',
        'bid': f"{quantity}x {face}s"
    })

    next_idx = next_alive_player(game, game['current_player'])
    if next_idx is None:
        broadcast_game_state(room_code)
        return

    game['current_player'] = next_idx
    next_player = game['players'][game['current_player']]
    game['message'] = f"{next_player['name']}'s turn!"

    broadcast_game_state(room_code)

    # If next player is AI, process their turn
    if not next_player['is_human']:
        socketio.start_background_task(process_ai_turns_async, room_code)

@socketio.on('challenge')
def handle_challenge(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game or game['phase'] != 'bidding':
        return

    if game['current_bid'] is None:
        emit('game_error', {'message': 'Nothing to challenge!'})
        return

    current_player = game['players'][game['current_player']]
    if current_player.get('sid') != request.sid:
        emit('game_error', {'message': "It's not your turn!"})
        return

    challenger_idx = game['current_player']
    bidder_idx = game['current_bidder']

    game['round_history'].append({
        'player': current_player['name'],
        'action': 'challenge'
    })

    resolve_challenge(game, challenger_idx, bidder_idx)
    broadcast_game_state(room_code)

@socketio.on('continue_game')
def handle_continue(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game:
        return

    if game['phase'] == 'game_over':
        # Reset for new game
        for player in game['players']:
            player['num_dice'] = 5
            player['dice'] = []
        game['phase'] = 'rolling'
        game['current_bid'] = None
        game['round_starter'] = None  # Reset so new game gets random starter
        game['message'] = 'New game! Roll the dice!'
    elif game['phase'] == 'reveal':
        game['phase'] = 'rolling'
        game['message'] = 'Roll the dice for next round!'

    broadcast_game_state(room_code)

@socketio.on('return_to_lobby')
def handle_return_to_lobby(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game:
        return

    # Only host can return to lobby
    if game['players'][0].get('sid') != request.sid:
        emit('game_error', {'message': 'Only the host can return to lobby!'})
        return

    # Remove AI players (they'll be re-added when game starts)
    game['players'] = [p for p in game['players'] if p['is_human']]

    # Add any waiting players to main roster
    for waiting in game.get('waiting_players', []):
        if len(game['players']) < game['max_players']:
            game['players'].append(waiting)

    game['waiting_players'] = []

    # Reset all players
    for player in game['players']:
        player['num_dice'] = 5
        player['dice'] = []

    # Reset game state
    game['phase'] = 'lobby'
    game['current_bid'] = None
    game['current_bidder'] = None
    game['current_player'] = 0
    game['round_history'] = []
    game['reveal_data'] = None
    game['round_starter'] = None  # Reset so new game gets random starter
    game['message'] = 'Returned to lobby! Waiting for host to start...'

    broadcast_game_state(room_code)

@socketio.on('kick_player')
def handle_kick_player(data):
    room_code = data.get('room_code')
    player_index = data.get('player_index')
    game = games.get(room_code)

    if not game:
        return

    # Verify sender is host
    if game['players'][0].get('sid') != request.sid:
        emit('game_error', {'message': 'Only the host can kick players!'})
        return

    # Can't kick yourself (host is index 0)
    if player_index == 0 or player_index >= len(game['players']):
        return

    kicked_player = game['players'][player_index]
    kicked_name = kicked_player['name']
    kicked_sid = kicked_player.get('sid')

    # If it was the kicked player's turn, move to next player
    if game['phase'] == 'bidding' and game['current_player'] == player_index:
        alive = get_alive_players(game)
        if player_index in alive:
            game['current_player'] = next_alive_player(game, player_index)

    # Remove the player
    game['players'].pop(player_index)

    # Adjust current_player index if needed
    if game['current_player'] > player_index:
        game['current_player'] -= 1
    if game.get('current_bidder') and game['current_bidder'] > player_index:
        game['current_bidder'] -= 1

    game['message'] = f"{kicked_name} walked the plank!"

    # Notify the kicked player
    if kicked_sid:
        socketio.emit('kicked', {'message': 'You have been kicked from the game!'}, room=kicked_sid)

    # Check if game should continue
    alive = get_alive_players(game)
    if len(alive) <= 1 and game['phase'] not in ['lobby', 'game_over']:
        game['phase'] = 'game_over'
        if alive:
            winner = game['players'][alive[0]]
            game['message'] = f"{winner['name']} WINS! The treasure is theirs!"
            try:
                if winner.get('user_token'):
                    session_data = validate_session(winner['user_token'])
                    if session_data:
                        increment_user_wins(session_data['username'])
                        diff = game.get('ai_difficulty', 'hard')
                        if diff in ('hard', 'impossible', 'random'):
                            increment_user_coins(session_data['username'], 100)
                        user_data = get_user_by_username(session_data['username'])
                        if user_data:
                            session_data['wins'] = user_data['wins']
                            session_data['coins'] = user_data.get('coins', 0)
                            if winner.get('sid'):
                                socketio.emit('coins_update', {'coins': user_data.get('coins', 0)}, room=winner['sid'])
                        broadcast_leaderboard_update()
            except Exception as e:
                print(f"Error recording win: {e}")

    broadcast_game_state(room_code)

    # If next player is AI, process their turn
    if game['phase'] == 'bidding':
        current = game['players'][game['current_player']] if game['current_player'] < len(game['players']) else None
        if current and not current['is_human']:
            socketio.start_background_task(process_ai_turns_async, room_code)

@socketio.on('change_avatar')
def handle_change_avatar(data):
    room_code = data.get('room_code')
    avatar = data.get('avatar')
    game = games.get(room_code)

    if not game or not avatar:
        return

    # Find the player by their socket id
    for player in game['players']:
        if player.get('sid') == request.sid:
            player['avatar'] = avatar
            break

    broadcast_game_state(room_code)

@socketio.on('leave_game')
def handle_leave_game(data):
    room_code = data.get('room_code')
    game = games.get(room_code)

    if not game:
        return

    # Find the leaving player
    leaving_player = None
    leaving_idx = -1
    for i, player in enumerate(game['players']):
        if player.get('sid') == request.sid:
            leaving_player = player
            leaving_idx = i
            break

    # Also check waiting players
    if not leaving_player:
        for i, player in enumerate(game.get('waiting_players', [])):
            if player.get('sid') == request.sid:
                game['waiting_players'].pop(i)
                leave_room(room_code)
                broadcast_game_state(room_code)
                return

    if not leaving_player:
        return

    leave_room(room_code)

    # In lobby phase, fully remove the player
    if game['phase'] == 'lobby':
        game['players'].pop(leaving_idx)

        # Count remaining connected human players
        connected_humans = [p for p in game['players'] if p['is_human'] and p.get('connected', False)]
        if len(connected_humans) == 0:
            del games[room_code]
            return

        game['message'] = f"{leaving_player['name']} has left the ship!"
        broadcast_game_state(room_code)
        return

    # Mark player as disconnected (during active game)
    leaving_player['connected'] = False
    leaving_player['sid'] = None

    # Count remaining connected human players
    connected_humans = [p for p in game['players'] if p['is_human'] and p.get('connected', False)]

    if len(connected_humans) == 0:
        # No humans left, delete the game
        del games[room_code]
        return

    game['message'] = f"{leaving_player['name']} has left the ship!"

    # If it was the leaving player's turn, skip to next player
    if game['phase'] == 'bidding' and leaving_idx == game['current_player']:
        alive = get_alive_players(game)
        if leaving_idx in alive:
            game['current_player'] = next_alive_player(game, leaving_idx)
            if game['current_player'] is not None:
                next_player = game['players'][game['current_player']]
                game['message'] = f"{leaving_player['name']} fled! {next_player['name']}'s turn!"

                # If next player is AI, process their turn
                if not next_player['is_human']:
                    socketio.start_background_task(process_ai_turns_async, room_code)

    broadcast_game_state(room_code)

@socketio.on('chat_message')
def handle_chat_message(data):
    room_code = data.get('room_code')
    message = data.get('message', '')[:100]  # Limit message length

    game = games.get(room_code)
    if not game:
        return

    # Find sender
    sender = None
    for player in game['players']:
        if player.get('sid') == request.sid:
            sender = player
            break

    if not sender:
        return

    # Broadcast to all other players in the room
    for player in game['players']:
        if player.get('sid') and player['is_human'] and player['sid'] != request.sid:
            socketio.emit('chat_message', {
                'sender': sender['name'],
                'avatar': sender.get('avatar', '⚓'),
                'message': message
            }, room=player['sid'])

@socketio.on('browse_games')
def handle_browse_games():
    """Return list of public games for the server browser."""
    game_list = []
    for code, game in games.items():
        if game.get('is_private', False):
            continue
        human_count = len([p for p in game['players'] if p['is_human']])
        game_list.append({
            'room_code': code,
            'host': game['host'],
            'player_count': human_count,
            'max_players': game['max_players'],
            'phase': game['phase'],
            'ai_count': game.get('num_ai', 0),
            'ai_difficulty': game.get('ai_difficulty', 'hard')
        })
    emit('game_list', {'games': game_list})

@socketio.on('update_ai_count')
def handle_update_ai_count(data):
    """Host adjusts AI count in lobby."""
    room_code = data.get('room_code')
    game = games.get(room_code)
    if not game or game['phase'] != 'lobby':
        return
    # Host-only
    if game['players'][0].get('sid') != request.sid:
        return
    human_count = len([p for p in game['players'] if p['is_human']])
    max_ai = game['max_players'] - human_count
    new_count = max(0, min(int(data.get('num_ai', 0)), max_ai))
    game['num_ai'] = new_count
    broadcast_game_state(room_code)

@socketio.on('update_ai_difficulty')
def handle_update_ai_difficulty(data):
    """Host adjusts AI difficulty in lobby."""
    room_code = data.get('room_code')
    game = games.get(room_code)
    if not game or game['phase'] != 'lobby':
        return
    # Host-only
    if game['players'][0].get('sid') != request.sid:
        return
    difficulty = data.get('ai_difficulty', 'hard')
    if difficulty not in ['easy', 'medium', 'hard', 'impossible', 'random']:
        difficulty = 'easy'
    game['ai_difficulty'] = difficulty
    broadcast_game_state(room_code)

@socketio.on('update_privacy')
def handle_update_privacy(data):
    """Host toggles game privacy in lobby."""
    room_code = data.get('room_code')
    game = games.get(room_code)
    if not game or game['phase'] != 'lobby':
        return
    # Host-only
    if game['players'][0].get('sid') != request.sid:
        return
    game['is_private'] = bool(data.get('is_private', False))
    broadcast_game_state(room_code)

# Authentication Socket Events
@socketio.on('register')
def handle_register(data):
    """Handle user registration."""
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    avatar = data.get('avatar', '🏴‍☠️')

    success, message, user_data = create_user(username, password, avatar)

    if success:
        # Create session token
        token = create_session(user_data['username'], user_data['avatar'], user_data['wins'], user_data.get('coins', 50))
        emit('register_success', {
            'token': token,
            'username': user_data['username'],
            'avatar': user_data['avatar'],
            'wins': user_data['wins'],
            'coins': user_data.get('coins', 50)
        })
        broadcast_leaderboard_update()
    else:
        emit('register_error', {'message': message})

@socketio.on('login')
def handle_login(data):
    """Handle user login."""
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    success, message, user_data = authenticate_user(username, password)

    if success:
        # Update last login
        update_last_login(user_data['username'])

        # Create session token
        token = create_session(user_data['username'], user_data['avatar'], user_data['wins'], user_data.get('coins', 50))
        emit('login_success', {
            'token': token,
            'username': user_data['username'],
            'avatar': user_data['avatar'],
            'wins': user_data['wins'],
            'coins': user_data.get('coins', 50)
        })
    else:
        emit('login_error', {'message': message})

@socketio.on('logout')
def handle_logout(data):
    """Handle user logout."""
    token = data.get('token')
    if token:
        invalidate_session(token)
    emit('logout_success', {'message': 'Fair winds and following seas! ⛵'})

@socketio.on('validate_token')
def handle_validate_token(data):
    """Validate session token on page load."""
    token = data.get('token')
    session_data = validate_session(token)

    if session_data:
        # Refresh user data from database
        user_data = get_user_by_username(session_data['username'])
        if user_data:
            session_data['wins'] = user_data['wins']
            session_data['coins'] = user_data.get('coins', 50)
            emit('token_valid', {
                'username': user_data['username'],
                'avatar': user_data['avatar'],
                'wins': user_data['wins'],
                'coins': user_data.get('coins', 50)
            })
        else:
            emit('token_invalid')
    else:
        emit('token_invalid')

@socketio.on('update_avatar')
def handle_update_avatar(data):
    """Update a user's avatar in the database."""
    token = data.get('token')
    avatar = data.get('avatar')
    session_data = validate_session(token)
    if session_data and avatar:
        if update_user_avatar(session_data['username'], avatar):
            session_data['avatar'] = avatar
            emit('avatar_updated', {'avatar': avatar})
            broadcast_leaderboard_update()
        else:
            emit('avatar_update_error', {'message': 'Failed to update avatar'})

@socketio.on('get_leaderboard')
def handle_get_leaderboard():
    """Send current leaderboard (Most Treasure) to client."""
    leaderboard = get_top_by_coins(5)
    emit('leaderboard_update', {'top_pirates': leaderboard})

@socketio.on('get_coins')
def handle_get_coins(data):
    """Get a user's coin balance."""
    token = data.get('token')
    session_data = validate_session(token)
    if session_data:
        coins = get_user_coins(session_data['username'])
        rank = get_user_rank(session_data['username'])
        emit('coins_update', {'coins': coins, 'rank': rank})

@socketio.on('get_my_rank')
def handle_get_my_rank(data):
    """Get the requesting user's rank and coins."""
    token = data.get('token')
    session_data = validate_session(token)
    if session_data:
        coins = get_user_coins(session_data['username'])
        rank = get_user_rank(session_data['username'])
        emit('my_rank_update', {'coins': coins, 'rank': rank, 'username': session_data['username']})

@socketio.on('spend_coins')
def handle_spend_coins(data):
    """Spend coins from a user's account (for ghost bets)."""
    token = data.get('token')
    amount = data.get('amount', 0)
    session_data = validate_session(token)
    if session_data and amount > 0:
        current = get_user_coins(session_data['username'])
        if current >= amount:
            new_balance = increment_user_coins(session_data['username'], -amount)
            session_data['coins'] = new_balance
            rank = get_user_rank(session_data['username'])
            emit('coins_update', {'coins': new_balance, 'rank': rank})
        else:
            rank = get_user_rank(session_data['username'])
            emit('coins_update', {'coins': current, 'rank': rank, 'error': 'Not enough coins!'})

@socketio.on('award_coins')
def handle_award_coins(data):
    """Award coins to a user (snake game, quest rewards)."""
    token = data.get('token')
    amount = data.get('amount', 0)
    source = data.get('source', '')
    session_data = validate_session(token)
    if session_data and amount > 0:
        new_balance = increment_user_coins(session_data['username'], amount)
        session_data['coins'] = new_balance
        rank = get_user_rank(session_data['username'])
        emit('coins_update', {'coins': new_balance, 'rank': rank})
        broadcast_leaderboard_update()

# Admin config events
ADMIN_PASSWORD = 'SantoIsCool'

@socketio.on('admin_auth')
def handle_admin_auth(data):
    """Verify admin password."""
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        users = get_all_users()
        emit('admin_auth_success', {'users': users})
    else:
        emit('admin_auth_error', {'message': 'Wrong password, landlubber!'})

@socketio.on('admin_reset_user')
def handle_admin_reset_user(data):
    """Reset a specific user's wins."""
    password = data.get('password', '')
    username = data.get('username', '')
    if password != ADMIN_PASSWORD:
        emit('admin_auth_error', {'message': 'Unauthorized!'})
        return
    if reset_user_wins(username):
        users = get_all_users()
        emit('admin_reset_success', {'message': f"{username}'s wins reset to 0!", 'users': users})
        broadcast_leaderboard_update()
    else:
        emit('admin_reset_error', {'message': f"Failed to reset {username}"})

@socketio.on('admin_reset_all')
def handle_admin_reset_all(data):
    """Reset all users' wins."""
    password = data.get('password', '')
    if password != ADMIN_PASSWORD:
        emit('admin_auth_error', {'message': 'Unauthorized!'})
        return
    if reset_all_wins():
        users = get_all_users()
        emit('admin_reset_success', {'message': 'All pirate wins reset to 0!', 'users': users})
        broadcast_leaderboard_update()
    else:
        emit('admin_reset_error', {'message': 'Failed to reset leaderboard'})

@socketio.on('admin_set_coins')
def handle_admin_set_coins(data):
    """Set a user's coin balance."""
    password = data.get('password', '')
    if password != ADMIN_PASSWORD:
        emit('admin_auth_error', {'message': 'Unauthorized!'})
        return
    username = data.get('username', '')
    amount = data.get('amount', 0)
    if not username or amount < 0:
        emit('admin_reset_error', {'message': 'Invalid input'})
        return
    set_user_coins(username, amount)
    users = get_all_users()
    emit('admin_reset_success', {'message': f'Set {username}\'s coins to {amount}', 'users': users})
    broadcast_leaderboard_update()

@socketio.on('debug_reveal_dice')
def handle_debug_reveal_dice(data):
    """Return all players' actual dice for debug mode."""
    room_code = data.get('room_code')
    game = games.get(room_code)
    if not game or game['phase'] not in ['bidding', 'reveal', 'game_over']:
        return
    result = []
    for p in game['players']:
        result.append({
            'name': p['name'],
            'dice': p['dice'] if p['num_dice'] > 0 else [],
            'num_dice': p['num_dice']
        })
    emit('debug_dice_data', {'players': result})

if __name__ == '__main__':
    import os

    # Check if running in production (Docker)
    is_production = os.environ.get('FLASK_ENV') == 'production'

    if is_production:
        # Production mode - use gevent
        print("\n" + "="*50)
        print("  LIAR'S DICE - Production Server")
        print("="*50)
        print(f"\n  Server running on port 5001")
        print("="*50 + "\n")

        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    else:
        # Development mode
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        print("\n" + "="*50)
        print("  LIAR'S DICE - Multiplayer Server")
        print("="*50)
        print(f"\n  Local play: http://127.0.0.1:5001")
        print(f"  Network play: http://{local_ip}:5001")
        print("\n  Share the Network URL with other players!")
        print("="*50 + "\n")

        socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
