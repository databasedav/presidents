import io from 'socket.io-client'
import state from '../store/server_module/state'
import getters from '../store/server_module/getters'
import mutations from '../store/server_module/mutations'
import actions from '../store/server_module/actions'

function server_browser_plugin (rbnsp) {
  return store => {
    store.registerModule(rbnsp, create_server_browser_module(rbnsp))
    // TODO
  }
}

function create_server_module () {
  return {
    strict: process.env.NODE_ENV !== 'production',
    namespaced: true,
    state,
    getters,
    mutations,
    actions
  }
}

const EVENTS = [
  'add_card',
  'alert',
  'clear_cards',
  'clear_hand_in_play',
  'deselect_asking_option',
  'deselect_card',
  'message',
  'remove_asking_option',
  'remove_card',
  'select_asking_option',
  'select_card',
  'set_asker',
  'set_cards_remaining',
  'set_dot_color',
  'set_giver',
  'set_gives_remaining',
  'set_giving_options',
  'set_hand_in_play',
  'set_names',
  'set_on_turn',
  'set_pass_unlocked',
  'set_spot',
  'set_takes_remaining',
  'set_time',
  'set_trading',
  'set_unlocked',
  'update_alert_str',
  'update_current_hand_str'
]

function server_plugin ({ namespace, testing=false }) {
  return store => {
    // use actual server namespace to connect
    // TODO: use single socket connection per browser
    const socket = io(`http://127.0.0.1:5000${namespace}`, { forceNew: true })
    // if testing (i.e. four player vue), use sid as namespace
    socket.once('connect', function () {
      namespace = testing ? socket.id : namespace
      store.registerModule(namespace, create_server_module())
      // register presidents event listeners
      EVENTS.forEach(event => {
        socket.on(event, payload => {
          store.commit(`${namespace}/${event}`, payload)
        })
      })
      // gives store access to namespaced socket
      store.commit(`${namespace}/set_socket`, { 'socket': socket })
    })
    return socket
  }
}


export { server_plugin, server_browser_plugin }