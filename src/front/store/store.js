import Vue from 'vue'
import Vuex from 'vuex'
import io from 'socket.io-client'

import { room_browser_plugin } from './plugins'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
    server: 'US-West'
  },

  mutations: {
    set_nickname (state, payload) {
      state.nickname = payload.nickname
    }
  },

  actions: {
    plugin_room_browser ({ state }) {
      room_browser_plugin(state.server)(this)
    },

    plugin_room ({ state }) {
      
    }
  }
})
