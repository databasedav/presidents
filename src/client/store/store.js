import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    nickname: '',
    rooms: []
  },

  mutations: {
    set_nickname (state, nickname) {
      state.nickname = nickname
    }
  }
})
