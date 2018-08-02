<template>
  <button
    @click='trySelect'
    :style="{
              top: isSelected ? '-10px' : '0px',
              color: [1, 2].includes((this.card - 1) % 4) ? '#ff0000' : '#000000'
            }"
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
    isSelected: Boolean
  },
  data () {
    return {
      value: values[~~((this.card - 1) / 4)],
      suite: suites[(this.card - 1) % 4],
      
    }
  },
  methods: {
    trySelect () {
      this.$socket.emit('card click', {'card': this.card})
      if (this.isClicked) {
        this.$socket.emit('remove card', {'card': this.card})
      } else if (this.$store.getters.current_hand_in_spot(this.spot).length === 5) {
        return
      } else {
        this.$socket.emit('add card', {'card': this.card})
      }
      this.isClicked = !this.isClicked
    }
  }
}
</script>

<style scoped>
button {
  text-align: center;
  text-decoration: none;
  display: inline-block;
  border: none;
  border-radius: 4px;
  font-size: 25px;
  margin: 2px;
  position: relative;
}
/* TODO: only allow hover on mouseover in non mobile browsers (maybe?) */
</style>
