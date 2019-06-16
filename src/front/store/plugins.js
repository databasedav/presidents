import { create_server_browser_module, create_server_module } from '../utils/utils'
import Vue from 'vue'
import io from 'socket.io-client'
// import VueSocketio from 'vue-socket.io-extended'
import VueSocketIO from 'vue-socket.io'



function server_browser_plugin (rbnsp) {
  return store => {
    store.registerModule(rbnsp, create_server_browser_module(rbnsp))
    Vue.use(
      new VueSocketIO({
        connection: io(rbnsp),
        options: {
          useConnectionNamespace: true,
          namespaceName: rbnsp
        },
        debug: false,
        vuex: {
          store,
          mutationPrefix: 'SOCKET_',
          actionPrefix: 'socket_'
        }
      })
    )
  }
}

function server_plugin (rnsp) {
  return store => {
    store.registerModule(rnsp, create_server_module(rnsp))
    Vue.use(new VueSocketIO({
      connection: io(rnsp),
      options: {
        useConnectionNamespace: true,
        namespaceName: rnsp
      },
      debug: false,
      vuex: {
        store,
        mutationPrefix: 'SOCKET_',
        actionPrefix: 'socket_'
      }
    }))
  }
}

function create_namespaced_player_socket_plugin (socket, namespace) {
  
  return store => {

    function commit (namespace, event, payload) {
      store.commit(`${namespace}/${event}`, payload)
    }

    socket.on('add_card', payload => {
      commit(namespace, 'add_card', payload)
    })

    socket.on('select_card', payload => {
      commit(namespace, 'select_card', payload)
    })

    socket.on('deselect_card', payload => {
      commit(namespace, 'deselect_card', payload)
    })

    socket.on('update_current_hand_str', payload => {
      commit(namespace, 'update_current_hand_str', payload)
    })

    socket.on('update_alert_str', payload => {
      commit(namespace, 'update_alert_str', payload)
    })

    socket.on('set_hand_in_play', payload => {
      commit(namespace, 'set_hand_in_play', payload)
    })

    socket.on('alert', payload => {
      commit(namespace, 'alert', payload)
    })

    socket.on('clear_cards', payload => {
      commit(namespace, 'clear_cards', payload)
    })

    socket.on('set_on_turn', (payload, callback) => {
      commit(namespace, 'set_on_turn', payload)
      if (callback) {
        callback()
      }
    })

    socket.on('set_unlocked', payload => {
      commit(namespace, 'set_unlocked', payload)
    })

    socket.on('set_pass_unlocked', payload => {
      commit(namespace, 'set_pass_unlocked', payload)
    })

    socket.on('remove_card', payload => {
      commit(namespace, 'remove_card', payload)
    })

    socket.on('set_spot', payload => {
      commit(namespace, 'set_spot', payload)
    })

    socket.on('clear_hand_in_play', payload => {
      commit(namespace, 'clear_hand_in_play', payload)
    })

    socket.on('set_asker', payload => {
      commit(namespace, 'set_asker', payload)
    })

    socket.on('set_giver', payload => {
      commit(namespace, 'set_giver', payload)
    })

    socket.on('set_trading', payload => {
      commit(namespace, 'set_trading', payload)
    })

    socket.on('select_asking_option', payload => {
      commit(namespace, 'select_asking_option', payload)
    })

    socket.on('deselect_asking_option', payload => {
      commit(namespace, 'deselect_asking_option', payload)
    })

    socket.on('set_giving_options', payload => {
      commit(namespace, 'set_giving_options', payload)
    })

    socket.on('remove_asking_option', payload => {
      commit(namespace, 'remove_asking_option', payload)
    })

    socket.on('set_takes_remaining', payload => {
      commit(namespace, 'set_takes_remaining', payload)
    })

    socket.on('set_gives_remaining', payload => {
      commit(namespace, 'set_gives_remaining', payload)
    })

    socket.on('set_cards_remaining', payload => {
      commit(namespace, 'set_cards_remaining', payload)
    })

    socket.on('message', payload => {
      commit(namespace, 'message', payload)
    })

    socket.on('set_names', payload => {
      commit(namespace, 'set_names', payload)
    })

    socket.on('set_time', payload => {
      commit(namespace, 'set_time', payload)
    })

    socket.on('set_dot_color', payload => {
      commit(namespace, 'set_dot_color', payload)
    })
  }
}

export { server_plugin, server_browser_plugin }