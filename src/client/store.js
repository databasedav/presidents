import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    // raw card numbers (i.e. 1-52)
    cards: [
      [],
      [],
      [],
      []
    ],
    // bools for whether or not selected
    is_selected: [
      [],
      [],
      [],
      []
    ],
    current_hands: [
      [],
      [],
      [],
      []
    ],
    current_hands_desc: [
      'fuck',
      null,
      null,
      null
    ],
    stored_hands: [
      [],
      [],
      [],
      []
    ],
  },
  getters: {
    cards_in_spot: (state) => (spot) => {
      return state.cards[spot]
    },
    hand_desc_in_spot: (state) => (spot) => {
      return state.current_hands_desc[spot]
    },
    current_hand_in_spot: (state) => (spot) => {
      return state.current_hands[spot]
    }
  },
  mutations: {
    add_card_to_spot (state, payload) {
      state.cards[payload.spot].push(payload.card)
    },
    SOCKET_SET_ALL_CARDS (state, payload) {
      state.cards = payload.cards
    },
    SOCKET_SET_IS_SELECTED_ARR (state, payload) {
      state.is_selected = payload.arr
    },
    SOCKET_UPDATE_CURRENT_HAND (state, payload) {
      state.current_hands.splice(payload.spot, 1, payload.hand)
    },
    SOCKET_UPDATE_HAND_DESC (state, payload) {
      state.current_hands_desc.splice(payload.spot, 1, payload.desc)
    }
  }
})
