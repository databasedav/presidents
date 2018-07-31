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
  },
  mutations: {
    add_card_to_spot (state, payload) {
      state.cards[payload.spot].push(payload.card)
    },
    SOCKET_DEAL_CARDS (state, payload) {
      state.cards.splice(payload.spot, 1, payload.cards)
    },
    SOCKET_UPDATE_HAND_DESC (state, payload) {
      state.current_hands_desc.splice(payload.spot, 1, payload.desc)
    }
  }
})
