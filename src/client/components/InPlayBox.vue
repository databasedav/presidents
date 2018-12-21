<template>
  <div>
    <Card
      v-for='card in hand_in_play'
      :key='card'
      :card='card'
    ></Card><span v-if='this.hand_in_play.length == 0'></span><span v-else>{{ hand_in_play_str }}</span>
  </div>
</template>

<script>
import io from 'socket.io-client'
import Card from './Card.vue'

export default {

  name: 'CardBox',

  components: {
    Card
  },

  props: {
    socket: io.Socket,
    namespace: String
  },

  computed: {
    hand_in_play () {
      return this.$store.getters[`${this.namespace}/hand_in_play`]
    },

    hand_in_play_str () {
      return this.$store.getters[`${this.namespace}/hand_in_play_str`]
    },
  },
}
</script>