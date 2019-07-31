class BotFarm:
    def __init__(self) -> None:
        self._num_bots: int = 0
        self._bot_dict: Dict[str, Bot]

# TODO: another thing that receives rounds that have just been completed
#       and then replays all the moves with assertions and then put the
#       rounds into a database that just marks that they have passed
#       playing the game with assertions

class Bot:
    '''
    Bots broadly perform two functions. The first is to replay 
    presidents rounds played by humans with assertions in order to
    guarantee that the rules of my game are implemented fucking
    perfectly. The second is to auto play against each other and with
    other players; they can autoplay at various levels of skill based on
    artificial intelligence and machine learning (wow!).

    Interfaces directly with GameClicks table.
    '''
    actions = {
        'card_click': 'add_or_remove_card',
        'unlock': 'unlock_handler',
        'lock': 'lock_handler',
        'play': 'maybe_play_current_hand',
        'unlock_pass': 'maybe_unlock_pass_turn',
        'pass_turn': 'maybe_pass_turn',
        'select_asking_option', 'set_selected_asking_option',
        'ask': 'ask_for_card',
        'give': 'give_card'
    }


    def __init__(self):
        self.game = None
        
    def take_action(self):
        '''
        ...against humanity...
        '''
        
    

class ClientBot(Bot, AsyncClient):
    '''
    The client bot has the same 'view' of the game state that a human
    player does and communicates with the server with the same socket.io
    events that the web client does.
    '''
    def __init__(self)
        ...
    
    def 

# TODO: orchestrator for client bots that auto rejoins them to reset
#       games to avoid having to deal with trading