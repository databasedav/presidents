import Vue from 'vue'
import Vuex from 'vuex'
import io from 'socket.io-client'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
    rooms: [],
    socket: io.Socket,
    room_dne: true
  },

  mutations: {
    set_nickname (state, payload) {
      state.nickname = payload.nickname
    },

    attach_socket (state) {
      state.socket = io(`//${window.location.host}`, { forceNew: true })
    },

    refresh (state, payload) {
      state.rooms = payload.rooms
    },

    set_room_dne (state, payload) {
      state.room_dne = payload.room_dne
    }
  }
})
