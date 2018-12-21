<template>
  <div>
    <v-btn color="error">unlock</v-btn>
    <v-btn color="info">store hand</v-btn>
    <v-btn color="success">play</v-btn>
    <br>
    <button @click='restart'>restart</button>
  </div>
</template>

<script>
import io from 'socket.io-client'

export default {
  name: 'ButtonBox',
  props: {
    socket: io.Socket
  },
  methods: {
    restart () {
      this.socket.emit('restart')
    }
  }
}
</script>
