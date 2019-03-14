import Vue from 'vue'
import Vuex from 'vuex'
import io from 'socket.io-client'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
    socket: io.Socket,
    namespace: String,  // sid
    rooms: [],
    sockets: []
  },

  mutations: {
    set_nickname (state, payload) {
      state.nickname = payload.nickname
    },

    set_namespace (state, payload) {
      state.namespace = payload.namespace
    },

    attach_socket (state) {
      state.socket = io('/', { forceNew: true })
      state.socket.once('connect', () => {
        state.namespace = state.socket.id
      })
    },

    add_socket (state, payload) {
      state.socket.push(io(payload.namespace))
    },

    refresh (state, payload) {
      state.rooms = payload.rooms
    },

    set_room_dne (state, payload) {
      state.room_dne = payload.room_dne
    },

    // join_room (state) {
    //   router.push({ path: '/presidents' })
    //   // console.log(state.namespace)
    //   // this.registerModule(state.namespace, createSinglePlayerStore(state.socket, state.namespace))
    // }
  }
})
