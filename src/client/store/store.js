import Vue from 'vue'
import Vuex from 'vuex'
import state from './state'
import mutations from './mutations'
import getters from './getters'

Vue.use(Vuex)


const SinglePlayerStore = {
  strict: process.env.NODE_ENV !== 'production',
  namespaced: true,
  state () {
    return state
  },
  getters,
  mutations
}

export default new Vuex.Store({
  modules: {
    a: SinglePlayerStore,
    b: SinglePlayerStore,
    c: SinglePlayerStore,
    d: SinglePlayerStore
  }
})
