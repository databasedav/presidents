import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)


export default new Vuex.Store({
  state: {
    cards: [],
    current_hand: Array,
    current_hand_desc: '',
    current_hand_str: '',
    alert: '',
    // snackbar: false,
    stored_hands: [],
  },
  getters: {
    cards (state) {
      return state.cards
    },
    current_hand_desc (state) {
      return state.current_hand_desc
    },
    current_hand (state) {
      return state.current_hand
    },
    stored_hands (state) {
      return state.stored_hands
    },
    alert (state) {
      return state.alert
    },
    // snackbar (state) {
    //   return state.snackbar
    // },
    current_hand_str (state) {
      return state.current_hand_str
    }
  },
  mutations: {
    SOCKET_SET_CARDS_WITH_SELECTION (state, payload) {
      state.cards = payload.cards
    },
    SOCKET_UPDATE_CURRENT_HAND_ARR (state, payload) {
      state.current_hand = payload.arr
    },
    SOCKET_UPDATE_CURRENT_HAND_DESC (state, payload) {
      state.current_hand_desc = payload.desc
    },
    SOCKET_UPDATE_CURRENT_HAND_STR (state, payload) {
      state.current_hand_str = payload.str  
    },
    SOCKET_ADD_CARD (state, payload) {
      state.cards.push({
        'id': payload.id,
        'value': payload.value,
        'is_selected': payload.is_selected
      })
    },
    SOCKET_SELECT_CARD (state, payload) {
      state.cards.splice(state.cards.map(o => o.value).indexOf(payload.card), 1, {
        'value': payload.card,
        'is_selected': true
      })
    },
    SOCKET_DESELECT_CARD (state, payload) {
      state.cards.splice(state.cards.map(o => o.value).indexOf(payload.card), 1, {
        'value': payload.card,
        'is_selected': false
      })
    },
    SOCKET_STORE_HAND (state, payload) {
      state.stored_hands.push({
        'cards': payload.cards,
        'is_selected': false
      })
    },
    SOCKET_SELECT_HAND (state, payload) {
      i = state.stored_hands.map(hand => hand.cards.map(card => card.value)).indexOf(payload.cards)
      state.stored_hands.splice(i, 1, {
        'cards': stored_hands[i].cards,
        'is_selected': true
      })
    },
    SOCKET_DESELECT_HAND (state, payload) {
      i = state.stored_hands.map(hand => hand.cards.map(card => card.value)).indexOf(payload.cards)
      state.stored_hands.splice(i, 1, {
        'cards': stored_hands[i].cards,
        'is_selected': false
      })
    },
    SOCKET_ALERT (state, payload) {
      state.alert = payload.alert
      Vue.$snackbar.show(payload.alert)
    },
    SOCKET_DESELECT_ALL_HANDS (state, payload) {
      for (var i = 0; i < state.stored_hands.length; i += 1) {
        state.stored_hands.splice(i, 1, {
          'cards': state.stored_hands[i].cards,
          'is_selected': false
        })
      }
    }
  }
})
