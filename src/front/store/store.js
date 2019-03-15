import Vue from 'vue'
import Vuex from 'vuex'
import io from 'socket.io-client'

import { room_browser_plugin } from '../utils/utils'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
    server: 'US-West'
  },

  mutations: {
    set_nickname (state, payload) {
      state.nickname = payload.nickname
    },

    SOCKET_REFRESH () {
      console.log('fuck')
    }
  }
})
