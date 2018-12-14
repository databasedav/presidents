import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)


export default new Vuex.Store({
  state: {
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
    current_hand_desc: '',
    stored_hands: new Map(),
    play_unlocked: false,
    current_hand_str: '',
    alert: '',
    // snackbar: false,
    stored_hands: [],
  },
  getters: {
    cards (state) {
      return state.cards
    },

    cards_array (state) {
      return state.cards_array
    },

    cards_selected_array (state) {
      return state.cards_selected_array
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

    play_unlocked (state) {
      return state.unlocked
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

    SOCKET_ASSIGN_CARDS (state, payload) {
      
    },

    SOCKET_UNLOCK_PLAY (state, payload) {
      state.play_unlocked = true
    },

    SOCKET_LOCK_PLAY (state, payload) {
      state.play_unlocked = false
    },

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
      state.cards.set(payload.card, false)
      // remove after Vue supports maps
      state.cards_array.push(payload.card)
    },

    SOCKET_SELECT_CARD (state, payload) {
      state.cards.set(payload.card, true)
      // remove after Vue supports maps
      state.cards_selected_array.splice(payload.card, 1, true)
    },

    SOCKET_DESELECT_CARD (state, payload) {
      state.cards.set(payload.card, false)
      // remove after Vue supports maps
      state.cards_selected_array.splice(payload.card, 1, false)
    },

    SOCKET_CLEAR_CARDS (state, payload) {
      state.cards.clear()
      state.cards_array = new Array()
      state.cards_selected_array.fill(false)
    },

    SOCKET_STORE_HAND (state, payload) {
      state.stored_hands.set(payload.id, {
        'hand': payload.cards,
        'is_selected': false
      })
    },

    SOCKET_SELECT_HAND (state, payload) {
      // this might not be reactive (even when Vue supports maps)
      state.stored_hands.get(payload.id)['is_selected'] = true
    },

    SOCKET_DESELECT_HAND (state, payload) {
      // this might not be reactive (even when Vue supports maps)
      state.stored_hands.get(payload.id)['is_selected'] = false
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
