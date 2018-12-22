export default function state () {
  return {
    // should be a map how to deal with it rn?
    // make the things I want to eventually be maps, maps rn
    // and have the components that read them deal with the 
    // conversion to lists required v-for iteration
    cards: new Map(),
    // remove once Vue supports maps; change CardBox getters to cards map
    cards_array: new Array(),
    // remove once Vue supports maps; change CardBox getters to cards map
    cards_selected_array: Array(52).fill(false),
    current_hand: Array,
    stored_hands: new Map(),
    play_unlocked: false,
    current_hand_str: '',
    snackbar: false,
    alert: String,
    hand_in_play: [],
    hand_in_play_desc: '',
    on_turn: false,
    spot: Number
  }
}
