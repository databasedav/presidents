import store from '../store/store'
import create_state from '../store/room_module/state'
import mutations from '../store/room_module/mutations'
import getters from '../store/room_module/getters'
import router from '../router'

// import { create_namespaced_player_socket_plugin } from "../store/plugins"

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

function create_room_module (socket) {
  return {
    strict: process.env.NODE_ENV !== 'production',
    namespaced: true,
    state: create_state(socket),
    getters,
    mutations,
  }
}

function create_room_browser_module (socket) {
  
  return {

    strict: process.env.NODE_ENV !== 'production',

    namespaced: true,
    
    state: {
      socket: socket,
      // TODO: change to map once reactive
      rooms: []
    },
  
    mutations: {
      SOCKET_REFRESH (state, payload) {
        state.rooms = payload.rooms
      },
    },

    actions: {
      socket_sendToRoom (payload) {
        router.push({
          name: 'presidents',
          params: {
            rnsp: payload.rnsp
          }
        })
      }
    }
  }
}



function register_namespaced_module (namespace, module) {
  store.registerModule(namespace, module)
}



export { create_room_browser_module, namespaced_getter, createSinglePlayerStore, register_namespaced_module }