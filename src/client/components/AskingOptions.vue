<template>
  <div>
    <v-btn
      class='rank'
      v-for='value in this.ask_values'
      :key='52 + value'
      :outline='ask_values_selected_arr[value]'
      @click='$emit("asking_click", value)'
    >
      {{ ranks[value - 1] }}
    </v-btn>
  </div>
</template>

<script>
import Card from './Card.vue'

export default {
  name: 'AskingOptions',

  components: {
    Card
  },

  props: {
    namespace: String
  },

  data () {
    return {
      // TODO: where to put this?
      ranks: ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
    }
  },

  computed: {
    ask_values () {
      return this.$store.state[this.namespace].ask_values_arr
    },

    ask_values_selected_arr () {
      return this.$store.state[this.namespace].ask_values_selected_arr
    },


  },

  methods: {
  
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
