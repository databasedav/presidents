import Vue from 'vue'

export default function mutations () {
  return {
    // SOCKET_ASSIGN_CARDS (state, payload) {
    
    // },
  
    // SOCKET_UNLOCK_PLAY (state, payload) {
    //   state.play_unlocked = true
    // },
  
    // SOCKET_LOCK_PLAY (state, payload) {
    //   state.play_unlocked = false
    // },
  
    // SOCKET_SET_CARDS_WITH_SELECTION (state, payload) {
    //   state.cards = payload.cards
    // },
  
    // SOCKET_UPDATE_CURRENT_HAND_ARR (state, payload) {
    //   state.current_hand = payload.arr
    // },
  
    // SOCKET_UPDATE_CURRENT_HAND_DESC (state, payload) {
    //   state.current_hand_desc = payload.desc
    // },
  
    // SOCKET_UPDATE_CURRENT_HAND_STR (state, payload) {
    //   state.current_hand_str = payload.str  
    // },

    // SOCKET_ADD_CARD (state, payload) {
    //   state.cards.set(payload.card, false)
    //   // remove after Vue supports maps
    //   state.cards_array.push(payload.card)
    // },
  
    // SOCKET_SELECT_CARD (state, payload) {
    //   state.cards.set(payload.card, true)
    //   // remove after Vue supports maps
    //   state.cards_selected_array.splice(payload.card, 1, true)
    // },
  
    // SOCKET_DESELECT_CARD (state, payload) {
    //   state.cards.set(payload.card, false)
    //   // remove after Vue supports maps
    //   state.cards_selected_array.splice(payload.card, 1, false)
    // },

    // SOCKET_CLEAR_CARDS (state, payload) {
    //   state.cards.clear()
    //   state.cards_array = new Array()
    //   state.cards_selected_array.fill(false)
    // },

    // SOCKET_STORE_HAND (state, payload) {
    //   state.stored_hands.set(payload.id, {
    //     'hand': payload.cards,
    //     'is_selected': false
    //   })
    // },
  
    // SOCKET_SELECT_HAND (state, payload) {
    //   // this might not be reactive (even when Vue supports maps)
    //   state.stored_hands.get(payload.id)['is_selected'] = true
    // },
  
    // SOCKET_DESELECT_HAND (state, payload) {
    //   // this might not be reactive (even when Vue supports maps)
    //   state.stored_hands.get(payload.id)['is_selected'] = false
    // },
    // SOCKET_ALERT (state, payload) {
    //   state.alert = payload.alert
    //   Vue.$snackbar.show(payload.alert)
    // },
    // SOCKET_DESELECT_ALL_HANDS (state, payload) {
    //   for (var i = 0; i < state.stored_hands.length; i += 1) {
    //     state.stored_hands.splice(i, 1, {
    //       'cards': state.stored_hands[i].cards,
    //       'is_selected': false
    //     })
    //   }
    // },

    

    alert (state, payload) {
      state.alert = payload.alert
      state.snackbar = true
      setTimeout(() => state.snackbar = false, 1000)
    },

    flip_turn (state, payload) {
      state.on_turn = !state.on_turn
    },

    all_off_turn (state, payload) {
      state.on_turn = false
    },

    unlock_play (state, payload) {
      state.play_unlocked = true
    },

    lock_play (state, payload) {
      state.play_unlocked = false
    },

    clear_cards (state, payload) {
      state.cards.clear()
      state.cards_array = new Array()
      state.cards_selected_arr.fill(false)
    },

    select_card (state, payload) {
      state.cards.set(payload.card, true)
      // remove after Vue supports maps
      state.cards_selected_arr.splice(payload.card, 1, true)
    },

    deselect_card (state, payload) {
      state.cards.set(payload.card, false)
      // remove after Vue supports maps
      state.cards_selected_arr.splice(payload.card, 1, false)
    },

    add_card (state, payload) {
      state.cards.set(payload.card, false)
      // remove after Vue supports maps
      state.cards_array.push(payload.card)
    },

    update_current_hand_str (state, payload) {
      state.current_hand_str = payload.str  
    },

    remove_card (state, payload) {
      state.cards.delete(payload.card)
      // this is gross
      state.cards_array = Array.from(state.cards.keys())
    },

    update_spot (state, payload) {
      state.spot = payload.spot
    },

    update_hand_in_play (state, payload) {
      state.hand_in_play = payload.hand_in_play
      state.hand_in_play_desc = payload.hand_in_play_desc
    },

    clear_hand_in_play (state, payload) {
      state.hand_in_play = []
      state.hand_in_play_desc = ''
    },

    add_trading_options (state, payload) {
      state.asking = true
    },

    set_asker (state, payload) {
      state.asker = true
    },

    set_giver (state, payload) {
      state.giver = true
    },

    set_trading (state, payload) {
      state.trading = payload.trading
      if (!state.trading) {
        state.asker = false
        state.giver = false
      }
    }
  }
}