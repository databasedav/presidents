export default {
  
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

  unlock (state, payload) {
    state.unlocked = true
  },

  lock (state, payload) {
    state.unlocked = false
  },

  clear_cards (state, payload) {
    state.cards.clear()
    state.cards_arr = new Array()
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
    state.cards_arr.push(payload.card)
  },

  update_current_hand_str (state, payload) {
    state.current_hand_str = payload.str  
  },

  remove_card (state, payload) {
    state.cards.delete(payload.card)
    // this is gross
    state.cards_arr = Array.from(state.cards.keys())
    state.cards_selected_arr.splice(payload.card, 1, false)
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
  },

  select_asking_option (state, payload) {
    state.ask_values.set(payload.value, true)
    // remove after Vue supports maps
    state.ask_values_selected_arr.splice(payload.value, 1, true)
  },

  deselect_asking_option (state, payload) {
    state.ask_values.set(payload.value, false)
    // remove after Vue supports maps
    state.ask_values_selected_arr.splice(payload.value, 1, false)
  },

  highlight_giving_options (state, payload) {
    for (var i in payload.options) {
      state.giving_options_arr.splice(payload.options[i], 1, true)
    }
  },

  removing_asking_options (state, payload) {
    
  }
}