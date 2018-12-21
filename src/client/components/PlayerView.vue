<template>
  <div>
    <!-- <button @click='restart'>restart</button> -->
    <Receiver
      :socket='this.socket'
      :namespace='this.namespace'
    ></Receiver>
    <CardBox
      :socket='this.socket'
      :namespace='this.namespace'
    ></CardBox>
  </div>
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import Receiver from './Receiver.vue'

export default {
  data () {
    return {
      socket: io.Socket
    }
  },

  props: {
    namespace: String
  },

  components: {
    CardBox,
    Receiver
  },

  methods: {
    restart () {
      this.socket.emit('restart')
    }
  },

  created () {
    this.socket = io(`//${window.location.host}`, { forceNew: true })
  },


}
</script>
