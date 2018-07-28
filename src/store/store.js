import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export const store = new Vuex.Store({
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
    stored_hands: [
      [],
      [],
      [],
      []
    ]
  },
  getters: {
    cards_in_spot: (state) => (spot) => {
      return state.cards[spot]
    }
  },
  mutations: {
    add_card_to_spot (state, payload) {
      state.cards[payload.spot].push(payload.card)
    }
  }
})
