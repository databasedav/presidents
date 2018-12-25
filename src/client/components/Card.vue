<template>
  <v-btn
    class='card'
    color='grey lighten-3'
    @click='$emit("card_click", card)'
    :style='{color, top}'
  >
    {{ this.rank }}<br>{{ this.suit }}
  </v-btn>
</template>

<script>


// TODO: make cards a basic shape object (?) and then use it
//       as a button or not as needed.

const ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
const suits = ['♣', '♦', '♥', '♠']

export default {

  name: 'Card',

  props: {
    card: Number,
    is_selected: Boolean
  },

  computed: {

    rank () {
      return ranks[~~((this.card - 1) / 4)]
    },

    suit () {
      return suits[(this.card - 1) % 4]
    },

    color () {
      return [1, 2].includes((this.card - 1) % 4) ? '#ff0000' : '#000000'
    },

    top () {
      return this.is_selected ? '-10px' : '0px'
    }
  }
}
</script>

<style scoped>
/* TODO: 10's are fatter than the other cards */
.card {
  height:60px;
  width: 30px;
  margin: 4px;
  font-size: 20px;
  text-align: center;
  border-radius: 5px;
}
.v-btn {
  min-width: 0;
}
</style>
