<template>
  <div>
    <v-btn
      class='rank'
      v-for='value in this.asking_options'
      :key='52 + value'
      :outline='asking_options_selected_arr[value]'
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
    asking_options () {
      return this.$store.state[this.namespace].asking_options_arr
    },

    asking_options_selected_arr () {
      return this.$store.state[this.namespace].asking_options_selected_arr
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
