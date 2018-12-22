<template>
  <div>
    <Card
      v-for='card in hand_in_play'
      :key='card'
      :card='card'
    ></Card><br>
    <span v-if='this.hand_in_play.length == 0'>waiting for hand to be played...</span>
    <span v-else>{{ hand_in_play_desc }}</span>
  </div>
</template>

<script>
import io from 'socket.io-client'
import Card from './Card.vue'

import { namespaced_getter } from '../utils/utils'

export default {

  name: 'CardBox',

  components: {
    Card
  },

  props: {
    namespace: String
  },

  computed: {
    hand_in_play () {
      return namespaced_getter(this.namespace, 'hand_in_play')
    },

    hand_in_play_desc () {
      return namespaced_getter(this.namespace, 'hand_in_play_desc')
    },
  },
}
</script>