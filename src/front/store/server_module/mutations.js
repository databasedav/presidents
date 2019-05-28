export default {
  SOCKET_alert (state, payload) {
    state.alert = payload.alert
    state.snackbar = true
    setTimeout(() => state.snackbar = false, 1000)
  },

  SOCKET_set_on_turn (state, payload, callback) {
    state.on_turn = payload.on_turn
    state.times.splice(payload.spot, 1, payload.time)
    if (callback) {
      callback()
    }
  },

  SOCKET_set_pass_unlocked(state, payload) {
    state.pass_unlocked = payload.pass_unlocked
  },

  SOCKET_set_unlocked (state, payload) {
    state.unlocked = payload.unlocked
  },

  SOCKET_clear_cards (state, payload) {
    state.cards.clear()
    state.cards_arr = new Array()
    state.cards_selected_arr.fill(false)
  },

  SOCKET_select_card (state, payload) {
    state.cards.set(payload.card, true)
    // remove after Vue supports maps
    state.cards_selected_arr.splice(payload.card, 1, true)
  },

  SOCKET_deselect_card (state, payload) {
    state.cards.set(payload.card, false)
    // remove after Vue supports maps
    state.cards_selected_arr.splice(payload.card, 1, false)
  },

  SOCKET_add_card (state, payload) {
    state.cards.set(payload.card, false)
    // remove after Vue supports maps
    // also ew
    state.cards_arr = Array.from(state.cards.keys())
  },

  SOCKET_update_current_hand_str (state, payload) {
    state.current_hand_str = payload.str  
  },

  SOCKET_remove_card (state, payload) {
    state.cards.delete(payload.card)
    // TODO: this is gross
    state.cards_arr = Array.from(state.cards.keys())
    state.cards_selected_arr.splice(payload.card, 1, false)
  },

  SOCKET_set_spot (state, payload) {
    state.spot = payload.spot
  },

  SOCKET_set_hand_in_play (state, payload) {
    state.hand_in_play = payload.hand_in_play
    state.hand_in_play_desc = payload.hand_in_play_desc
  },

  SOCKET_clear_hand_in_play (state, payload) {
    state.hand_in_play = []
    state.hand_in_play_desc = ''
  },

  SOCKET_add_trading_options (state, payload) {
    state.asking = true
  },

  SOCKET_set_asker (state, payload) {
    state.asker = true
  },

  SOCKET_set_giver (state, payload) {
    state.giver = true
  },

  SOCKET_set_trading (state, payload) {
    state.trading = payload.trading
    if (!state.trading) {
      state.asker = false
      state.giver = false
    }
  },

  SOCKET_select_asking_option (state, payload) {
    state.asking_options.set(payload.value, true)
    // remove after Vue supports maps
    state.asking_options_selected_arr.splice(payload.value, 1, true)
  },

  SOCKET_deselect_asking_option (state, payload) {
    state.asking_options.set(payload.value, false)
    // remove after Vue supports maps
    state.asking_options_selected_arr.splice(payload.value, 1, false)
  },

  SOCKET_remove_asking_option (state, payload) {
    state.asking_options.delete(payload.value)
    // TODO: this is gross
    state.asking_options_arr = Array.from(state.asking_options.keys())
    state.asking_options_selected_arr.splice(payload.value, 1, false)
  },

  SOCKET_set_giving_options (state, payload) {
    for (var i in payload.options) {
      state.giving_options_arr.splice(payload.options[i], 1, payload.highlight)
    }
  },

  SOCKET_set_takes_remaining (state, payload) {
    state.takes_remaining = payload.takes_remaining
  },

  SOCKET_set_gives_remaining (state, payload) {
    state.gives_remaining = payload.gives_remaining
  },

  SOCKET_set_message (state, payload) {
    state.message = payload.message
  },

  SOCKET_set_cards_remaining (state, payload) {
    state.cards_remaining.splice(payload.spot, 1, payload.cards_remaining)
  },

  SOCKET_message (state, payload) {
    state.message += `\n${payload.message}`
  },

  SOCKET_set_names(state, payload) {
    state.names = payload.names
  },

  SOCKET_set_time(state, payload) {
    state.times.splice(payload.spot, 1, payload.time)
  },

  SOCKET_set_dot_color (state, payload) {
    state.dot_colors.splice(payload.spot, 1, payload.dot_color)
  }
}
