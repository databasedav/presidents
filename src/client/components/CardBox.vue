<template>
  <div>
    <!-- <button @click='restart'>restart</button> -->
    <br>
      <span v-if="current_hand_str != ': empty hand'">{{ current_hand_str }}</span>
      <span v-else>Click on cards to add them to your current hand!</span>
    <br><br>
    <Card
      v-for='card in cards'
      :key='card'
      :card='card'
      :is_selected='cards_selected[card]'
      :socket='socket'
    ></Card>
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
    cards () {
      return this.$store.getters[`${this.namespace}/cards_array`]
    },
    cards_selected () {
      return this.$store.getters[`${this.namespace}/cards_selected_array`]
    },
    current_hand_str () {
      return this.$store.getters[`${this.namespace}/current_hand_str`]
    },
  },
}
</script>
