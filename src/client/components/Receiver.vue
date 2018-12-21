<template>
    
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import store from '../store/store'

// commits mutation to (namespaced) store
function commit (namespace, event, payload) {
  store.commit(`${namespace}/${event}`, payload)
}

export default {

  name: 'Receiver',

  props: {
    socket: io.Socket,
    namespace: String
  },

  created () {
    this.socket.on('add_card',
      payload => commit(this.namespace, 'add_card', payload)
    )

    this.socket.on('select_card',
      payload => commit(this.namespace, 'select_card', payload)
    )

    this.socket.on('deselect_card',
      payload => commit(this.namespace, 'deselect_card', payload)
    )

    this.socket.on('update_current_hand_str',
      payload => commit(this.namespace, 'update_current_hand_str', payload)
    )

    this.socket.on('update_alert_str',
      payload => commit(this.namespace, 'update_alert_str', payload)
    )

    this.socket.on('update_hand_in_play',
      payload => commit(this.namespace, 'update_hand_in_play', payload)
    )

    this.socket.on('alert',
      payload => commit(this.namespace, 'alert', payload)
    )

    this.socket.on('clear_cards',
      payload => commit(this.namespace, 'clear_cards', payload)
    )

    this.socket.on('flip_turn',
      payload => commit(this.namespace, 'flip_turn', payload)
    )

    this.socket.on('all_off_turn',
      payload => commit(this.namespace, 'all_off_turn', payload)
    )

    this.socket.on('unlock_play',
      payload => commit(this.namespace, 'unlock_play', payload)
    )

    this.socket.on('lock_play',
      payload => commit(this.namespace, 'lock_play', payload)
    )
  },

}
</script>
