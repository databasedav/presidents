var SortedMap = require("collections/sorted-map");

export default _ => {
  return {
    socket: null,
    cards: new SortedMap(),
    // TODO: remove once Vue supports maps; change CardBox getters to cards map
    cards_arr: new Array(),
    // TODO: remove once Vue supports maps; change CardBox getters to cards map
    cards_selected_arr: Array(53).fill(false),
    current_hand: Array,
    stored_hands: new Map(),
    unlocked: false,
    pass_unlocked: false,
    current_hand_str: "",
    snackbar: false,
    alert: String,
    message: "",
    hand_in_play: [],
    hand_in_play_desc: "",
    on_turn: false,
    spot: Number,
    trading: false,
    asker: false,
    asking_options: new Map(
      [...Array(14).slice(1, 14)].map((_, i) => [i + 1, false])
    ),
    // TODO: use a map for this as well when Vue supports reactive maps
    asking_options_arr: Array(13).fill(1).map((x, y) => x + y),  // [...Array(14).keys()].slice(1, 4) not working
    // TODO: use a map for this as well when Vue supports reactive maps
    asking_options_selected_arr: Array(14).fill(false),
    giver: false,
    alt_play_button_str: String,
    giving_options_arr: Array(53).fill(false),
    takes: Number,
    gives: Number,
    cards_remaining: Array(4).fill(13),
    names: Array(4).fill(""),
    dot_colors: Array(4).fill("red"),
    turn_times: Array(4).fill(0),
    reserve_times: Array(4).fill(0),
    turn_time_states: Array(4).fill(false),
    reserve_time_states: Array(4).fill(false),
    stored_hand_lists: new Map(),
    stored_hand_selected: new Map()
  };
};
