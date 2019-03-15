<template>
  <Player/>
</template>

<script>
import Player from '../components/Player.vue'

export default {

  name: 'Presidents',

  components: {
    Player,
  },

  props: {
    rnsp: String
  },

  beforeCreate () {
    this.$store.dispatch('plugin_room', {
      rnsp: this.rnsp
    })
  },

  beforeRouteLeave(to, from, next) {
    const answer = window.confirm('do you really want to leave?')
    if (answer) {
      next()
    } else {
      next(false)
    }
  }
}
</script>
