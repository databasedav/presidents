<template>
  <v-btn class='card'
    color='grey lighten-3'
    @click='try_select'
    :style='[style_object, selected_style]'
  >
    {{ value }}<br>{{ suit }}
  </v-btn>
</template>

<script>
// TODO: make cards a basic shape object (?) and then use it
//       as a button or not as needed.

import io from 'socket.io-client'

const values = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
const suits = ['♣', '♦', '♥', '♠']

export default {
  name: 'Card',
  props: {
    card: Number,
    is_selected: Boolean,
    socket: io.Socket
  },
  data () {
    return {
      value: values[~~((this.card - 1) / 4)],
      suit: suits[(this.card - 1) % 4],
      style_object: {
        color: [1, 2].includes((this.card - 1) % 4) ? '#ff0000' : '#000000'
      }
    }
  },
  computed: {
    selected_style () {
      return {
        top: this.is_selected ? '-10px' : '0px'
      }
    }
  },
  methods: {
    try_select () {
      this.socket.emit('card_click', {'card': this.card})
    }
  }
}
</script>

<style scoped>
/* TODO: 10's are fatter than the other cards */
.card {
  height:60px;
  width: 30px;
  /* padding-left: 10px;
  padding-right: 10px; */
  margin: 4px;
  font-size: 20px;
  text-align: center;
  text-decoration: none;
  display: inline-flex;
  /* color: rgb(153, 153, 153); */
  border: none;
  border-radius: 4px;
}
.v-btn {
  min-width: 0;
}
</style>
