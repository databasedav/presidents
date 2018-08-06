<template>
  <button
    :class="functional ? 'selectable' : 'unselectable'"
    v-on="functional ? { click: try_select } : {}"
    :style='[style_object, selected_style]'
  >
    {{ value }}
    <br>
    {{ suite }}
  </button>
</template>

<script>
const values = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
const suites = ['♣', '♦', '♥', '♠']

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
      suite: suites[(this.card - 1) % 4],
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

<style scoped>
button.selectable {
  text-align: center;
  text-decoration: none;
  display: inline-block;
  border: none;
  border-radius: 4px;
  font-size: 25px;
  margin: 2px;
  position: relative;
}
button.unselectable {
  text-align: center;
  text-decoration: none;
  display: inline-block;
  border: none;
  border-radius: 4px;
  font-size: 15px;
  margin: 2px;
  position: relative;
}
/* TODO: only allow hover on mouseover in non mobile browsers (maybe?) */
</style>
