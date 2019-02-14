<template>
  <v-btn
    class='card'
    @click='$emit("card_click", card)'
    :style='{color, transform}'
    :outline='outline'
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
    is_selected: Boolean,
    is_giving_option: Boolean
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

    transform () {
      return this.is_selected ? 'rotate(15deg)': 'rotate(0deg)'
    },

    // border () {
    //   return this.is_giving_option ? 'border-color: #84FFFF !important' : null
    // },

    outline () {
      return this.is_giving_option
    }
  }
}
</script>

<style scoped>
/* TODO: border should not increase width of cards */
.v-btn.card {
  min-width: 0;
  height:70px;
  width: 35px;
  margin: 5px;
  font-size: 20px;
  text-align: center;
  border-radius: 5px;
  box-sizing: border-box !important;
  background-color: #E0E0E0 !important;
  border-color: #18FFFF !important;
}
</style>
