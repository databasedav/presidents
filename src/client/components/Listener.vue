<template>
    
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import mutations from '../store/mutations';
import store from '../store/store'

function commit (namespace, event, payload) {
    store.commit(`${namespace}/${event}`, payload)
}

export default {

  name: 'Listener',

  props: {
    socket: io.Socket,
    namespace: String
  },

  // TODO: why on created instead of a different part of lifecycle?
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

    this.socket.on('set_hand_in_play',
      payload => commit(this.namespace, 'set_hand_in_play', payload)
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

    this.socket.on('unlock',
      payload => commit(this.namespace, 'unlock', payload)
    )

    this.socket.on('lock',
      payload => commit(this.namespace, 'lock', payload)
    )

    this.socket.on('set_unlocked',
      payload => commit(this.namespace, 'set_unlocked', payload)
    )

    this.socket.on('remove_card',
      payload => commit(this.namespace, 'remove_card', payload)
    )

    this.socket.on('set_spot',
      payload => commit(this.namespace, 'set_spot', payload)
    )

    this.socket.on('clear_hand_in_play',
      payload => commit(this.namespace, 'clear_hand_in_play', payload)
    )

    this.socket.on('set_asker',
      payload => commit(this.namespace, 'set_asker', payload)
    )

    this.socket.on('set_giver',
      payload => commit(this.namespace, 'set_giver', payload)
    )

    this.socket.on('set_trading',
      payload => commit(this.namespace, 'set_trading', payload)
    )

    this.socket.on('select_asking_option',
      payload => commit(this.namespace, 'select_asking_option', payload)
    )

    this.socket.on('deselect_asking_option',
      payload => commit(this.namespace, 'deselect_asking_option', payload)
    )

    this.socket.on('highlight_giving_options',
      payload => commit(this.namespace, 'highlight_giving_options', payload)
    )

    this.socket.on('remove_asking_option',
      payload => commit(this.namespace, 'remove_asking_option', payload)
    )

    this.socket.on('update_takes',
      payload => commit(this.namespace, 'update_takes', payload)
    )

    this.socket.on('update_gives',
      payload => commit(this.namespace, 'update_gives', payload)
    )

  },

}
</script>
