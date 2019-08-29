import Vue from 'vue'
import Vuex from 'vuex'

import { server_browser_plugin, server_plugin } from './plugins'

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
    plugin_server_browser (context, payload) {
      server_browser_plugin(payload.rbnsp)(this)
    },

    plugin_server (context, payload) {
      server_plugin(payload)(this)
    },
  }
})
