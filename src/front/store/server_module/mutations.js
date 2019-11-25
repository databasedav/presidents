export default {
  add_card (state, payload) {
    state.cards.set(payload.card, false)
    // remove after Vue supports maps
    // also ew
    state.cards_arr = Array.from(state.cards.keys())
  },

  alert (state, payload) {
    state.alert = payload.alert
    state.snackbar = true
    setTimeout(() => state.snackbar = false, 1000)
  },

  clear_cards (state, payload) {
    state.cards.clear()
    state.cards_arr = new Array()
    state.cards_selected_arr.fill(false)
  },

  clear_hand_in_play (state, payload) {
    state.hand_in_play = []
    state.hand_in_play_desc = ''
  },

  deselect_asking_option (state, payload) {
    state.asking_options.set(payload.value, false)
    // remove after Vue supports maps
    state.asking_options_selected_arr.splice(payload.value, 1, false)
  },

  deselect_card (state, payload) {
    state.cards.set(payload.card, false)
    // remove after Vue supports maps
    state.cards_selected_arr.splice(payload.card, 1, false)
  },

  message (state, payload) {
    state.message += `\n${payload.message}`
  },

  remove_asking_option (state, payload) {
    state.asking_options.delete(payload.value)
    // TODO: this is gross
    state.asking_options_arr = Array.from(state.asking_options.keys())
    state.asking_options_selected_arr.splice(payload.value, 1, false)
  },

  remove_card (state, payload) {
    state.cards.delete(payload.card)
    // TODO: this is gross
    state.cards_arr = Array.from(state.cards.keys())
    state.cards_selected_arr.splice(payload.card, 1, false)
  },

  select_asking_option (state, payload) {
    state.asking_options.set(payload.value, true)
    // remove after Vue supports maps
    state.asking_options_selected_arr.splice(payload.value, 1, true)
  },

  select_card (state, payload) {
    state.cards.set(payload.card, true)
    // remove after Vue supports maps
    state.cards_selected_arr.splice(payload.card, 1, true)
  },

  set_asker (state, payload) {
    state.asker = true
  },

  set_asking_option(state, payload) {
    if (payload.old_rank) {
      state.asking_options.set(payload.old_rank, false)
      // remove after Vue supports maps
      state.asking_options_selected_arr.splice(payload.old_rank, 1, false)
    }
    state.asking_options.set(payload.new_rank, true)
    // remove after Vue supports maps
    state.asking_options_selected_arr.splice(payload.new_rank, 1, true)
  },

  set_cards_remaining (state, payload) {
    state.cards_remaining.splice(payload.spot, 1, payload.cards_remaining)
  },

  set_dot_color (state, payload) {
    state.dot_colors.splice(payload.spot, 1, payload.dot_color)
  },

  set_giver (state, payload) {
    state.giver = true
  },

  set_gives (state, payload) {
    state.gives = payload.gives
  },

  set_giving_options (state, payload) {
    for (var i in payload.options) {
      state.giving_options_arr.splice(payload.options[i], 1, payload.highlight)
    }
  },

  set_hand_in_play (state, payload) {
    state.hand_in_play = payload.hand_in_play
    state.hand_in_play_desc = payload.hand_in_play_desc
  },

  set_names(state, payload) {
    state.names = payload.names
  },

  set_on_turn (state, payload) {
    state.on_turn = payload.on_turn
  },

  set_pass_unlocked(state, payload) {
    state.pass_unlocked = payload.pass_unlocked
  },

  set_socket(state, payload) {
    state.socket = payload.socket
  },

  set_spot (state, payload) {
    state.spot = payload.spot
  },

  set_takes (state, payload) {
    state.takes = payload.takes
  },

  set_time(state, payload) {
    switch (payload.which) {
      case 'turn':
        state.turn_times.splice(payload.spot, 1, Math.max(0, payload.time - (Date.now() / 1000 - payload.timestamp)) || 0)
        state.turn_time_states.splice(payload.spot, 1, payload.start)
        break
      case 'reserve':
        state.reserve_times.splice(payload.spot, 1, Math.max(0, payload.time - (Date.now() / 1000 - payload.timestamp)) || 0)
        state.reserve_time_states.splice(payload.spot, 1, payload.start)
        break
      case 'trading':
        // using reserve time var for trading time and just changing
        // UI icon
        for (let spot = 0; spot < 4 ; spot += 1) {
          state.reserve_times.splice(spot, 1, Math.max(0, payload.time - (Date.now() / 1000 - payload.timestamp)) || 0)
          state.reserve_time_states.splice(spot, 1, payload.start)
        }
        break
    }
  },

  set_trading (state, payload) {
    state.trading = payload.trading
    if (!state.trading) {
      state.asker = false
      state.giver = false
    }
  },

  set_unlocked (state, payload) {
    state.unlocked = payload.unlocked
  },

  set_timer_state (state, payload) {
    switch (payload.which) {
      case 'turn':
        state.turn_time_states.splice(payload.spot, 1, payload.state)
        break
      case 'reserve':
        state.reserve_time_states.splice(payload.spot, 1, payload.state)
        break
      case 'trading':
        // using reserve time var for trading time and just changing
        // UI icon
        for (let spot = 0; spot < 4; spot += 1) {
          state.reserve_time_states.splice(spot, 1, payload.state)
        }
        break
    }
  },

  update_current_hand_str (state, payload) {
    state.current_hand_str = payload.str  
  }
}
