import Vue from "vue";
import Vuex from "vuex";
import router from '../router'
import { create_game_module, EVENTS } from '../utils'
import axios from 'axios'
import io from 'socket.io-client'

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    username: "",
    games: [],
    alert: '',
    testing_sids: []
  },

  mutations: {
    set_username(state, payload) {
      state.username = payload.username;
    }
  },

  actions: {
    create_game ({ dispatch }, payload) {
      axios.post('/create_game', {  // TODO: fix api routes
        name: payload.name
      }).then(response => {
        // adding a server auto joins it
        dispatch('join_game', {game_id: response.data.game_id})
      })
    },

    join_game ({ state, commit }, payload) {
      const game_id = payload.game_id
      return axios.put('/join_game', {
        game_id: game_id,
        username: payload.testing_username || state.username
      }).then(response => {
        const socket = io('/', {  // first arg is the namespace
          path: '/socket.io',
          forceNew: true,
          reconnection: false,
          transportOptions: {
            polling: {
              extraHeaders: {
                'game_id': game_id,
                'game_key': response.data.game_key
              }
            }
          }
        })
        // if connection is succesful
        socket.once('connect', _ => {
          // game id is used as a vuex namespace because
          // I plan to support playing multiple games at the
          // same time TODO
          // for testing, the sid is used
          const sid = socket.io.engine.id
          const namespace = payload.testing ? sid : game_id
          // need to do this because otherwise game views cannot use the sid
          // as the vuex namespace during testing
          if (payload.testing) {
            state.testing_sids.push(sid)
          }
          this.registerModule(namespace, create_game_module())
          commit(`${namespace}/set_socket`, {socket: socket})
          // register presidents event listeners
          EVENTS.forEach(event => {
            socket.on(event, payload => {
              commit(`${namespace}/${event}`, payload)
            })
          })

          if (!payload.testing) {
            router.push({ name: 'presidents', params: { game_id } })
          }
        })
      })
    },

    refresh_games ({ state }, payload) {
      axios.get('/get_games').then(response => {state.games = response.data.games})
    }
  }
});
