import Vue from 'vue'
import Vuex from 'vuex'
import io from 'socket.io-client'

import { room_browser_plugin, room_plugin } from './plugins'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
  },

  mutations: {
    set_nickname (state, payload) {
      state.nickname = payload.nickname
    }
  },

  actions: {
    plugin_room_browser (payload) {
      room_browser_plugin(payload.rbnsp)(this)
    },

    plugin_room (payload) {
      room_plugin(payload.rnsp)(this)
    }
  }
})
