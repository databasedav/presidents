<template>
  <v-btn
    class="card"
    @click="$emit('card_click', card)"
    :style="{ color, transform, 'background-color': bc }"
    height="70"
    width="35"
  >
    {{ this.rank }}
    <br>
    {{ this.suit }}
  </v-btn>
</template>

<script>
// TODO: make cards a basic shape object (?) and then use it
//       as a button or not as needed.

const ranks = [
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "J",
  "Q",
  "K",
  "A",
  "2"
];
const suits = ["♣", "♦", "♥", "♠"];

export default {
  name: "Card",

  props: {
    card: Number,
    selected: Boolean,
    is_giving_option: Boolean
  },

  computed: {
    rank () {
      return ranks[~~((this.card - 1) / 4)];
    },

    suit () {
      return suits[(this.card - 1) % 4];
    },

    color () {
      return [1, 2].includes((this.card - 1) % 4) ? "#ff0000" : "#000000";
    },

    transform () {
      return this.selected ? "rotate(15deg)" : "rotate(0deg)";
    },

    bc () {
      return this.is_giving_option ? "#696969": "#e0e0e0";
    }
  }
};
</script>

<style scoped>
/* TODO: border should not increase width of cards */
.v-btn.card {
  min-width: 0;
  margin: 5px;
  font-size: 20px;
  text-align: center;
  border-radius: 5px;
  /* box-sizing: border-box !important; */
  /* background-color: #e0e0e0 !important; */
  /* border-color: #18ffff !important; */
}
</style>
