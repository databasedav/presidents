<template>
  <div>
    <br>
      <span 
        v-if='current_hand_str.length === 0 || current_hand_str === ": empty hand"'
      >
        select cards to add them to your current hand
      </span>

      <span
        v-else
      >
        {{ current_hand_str }}
      </span>

    <br>
    <br>
    
    <Card
      v-for='card in cards'
      :key='card'
      :card='card'
      :is_selected='cards_selected_arr[card]'
      :is_giving_option='giving_options_arr[card]'
      @card_click='$emit("card_click", $event)'
      :namespace='namespace'
    ></Card>
  </div>
</template>

<script>
// @card_click='$emit("card_click", $event)'
import io from 'socket.io-client'
import Card from './Card.vue'
import { mapState } from 'vuex'

import { namespaced_getter } from '../utils/utils'

export default {

  name: 'CardBox',

  components: {
    Card
  },

  props: {
    namespace: String
  },

  computed: {

    cards () {
      return this.$store.state[this.namespace].cards_arr
    },

    cards_selected_arr () {
      return this.$store.state[this.namespace].cards_selected_arr
    },

    current_hand_str () {
      return this.$store.state[this.namespace].current_hand_str
    },

    giving_options_arr () {
      return this.$store.state[this.namespace].giving_options_arr
    }
  }
}
</script>
