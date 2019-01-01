function create_namespaced_socket_plugin (namespace, socket) {
  
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

    socket.on('set_on_turn', payload => {
      commit(namespace, 'set_on_turn', payload)
    })

    socket.on('unlock', payload => {
      commit(namespace, 'unlock', payload)
    })

    socket.on('lock', payload => {
      commit(namespace, 'lock', payload)
    })

    socket.on('set_unlocked', payload => {
      commit(namespace, 'set_unlocked', payload)
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
  }
}
