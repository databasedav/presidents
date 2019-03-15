<template>
  <Player/>

</template>

<script>
import Player from '../components/Player.vue'
import { mapState } from 'vuex'
import { createSinglePlayerStore } from '../utils/utils'
import { create_namespaced_player_socket_plugin } from '../store/plugins'

export default {

  name: 'Presidents',

  components: {
    Player,
  },

  data () {
    return {
      dialog: false
    }
  },

  beforeCreate () {
    room_plugin()
  },

  created () {
    this.$store.registerModule(this.namespace, createSinglePlayerStore())
    const plugin = create_namespaced_player_socket_plugin(this.socket, this.namespace)
    plugin(this.$store)
  },

  // beforeDestroy () {
  //   this.socket.disconnect()
  // },

  beforeRouteLeave(to, from, next) {
    const answer = window.confirm('do you really want to leave?')
    if (answer) {
      this.socket.disconnect()
      next()
    } else {
      next(false)
    }
  },

  computed: {
    ...mapState({
      socket: 'socket',
      namespace: 'namespace'
    })
  }
}
</script>
