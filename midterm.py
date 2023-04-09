from enum import Enum
from random import shuffle
import random 
import logging

# Code below divided into  sections for ease of reading.
# 0- Notes and remarks 1- Parameters 2- Utilities 3- The actual algorithm 4- test and game loop

# --------------------- 0- Notes and remarks --------------------- 
#
# - Limitations:
#    - Human is always the first player. Computer is always the second player.
#
# - Assumptions:
#       When each player takes 26 cards no majority card points awarded. Game ends with 13 points + pistis.
# - Usage:
#       - Run:
#               python midterm.py
#       You will be prompted your hand and the cards in the middle. Write the index of your card
#       you want to play(0,1,2,3), then press enter. Wait for computer's move. Repeat until end.
#       The scores you see in the last prompt are final scores. When computer plays a taking move
#       The cards on the ground will disappear in the next prompt. It is a bit confusing but 
#       working as intended.
#
# - How will you verify that the algorithm is better than random?
#       - It is better than random. Play the 0 index card constantly. You should see computer 
#         winning most of the games this way.
#       - Alternatively, see test_play_many_game_against_random_player_and_print_stats() method.
#         This test is run when TEST parameter is set to True. Takes 5-10 min time to run though.
#         output from when I ran it:
#              "Out of 20 games, random player won 136 points. smarter AI won 271 points."
#      
# - See the code if you need to verify the game logic. I am not providing methodology to configure
#   cards dealt. When script starts, a random deck is shuffled. The shuffled deck is consistent
#   throughout the game.
#   
# - Algorithm outline
#       1- At any point suggest_next_card_to_play(...) method generates 
#          many(count configurable below) possible hands for the opponent
#       2- For each opponent hand generated, the game is forked many times to generate 
#          every possible sequence until the end of current round(i.e at most 4!*4! continuations). 
#          Here game forking means creating alternate games where we assign random(but possible)
#          cards to the opponent.
#       3- For each possible continuation to the end of current round(i.e. one of 6 rounds in a game),
#          expected score for the rest of the whole game is estimated (heuristics). (Up to 
#          <number of guessed opponent hands> * 4! * 4! many round end estimations made.)
#       4- Finally, the card that is best to play against most opponent hands is chosen. The end goal 
#          of the optimization is configurable. See OPTIMIZE_FOR_MORE_POINTS_THAN_OPPONENT_IN_SINGLE_GAME
#          vs OPTIMIZE_FOR_MAX_POINTS_IN_SINGLE_GAME parameters below.
# - I have not written rounds to text files. I did not get what writing to files is for. 
#




# -------------   1- Parameters -----------------------
# Run tests
TEST = False

# Set logging to debug to see extra details.
logging.basicConfig(level=logging.INFO)

# Higher number is slower to calculate but produces more accurate results.
NUM_RANDON_GUESSES_FOR_OPPONENT_HAND = 30

# Looking at midterm question, it is not clear what the end goal of the game is.
# Select the end goal by setting it to 1 or 2. 
OPTIMIZE_FOR_MAX_POINTS_IN_SINGLE_GAME = 1
OPTIMIZE_FOR_MORE_POINTS_THAN_OPPONENT_IN_SINGLE_GAME = 2
GOAL = 1

# ------------   2- Utilities -----------------------
CARD_TYPE_MAP = {
    0: 'Maca',   1: "Kupa",    2: "Sinek",   3: "Karo",
}
CARD_VALUE_MAP = {
    0: 'As',1: '2',2: '3',3: '4',4: '5',5: '6',6: '7',7: '8',8: '9',9: '10',10: 'Vale',11: 'Kız',12: 'Papaz'
}

