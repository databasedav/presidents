import store from '../store/store'
import create_state from '../store/room_module/state'
import mutations from '../store/room_module/mutations'
import getters from '../store/room_module/getters'
import actions from '../store/room_module/actions'
import router from '../router'


// import { create_namespaced_player_socket_plugin } from "../store/plugins"

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

function create_room_module (rnsp) {
  return {
    strict: process.env.NODE_ENV !== 'production',
    namespaced: true,
    state: create_state(rnsp),
    getters,
    mutations,
    actions
  }
}

function create_room_browser_module (rbnsp) {
  return {
    strict: process.env.NODE_ENV !== 'production',

    namespaced: true,
    
    state: {
      rbnsp: rbnsp,
      // TODO: change to map once reactive
      rooms: [],
    },
  
    mutations: {
      SOCKET_refresh (state, payload) {
        state.rooms = payload.rooms
      },
    },

    actions: {
      emit_refresh (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('refresh')
      },

      emit_add_room (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('add_room', payload)
      },

      emit_join_room (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('join_room', payload)
      },

      socket_send_to_room (context, payload) {
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



export { create_room_module, create_room_browser_module, namespaced_getter, register_namespaced_module }