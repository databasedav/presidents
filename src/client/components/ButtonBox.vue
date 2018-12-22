<template>
  <div>
    <v-btn v-if='!play_unlocked' @click='try_unlock' color='error'>unlock</v-btn>
    <v-btn v-else @click='lock' color='error'>lock</v-btn>
    <v-btn color='info'>store hand</v-btn>
    <v-btn color='warning'>pass</v-btn>
    <v-btn v-if='play_unlocked' @click='try_play' color='success'>play</v-btn>
    <v-btn v-else disabled='true' color='success'>play</v-btn>
    <br>
    <button @click='restart'>restart</button>
  </div>
</template>

<script>
import io from 'socket.io-client'

export default {
  name: 'ButtonBox',
  props: {
    socket: io.Socket,
    namespace: String
  },
  methods: {
    restart () {
      this.socket.emit('restart')
    },

    try_unlock () {
      this.socket.emit('unlock')
    },

    lock () {
      this.socket.emit('lock')
    },

    try_play () {
      this.socket.emit('play')
    }
  },

  computed: {
    play_unlocked () {
      return this.$store.getters[`${this.namespace}/play_unlocked`]
    },
    
  },
}
</script>
