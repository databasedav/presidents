<template>
    
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import store from '../store/store'

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
  },

}
</script>
