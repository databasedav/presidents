<template>
  <div>
    <v-btn
      class='rank'
      v-for='value in this.values'
      :key='52 + value'
      :outline='selected_arr[value]'
      @click='click'
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
      ranks: ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2'],
      selected_arr: Array(13).fill(false)
    }
  },

  methods: {
    click (value) {
      if (this.selected_arr[value]) {
        this.selected_arr.splice(value, 1, false)
        this.$emit('select_for_asking', 0)
      } else {
        this.selected_arr.fill(false)
        this.selected_arr.splice(value, 1, true)
        this.$emit('select_for_asking', value)
      }
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
