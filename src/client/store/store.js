import Vue from 'vue'
import Vuex from 'vuex'
import { createSocketioPlugin } from 'vuex-socketio-plugin'
import io from 'socket.io-client'
import state from './state'
import mutations from './mutations'
import getters from './getters'

Vue.use(Vuex)

function createSinglePlayerStore () {
  return {
    strict: process.env.NODE_ENV !== 'production',
    namespaced: true,
    state,
    getters,
    mutations
  }
}

// start with only 1 module and add modules for testing

export default new Vuex.Store({
  modules: {
    a: createSinglePlayerStore(),
    b: createSinglePlayerStore(),
    c: createSinglePlayerStore(),
    d: createSinglePlayerStore()
  }
})
