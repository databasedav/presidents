import store from '../store/store'
import create_state from '../store/server_module/state'
import mutations from '../store/server_module/mutations'
import getters from '../store/server_module/getters'
import actions from '../store/server_module/actions'
import router from '../router'


// import { create_namespaced_player_socket_plugin } from "../store/plugins"

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

function create_server_module (rnsp) {
  return {
    strict: process.env.NODE_ENV !== 'production',
    namespaced: true,
    state: create_state(rnsp),
    getters,
    mutations,
    actions
  }
}

function create_server_browser_module (rbnsp) {
  return {
    strict: process.env.NODE_ENV !== 'production',

    namespaced: true,
    
    state: {
      rbnsp: rbnsp,
      // TODO: change to map once reactive
      servers: [],
    },
  
    mutations: {
      SOCKET_refresh (state, payload) {
        state.servers = payload.servers
      },
    },

    actions: {
      emit_refresh (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('refresh')
      },  

      emit_add_server (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('add_server', payload)
      },

      emit_join_server (context, payload) {
        this._vm.$socket[context.state.rbnsp].emit('join_server', payload)
      },

      socket_send_to_server (context, payload) {
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



export { create_server_module, create_server_browser_module, namespaced_getter, register_namespaced_module }