import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    cards: [
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
    current_hands_desc: 'fuck',
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
    // hand_desc_in_spot (state) {
    //   return state.current_hands_desc
    // },
  },
  mutations: {
    add_card_to_spot (state, payload) {
      state.cards[payload.spot].push(payload.card)
    },
    // WHY WONT THIS WORK
    SOCKET_HEY(state, payload) {
      state.current_hands_desc = payload.desc
    },
  }
})
