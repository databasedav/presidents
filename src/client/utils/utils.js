import store from '../store/store'
import state from '../store/state'
import mutations from '../store/mutations'
import getters from '../store/getters'

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

function createSinglePlayerStore () {
  return {
    strict: process.env.NODE_ENV !== 'production',
      namespaced: true,
      state,
      getters,
      mutations
  }
}

function register_namespaced_module (namespace, module) {
  store.registerModule(namespace, module)
}

export { namespaced_getter, createSinglePlayerStore, register_namespaced_module }