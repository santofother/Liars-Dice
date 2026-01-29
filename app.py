from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
from collections import Counter
import string
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store all active games
games = {}

def generate_room_code():
    """Generate a 4-letter room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in games:
            return code

def create_game(room_code, host_name, num_ai=0):
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
        'max_players': 6
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
    pirate_names = ['Davy Jones', 'Barbossa', 'Bootstrap Bill', 'Pintel', 'Ragetti']
    random.shuffle(pirate_names)

    for i in range(game['num_ai']):
        if len(game['players']) < game['max_players']:
            game['players'].append({
                'name': pirate_names[i],
                'dice': [],
                'num_dice': 5,
                'is_human': False,
                'sid': None,
                'connected': True,
                'avatar': ['🦑', '🏴‍☠️', '⚓', '💀', '🦜'][i]
            })

def roll_all_dice(game):
    """Roll dice for all alive players."""
    for player in game['players']:
        if player['num_dice'] > 0:
            player['dice'] = [random.randint(1, 6) for _ in range(player['num_dice'])]

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
    difficulty = game.get('ai_difficulty', 'easy')

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
    """Get next alive player index."""
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
        'ai_difficulty': game.get('ai_difficulty', 'easy')
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
        player = game['players'][current]

        if player['is_human']:
            game['message'] = f"Waiting for {player['name']}..."
            break

        if player['num_dice'] <= 0:
            game['current_player'] = next_alive_player(game, current)
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
            game['current_player'] = next_alive_player(game, current)
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
            game['message'] = f"{winner['name']} WINS! The Black Pearl is theirs!"
    # Round starter rotation is handled in roll_dice

# Routes
@app.route('/')
def index():
    return render_template('index.html')

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
        for player in game['players']:
            if player.get('sid') == sid:
                player['connected'] = False
                broadcast_game_state(room_code)
                break

@socketio.on('create_game')
def handle_create_game(data):
    player_name = data.get('name', 'Captain')[:20]
    num_ai = int(data.get('num_ai', 2))
    avatar = data.get('avatar', '🏴‍☠️')
    ai_difficulty = data.get('ai_difficulty', 'easy')

    # Validate difficulty
    if ai_difficulty not in ['easy', 'medium', 'hard', 'impossible']:
        ai_difficulty = 'easy'

    room_code = generate_room_code()
    game = create_game(room_code, player_name, num_ai)
    game['players'][0]['sid'] = request.sid
    game['players'][0]['avatar'] = avatar
    game['ai_difficulty'] = ai_difficulty

    games[room_code] = game
    join_room(room_code)

    emit('game_created', {'room_code': room_code})
    emit('game_state', get_game_state_for_player(game, request.sid))

@socketio.on('join_game')
def handle_join_game(data):
    room_code = data.get('room_code', '').upper()
    player_name = data.get('name', 'Sailor')[:20]
    avatar = data.get('avatar', '🏴‍☠️')

    game = games.get(room_code)
    if not game:
        emit('error', {'message': 'Game not found!'})
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

        join_room(room_code)
        game['message'] = f"{reconnecting_player['name']} has rejoined the crew!"

        emit('game_created', {'room_code': room_code})  # So client knows they're in
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
                emit('error', {'message': 'You are already in the waiting list!'})
                return

            if len(game['waiting_players']) >= 4:  # Limit waiting players
                emit('error', {'message': 'Waiting list is full!'})
                return

            game['waiting_players'].append({
                'name': player_name,
                'dice': [],
                'num_dice': 5,
                'is_human': True,
                'sid': request.sid,
                'connected': True,
                'avatar': avatar,
                'is_waiting': True
            })

            join_room(room_code)
            game['message'] = f"{player_name} is waiting to join next game!"

            emit('game_created', {'room_code': room_code})
            emit('waiting_status', {'message': 'You are spectating. You will join when the game returns to lobby!'})
            broadcast_game_state(room_code)
            return

    # Normal join during lobby phase
    if len([p for p in game['players'] if p['is_human']]) >= game['max_players'] - game['num_ai']:
        emit('error', {'message': 'Game is full!'})
        return

    # Check if name already taken (add suffix if so)
    existing_names = [p['name'].lower() for p in game['players']]
    original_name = player_name
    counter = 1
    while player_name.lower() in existing_names:
        player_name = f"{original_name}_{counter}"
        counter += 1

    game['players'].append({
        'name': player_name,
        'dice': [],
        'num_dice': 5,
        'is_human': True,
        'sid': request.sid,
        'connected': True,
        'avatar': avatar
    })

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
        emit('error', {'message': 'Only the host can start the game!'})
        return

    # Add AI players
    add_ai_players(game)

    human_count = len([p for p in game['players'] if p['is_human']])
    if human_count + game['num_ai'] < 2:
        emit('error', {'message': 'Need at least 2 players!'})
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
    game['phase'] = 'bidding'
    game['current_bid'] = None
    game['current_bidder'] = None
    game['round_history'] = []

    alive = get_alive_players(game)

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
        emit('error', {'message': "It's not your turn!"})
        return

    if not is_valid_bid(game, quantity, face):
        emit('error', {'message': 'Invalid bid! Must be higher than current bid.'})
        return

    game['current_bid'] = (quantity, face)
    game['current_bidder'] = game['current_player']
    game['round_history'].append({
        'player': current_player['name'],
        'action': 'bid',
        'bid': f"{quantity}x {face}s"
    })

    game['current_player'] = next_alive_player(game, game['current_player'])
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
        emit('error', {'message': 'Nothing to challenge!'})
        return

    current_player = game['players'][game['current_player']]
    if current_player.get('sid') != request.sid:
        emit('error', {'message': "It's not your turn!"})
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
        emit('error', {'message': 'Only the host can return to lobby!'})
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

if __name__ == '__main__':
    import os

    # Check if running in production (Docker)
    is_production = os.environ.get('FLASK_ENV') == 'production'

    if is_production:
        # Production mode - use gevent
        print("\n" + "="*50)
        print("  LIAR'S DICE - Production Server")
        print("="*50)
        print(f"\n  Server running on port 5000")
        print("="*50 + "\n")

        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    else:
        # Development mode
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        print("\n" + "="*50)
        print("  LIAR'S DICE - Multiplayer Server")
        print("="*50)
        print(f"\n  Local play: http://127.0.0.1:5000")
        print(f"  Network play: http://{local_ip}:5000")
        print("\n  Share the Network URL with other players!")
        print("="*50 + "\n")

        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
