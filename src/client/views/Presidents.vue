<template>
  <div>
    <Player/>
  </div>
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

  created () {
    this.$store.registerModule(this.namespace, createSinglePlayerStore())
    const plugin = create_namespaced_player_socket_plugin(this.socket, this.namespace)
    plugin(this.$store)
  },

  computed: {
    ...mapState({
      socket: 'socket',
      namespace: 'namespace'
    })
  }
}
</script>
