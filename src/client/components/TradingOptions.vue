<template>
  <div>
    <v-btn
      class='rank'
      v-for='value in this.values'
      :key='52 + value'
      @click='$emit("ask", value)'
    >
      {{ ranks[value - 1] }}
    </v-btn>
  </div>
</template>

<script>
import Card from './Card.vue'

export default {
  name: 'TradingOptions',

  components: {
    Card
  },

  data () {
    return {
      values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
      ranks: ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
    }
  }
}
</script>

<style scoped>
.rank {
  height:30px;
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
