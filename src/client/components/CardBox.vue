<template>
  <div>
    <br>
      <span 
        v-if='current_hand_str.length === 0 || current_hand_str === ": empty hand"'
      >
        Click on cards to add them to your current hand!
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
      :is_selected='cards_selected[card]'
      @card_click='$emit("card_click", $event)'
    ></Card>
  </div>
</template>

<script>
// @card_click='$emit("card_click", $event)'
import io from 'socket.io-client'
import Card from './Card.vue'

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
      return namespaced_getter(this.namespace, 'cards_array')
    },
    cards_selected () {
      return namespaced_getter(this.namespace, 'cards_selected_array')
    },
    current_hand_str () {
      return namespaced_getter(this.namespace, 'current_hand_str')
    },
  }
}
</script>