def card_to_text(card_no):
    return CARD_TYPE_MAP[card_no // 13] + "_" + CARD_VALUE_MAP[card_no % 13]

def text_to_card(text):
    card_type, card_value = text.split("_")
    return CARD_TYPE_MAP.index(card_type) * 13 + CARD_VALUE_MAP.index(card_value)

class Pisti:
    class Player(Enum):
        P1 = 0 # plays first card of the game
        P2 = 1 # plays last card of the game
        NONE = 2 

    def __init__(self, deck = None):
        if deck is None:
            self.deck = list(range(52))
            shuffle(self.deck)
            # Starting card cannot be vale
            while(self.deck[3] % 13 == 10):
                shuffle(self.deck)
        else:
            self.deck = deck
        self.cards_thrown = []
        self.last_round_dealt = 0
        
    def hand_of_player(self, player):
        return set(self.deck[self.last_round_dealt*8+ 4:self.last_round_dealt*8+8] 
                         if player == Pisti.Player.P1 else self.deck[self.last_round_dealt*8+ 8:self.last_round_dealt*8+12]) - set(self.cards_thrown)
        
    def swap_cards(deck, index1, index2):
        dummy = deck[index1]
        deck[index1] = deck[index2]
        deck[index2] = dummy
    def swap_player_hand(self, new_hand,player):
        """ Returns a modified clone of the game where the player in the clone has the new hand"""
        new_hand_copy = list(new_hand.copy())
        copy =  Pisti(self.deck.copy())
        copy.cards_thrown = self.cards_thrown.copy()
        copy.last_round_dealt = self.last_round_dealt
        current_hand = list(self.hand_of_player(player)).copy()
        logging.debug("deck before swap: {}".format(",".join([str(i) for i in copy.deck])))
        if len(current_hand) != len(new_hand_copy):
            raise Exception("Hand lengths do not match")
        if(len(set(new_hand_copy)) != len(new_hand_copy)):
            raise Exception("The new hand contains duplicates.")
        if set(copy.cards_thrown) &  set(new_hand_copy):
            raise Exception("The new hand contains already played cards.")
         
        non_overlapping_new_hand = list(set(new_hand_copy) - set(current_hand))
        non_overlapping_current_hand = list(set(current_hand) - set(new_hand_copy))
        for index,card in enumerate(non_overlapping_new_hand):
            Pisti.swap_cards(copy.deck , copy.deck.index(card), copy.deck.index(non_overlapping_current_hand[index]))
        
        logging.debug("deck after  swap: {}".format(",".join([str(i) for i in copy.deck])))
        return copy
        
    def score_of(cards, count_pisti = True):
        """ 'cards' is a list."""
        score = 0
        if count_pisti and len(cards)==2 and cards[0]%13 == cards[1]%13:
            score +=10
        for card in cards:
            if card == 3*13 + 9: # karo 10
                score += 3
            if card == 2*13 + 1: # sinek 2
                score += 2
            if card % 13 == 0: # as
                score+=1
            if card % 13 == 10: # vale
                score +=1
        return score    
    
    def takes(prev, next):
        """ Return True if next is vale or prev(face) == next(face) """
        return next%13 == prev%13 or next%13 == 10
        
    def get_game_view_of_player(self, player):
        closed_cards_on_ground = self.deck[0:3]
        open_cards_on_ground = [self.deck[3]]
        cards_taken = {Pisti.Player.P1 : [], Pisti.Player.P2 : [],Pisti.Player.NONE : []}
        score = {Pisti.Player.P1 : 0, Pisti.Player.P2 : 0,Pisti.Player.NONE : 0}
        last_taker = Pisti.Player.NONE
        face_down_cards_taker = Pisti.Player.NONE
        for index, card in enumerate(self.cards_thrown):
            player_throwing =  Pisti.Player.P1 if index%2 == 0 else Pisti.Player.P2
            open_cards_on_ground.append(card)
            # Checking taking condition
            if len(open_cards_on_ground) > 1 and Pisti.takes(open_cards_on_ground[-2], open_cards_on_ground[-1]):
                face_down_cards_taker = player_throwing if face_down_cards_taker == Pisti.Player.NONE else face_down_cards_taker
                cards_taken_this_round = closed_cards_on_ground if last_taker == Pisti.Player.NONE else list()
                last_taker = player_throwing
                cards_taken_this_round.extend(open_cards_on_ground)    
                score[player_throwing] += Pisti.score_of(cards_taken_this_round)
                cards_taken[player_throwing].extend(cards_taken_this_round)
                open_cards_on_ground = []
        # if not taken assign last cards on ground to the one took the last card
        if len(self.cards_thrown) == 48:
            cards_taken[last_taker].extend(open_cards_on_ground)
            score[last_taker] += Pisti.score_of(open_cards_on_ground, count_pisti=False)
            open_cards_on_ground = []
        # Assign score due to card majority
        if(len(cards_taken[Pisti.Player.P1]) > 26):
            score[Pisti.Player.P1] += 3
        if(len(cards_taken[Pisti.Player.P2]) > 26):
            score[Pisti.Player.P2] += 3
        return {
            'face_down_cards_taker' : face_down_cards_taker,
            'known_cards_p1_took' : sorted(cards_taken[Pisti.Player.P1]),
            'known_cards_p2_took' : sorted(cards_taken[Pisti.Player.P2]),
            'known_score_p1' : score[Pisti.Player.P1],
            'known_score_p2' : score[Pisti.Player.P2],
            'open_cards_on_ground' : open_cards_on_ground,
            'face_up_card_on_ground_if_exists' : -1 if len(open_cards_on_ground) ==0 else open_cards_on_ground[-1], # -1 if no face up card
            'p1_hand' : self.hand_of_player(Pisti.Player.P1) if player == Pisti.Player.P1 else set(),
            'p2_hand' : self.hand_of_player(Pisti.Player.P2) if player == Pisti.Player.P2 else set(),
            'p1_hand_size' : len(self.hand_of_player(Pisti.Player.P1)),
            'p2_hand_size' : len(self.hand_of_player(Pisti.Player.P2)),
            'i_am': player
        }
    
    def play_card(self, card_no):
        self.cards_thrown.append(card_no)
        
    def deal_next_round(self):
        self.last_round_dealt += 1


# ----------------------- 3- The actual algorithm -----------------------
# Entry point is suggest_next_card_to_play(...) method

def estimate_game_score(pisti_game, player):
    """ Returns expected score of dict {p1:expected_score, p2:expected_score} at the end of whole 
    game given the end of round state.
    
    Uses some heuristics. More sophisticated and more accurate algorithms/simulations/statistics 
    would be too much work for midterm.
    
    It is always assumed that the face down three cards are unknown for simplicity.
    """
    game_view = pisti_game.get_game_view_of_player(player)
    expected_score={Pisti.Player.P1 : 0, Pisti.Player.P2 : 0}
    unseen_cards = set(range(52)) - set(game_view['known_cards_p1_took']) - set(game_view['known_cards_p2_took']) - set(game_view['open_cards_on_ground'])
    expected_number_of_clean_grounds = 1 if game_view['face_up_card_on_ground_if_exists'] <= 1 else 0
    num_valet_remaining = len(list(filter(lambda card:card%13 == 10 ,  unseen_cards)))
    expected_number_of_pair_takings_left = float(len(unseen_cards))/13 # back of napkin calculation
    expected_number_of_clean_grounds += float(num_valet_remaining) + float(len(list(filter(lambda card:card%13 == 10 ,  unseen_cards)))) 
    # 1-  Calculate expected score from unseen cards includes the score from 3 face down cards.
    score_of_unseen_cards = float(Pisti.score_of(unseen_cards, count_pisti = False))
    expected_score[Pisti.Player.P1] += score_of_unseen_cards/2
    expected_score[Pisti.Player.P2] += score_of_unseen_cards/2
    
    # 2- Calculate expected score from taking cards already on ground
    score_of_open_cards = float(Pisti.score_of(game_view['open_cards_on_ground'],count_pisti = False))
    expected_score[Pisti.Player.P1] += score_of_open_cards*0.6 # guess work.
    expected_score[Pisti.Player.P2] += score_of_open_cards*0.4 # guess work
    
    # 3- Calculate expected score from majority of cards held
    total_cards_taken = float( len(game_view['known_cards_p2_took']) + len(game_view['known_cards_p1_took']) + 0 if game_view['face_down_cards_taker'] == Pisti.Player.NONE else 3)
    p1_cards_taken = float(len(game_view['known_cards_p1_took']) + 3 if game_view['face_down_cards_taker'] == Pisti.Player.P1 else 0)
    p2_cards_taken = total_cards_taken - p1_cards_taken
    if(p1_cards_taken > p2_cards_taken + 10):
        expected_score[Pisti.Player.P1] += 2
        expected_score[Pisti.Player.P2] += 1
    elif(p1_cards_taken > p2_cards_taken + 20):
        expected_score[Pisti.Player.P1] += 3
        expected_score[Pisti.Player.P2] += 0   
    elif(p1_cards_taken < p2_cards_taken -10):
        expected_score[Pisti.Player.P1] += 1
        expected_score[Pisti.Player.P2] += 2
    elif(p1_cards_taken < p2_cards_taken -20):
        expected_score[Pisti.Player.P1] += 0
        expected_score[Pisti.Player.P2] += 3
    else:  
        expected_score[Pisti.Player.P1] += 1.5
        expected_score[Pisti.Player.P2] += 1.5
        
    # 4- Calculate expected score from pisti
    remaning_pisti_score = 10.0 * float(expected_number_of_clean_grounds) * expected_number_of_pair_takings_left/(float(len(unseen_cards)) + 10.0)
    expected_score[Pisti.Player.P1] += remaning_pisti_score/2
    expected_score[Pisti.Player.P2] += remaning_pisti_score/2
    
    # 5- Add the already taken score
    expected_score[Pisti.Player.P1] += game_view['known_score_p1']
    expected_score[Pisti.Player.P2] += game_view['known_score_p2']
    return expected_score

def recursively_find_the_best_card_to_play(hands,player,pisti_game):
    """ Returns triplet (best_card_to_play, expected_p1_game_end_score_if_card_played, expected_p2_game_end_score_if_card_played).
    
    hands is a dict of <Pisti.Player, integer list> (player_hand, opponent_hand)
    pisti_game is not modified a copy of it is used.
    """
    other_player = Pisti.Player.P2 if  player == Pisti.Player.P1   else Pisti.Player.P1
    if len(hands[player]) == 0:
        # no card to throw in this state. Round is over.
        expected_score = estimate_game_score(pisti_game,player)
        return (-1, expected_score[Pisti.Player.P1], expected_score[Pisti.Player.P2])
    
    max_score = -99999
    card_to_play_with_best_score = -1
    p1_score_with_best_score = 0
    p2_score_with_best_score = 0
    for card_to_play in hands[player]:
        remaining_cards = set(hands[player]) - set([card_to_play])
        forked_game = pisti_game.swap_player_hand(hands[Pisti.Player.P1], Pisti.Player.P1)
        forked_game = forked_game.swap_player_hand(hands[Pisti.Player.P2], Pisti.Player.P2)
        forked_game.play_card(card_to_play)
        _, p1_score, p2_score = recursively_find_the_best_card_to_play({player:remaining_cards, other_player:hands[other_player]}, other_player, forked_game)
        score = p1_score - p2_score
        if player == Pisti.Player.P2:
            score = -score
        if(score > max_score):
            max_score = score
            card_to_play_with_best_score = card_to_play
            p1_score_with_best_score = p1_score
            p2_score_with_best_score = p2_score
    return (card_to_play_with_best_score, p1_score_with_best_score, p2_score_with_best_score)
         
def suggest_next_card_to_play(pisti, player):
    game_view = pisti.get_game_view_of_player(player)
    # generate many possible hands for opponent
    remaining_cards = set(range(52)) - set(game_view['known_cards_p1_took']) - set(game_view['known_cards_p2_took']) - set(game_view['open_cards_on_ground']) 
    if(player == Pisti.Player.P1):
        remaining_cards -= set(game_view['p1_hand'])
    else:
        remaining_cards -= set(game_view['p2_hand'])
    remaining_cards = list(remaining_cards)
    card_occurences = {}
    card_total_score = {}
    for sample in range(NUM_RANDON_GUESSES_FOR_OPPONENT_HAND):
        if player == Pisti.Player.P1: 
            hands = {Pisti.Player.P1 :game_view['p1_hand'],Pisti.Player.P2:random.sample(remaining_cards, game_view['p2_hand_size'])}
        else:
            hands = {Pisti.Player.P1 :random.sample(remaining_cards, game_view['p1_hand_size']),Pisti.Player.P2 :game_view['p2_hand']}
         
        best_card, p1_score, p2_score = recursively_find_the_best_card_to_play(hands, player, pisti)
        if player == Pisti.Player.P1:
            expected_score = p1_score
        else:
            expected_score = p2_score
        card_occurences[best_card] = card_occurences.get(best_card, 0) + 1
        card_total_score[best_card] = card_total_score.get(best_card, 0) + expected_score
    if GOAL == OPTIMIZE_FOR_MAX_POINTS_IN_SINGLE_GAME:
        suggestion = max(card_occurences, key=lambda k:card_total_score[k]/card_occurences[k])
    elif GOAL == OPTIMIZE_FOR_MORE_POINTS_THAN_OPPONENT_IN_SINGLE_GAME:
        suggestion = max(card_occurences, key=lambda k:card_occurences[k])
    logging.debug("Best card to play next is {} aka {}".format(  suggestion, card_to_text(suggestion)))
    return suggestion
    

# -----------------------4- Tests and game loop runner  ----------------------------
def test_hand_swapping():
    p = Pisti([50,24,2,16,30,35,51,3,29,13,14,36,18,25,0,47,31,9,33,37,23,11,5,7,21,45,10,46,6,27,17,48,34,39,32,26,42,49,12,1,41,8,20,4,22,40,38,19,43,28,15,44])
    p.cards_thrown = [3]
    p = p.swap_player_hand([51,22,26], Pisti.Player.P1)
    if  not (set(p.deck[4:8]) == set([3,22,26,51])):
        raise "Hand swapping failed"    
def test_play_many_game_against_random_player_and_print_stats():
    p1_score = 0
    p2_score = 0
    game_count = 20
    for i in range(game_count):
        print("running game {} out of {}".format(i, game_count))
        game = Pisti()
        for j in range(24):
            game_view = game.get_game_view_of_player(Pisti.Player.P1)
            game.play_card(list(game_view['p1_hand'])[0])
            game.play_card(suggest_next_card_to_play(game, Pisti.Player.P2))
            if j>0 and j%4 == 3:
                game.deal_next_round()
        p1_score += game.get_game_view_of_player(Pisti.Player.P1)['known_score_p1']
        p2_score += game.get_game_view_of_player(Pisti.Player.P1)['known_score_p2']
    print("Out of {} games, random player won {} points. smarter AI won {} points.".format(game_count,p1_score, p2_score))
        
def print_game_view(pisti, player):
    hand = list(game.hand_of_player(player))
    prompt = " ".join([str(i) +":" + card_to_text(card) for i,card in enumerate(hand)])
    game_view = pisti.get_game_view_of_player(player)
    ground_str = " ".join([card_to_text(card) for card in game_view['open_cards_on_ground']])
    if(game_view['face_down_cards_taker'] == Pisti.Player.NONE):
        ground_str = "FACE_DOWN FACE_DOWN FACE_DOWN " + ground_str
    print("\n\nYour score:{}\t Known machine score:{}\t Num of cards you took:{} Num of cards machine took:{}".format(
        game_view['known_score_p1'], 
        game_view['known_score_p2'], 
        len(game_view['known_cards_p1_took']), 
        len(game_view['known_cards_p2_took'])))
    print("\n\n\t\tCards in the middle(right most is top): \t\t\t\t" + ground_str)
    print("\n\t\tYour hand is \t\t\t\t\t\t\t\t" + prompt)
    
if __name__ == '__main__':
    if TEST:
        test_hand_swapping()
        test_play_many_game_against_random_player_and_print_stats()
        exit(0)
    game = Pisti()
    for i in range(24):
        # display hand
        human_hand = list(game.hand_of_player(Pisti.Player.P1))
        if len(human_hand) == 0:
            game.deal_next_round()
            human_hand = list(game.hand_of_player(Pisti.Player.P1))
        while(True):
            print_game_view(game, Pisti.Player.P1)
            print("\nWrite index of card(number to the left of the card) to play, then enter:")
            card_played = input()
            try:
                game.play_card(human_hand[int(card_played)])
                break;
            except:
                print("Invalid input, try again")
                
        print("\n\n")
        print_game_view(game, Pisti.Player.P1)
        print("Asking machine for the move...")
        game.play_card(suggest_next_card_to_play(game, Pisti.Player.P2))
        print("\nMachine played................................................................. {}\n\n".format(card_to_text(game.cards_thrown[-1])))
    print_game_view(game, Pisti.Player.P1)
    print("\n\ngame ended.")
          