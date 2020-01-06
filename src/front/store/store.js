import Vue from "vue";
import Vuex from "vuex";
import router from '../router'
import { create_game_module, EVENTS } from '../utils'

// import { server_browser_plugin, server_plugin } from './plugins'

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    username: "",
    servers: [],
    alert: ''
  },

  mutations: {
    set_nickname(state, payload) {
      state.nickname = payload.nickname;
    }
  },

  actions: {
    create_game ({ dispatch }, payload) {
      axios.post('game_browser/create_game', {
        name: payload.name
      }).then(response => {
        // adding a server auto joins it
        const game_server_id = response.game_server_id
        dispatch('join_server', {
          game_server_id: game_server_id
        })
      })
    },

    join_game ({ state, commit }, payload) {
      const game_server_id = payload.game_server_id
      axios.get('game_browser/join_game', {
        game_server_id: game_server_id,
        username: state.username
      }).then(response => {
        // post kub: also returns which pod (ip/port) to connect to
        const socket = io(`game_server_server/game_server_id=${game_server_id}`, {
          forceNew: true,
          transportOptions: {
            polling: {
              extraHeaders: {
                'key': response.key
              }
            }
          }
        })
        // if connection is succesful
        socket.once('connect', _ => {
          // game server id is used as a vuex namespace because
          // I plan to support playing multiple games at the
          // same time TODO
          context.registerModule(game_server_id, create_game_module())
          commit('set_socket', {
            socket: socket
          })
          // register presidents event listeners
          EVENTS.forEach(event => {
            socket.on(event, payload => {
              commit(`${game_server_id}/${event}`, payload)
            })
          })

          router.push('presidents')
        })
      }).catch(err => {
        state.alert = err.response.detail
      })
      
    }
  }

  // actions: {
  //   plugin_server_browser (context, payload) {
  //     server_browser_plugin(payload.rbnsp)(this)
  //   },

  //   plugin_server (context, payload) {
  //     server_plugin(payload)(this)
  //   },
  // }
});
