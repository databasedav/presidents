var SortedMap = require("collections/sorted-map")

export default function state () {
  return {
    cards: new SortedMap(),
    // TODO: remove once Vue supports maps; change CardBox getters to cards map
    cards_arr: new Array(),
    // TODO: remove once Vue supports maps; change CardBox getters to cards map
    cards_selected_arr: Array(53).fill(false),
    current_hand: Array,
    stored_hands: new Map(),
    unlocked: false,
    pass_unlocked: false,
    current_hand_str: '',
    snackbar: false,
    alert: String,
    message: '',
    hand_in_play: [],
    hand_in_play_desc: '',
    on_turn: false,
    spot: Number,
    trading: false,
    asker: false,
    asking_options: new Map([...Array(14).slice(1, 14)].map((_, i) => [i+1, false])),
    // TODO: use a map for this as well when Vue supports reactive maps
    asking_options_arr: [...Array(14).keys()].slice(1, 14),  // [1, ..., 13]
    // TODO: use a map for this as well when Vue supports reactive maps
    asking_options_selected_arr: Array(14).fill(false),
    giver: false,
    alt_play_button_str: String,
    giving_options_arr: Array(53).fill(false),
    takes_remaining: Number,
    gives_remaining: Number,
    cards_remaining: Array(4).fill(13)
  }
}
