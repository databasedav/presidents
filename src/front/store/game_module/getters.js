export default {
  at_least_one_card_selected(state) {
    return state.cards_selected_arr.some(selected => selected);
  },

  at_least_one_ask_value_selected(state) {
    return state.asking_options_selected_arr.some(selected => selected);
  },

  alt_play_button_str(state, getters) {
    // TODO: better to handle this in backend somehow?
    if (getters.at_least_one_card_selected) {
      return "give";
    } else if (getters.at_least_one_ask_value_selected) {
      return "ask";
    } else {
      return "ask/give";
    }
  }
};
