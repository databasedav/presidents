<template>
  <button
    @click='clickCard'
    :style="{
              top: isClicked ? '-10px' : '0px',
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
    card: Number
  },
  data () {
    return {
      value: values[~~((this.card - 1) / 4)],
      suite: suites[(this.card - 1) % 4],
      isClicked: false
    }
  },
  methods: {
    clickCard () {
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
