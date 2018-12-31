import Vue from 'vue'
import Vuex from 'vuex'
import { createSocketioPlugin } from 'vuex-socketio-plugin'
import io from 'socket.io-client'


Vue.use(Vuex)



export default new Vuex.Store({
  state: {
    nickname: ''
  },

  mutations: {
    set_nickname (state, nickname) {
      state.nickname = nickname
    }
  }
})
