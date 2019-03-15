import Vuex from 'vuex'
import io from 'socket.io-client'
import VueSocketio from 'vue-socket.io-extended'

export default {
  
  namespaced: true,
  
  state () {
    return {
      socket: io.Socket,
      // TODO: change to map once reactive
      rooms: []
    }
  },

  mutations: {
    SOCKET_REFRESH (state, payload) {
      state.rooms = payload.rooms
    },
  },
}
