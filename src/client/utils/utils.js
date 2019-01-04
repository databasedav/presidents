import store from '../store/store'
import state from '../store/player_store/state'
import mutations from '../store/player_store/mutations'
import getters from '../store/player_store/getters'

// import { create_namespaced_player_socket_plugin } from "../store/plugins"

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

function createSinglePlayerStore () {
  return {
    strict: process.env.NODE_ENV !== 'production',
      namespaced: true,
      state,
      getters,
      mutations,
      // plugins: [create_namespaced_player_socket_plugin(socket, namespace)]
  }
}

function register_namespaced_module (namespace, module) {
  store.registerModule(namespace, module)
}

export { namespaced_getter, createSinglePlayerStore, register_namespaced_module }