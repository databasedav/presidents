<template>
  <v-btn
    class="functional ? selectable : unselectable"
    depressed
    v-on="functional ? { click: try_select } : {}"
    :style='[style_object, selected_style]'
  >
    {{ value }}<br>{{ suit }}
  </v-btn>
</template>

<script>
const values = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
const suits = ['♣', '♦', '♥', '♠']

export default {
  name: 'Card',
  props: {
    card: Number,
    is_selected: Boolean,
    functional: Boolean
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
      this.$socket.emit('card click', {'card': this.card})
    }
  }
}
</script>

<style>
.selectable {
  height: auto;
  width: auto;
  margin: 6px;
  padding: 0px;
  padding-left: 20px;
  padding-right: 20px;
  min-width: 0;
  font-size: 35px;
}

/* .unselectable {
  height: auto;
  width: auto;
  margin: 6px;
  padding: 0px;
  padding-left: 20px;
  padding-right: 20px;
  min-width: 0;
  font-size: 15px;
} */
</style>
