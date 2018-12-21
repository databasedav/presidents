<template>
  <button
    @click='try_select'
    :style='[style_object, selected_style]'
  >
    {{ value }}<br>{{ suit }}
  </button>
</template>

<script>
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
      this.socket.emit('card click', {'card': this.card})
    }
  }
}
</script>

<style scoped>
/* TODO: 10's are fatter than the other cards */
button {
  padding: 0px;
  padding-left: 10px;
  padding-right: 10px;
  margin: 4px;
  font-size: 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  background: lightgray;
  border: none;
  border-radius: 4px;
  position: relative;
}
</style>
