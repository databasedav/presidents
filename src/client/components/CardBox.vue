<template>
  <div>
    <br>
      <span v-if="current_hand_str != ': empty hand'">{{ current_hand_str }}</span>
      <span v-else>Click on cards to add them to your current hand!</span>
    <br><br>
    <Card
      v-for='card in cards'
      :key='card'
      :card='card'
      :is_selected='cards_selected[card]'
    ></Card>
  </div>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import Card from './Card.vue'

const { mapState } = createNamespacedHelpers('a')

export default {

  name: 'CardBox',

  components: {
    Card
  },

  computed: {
    ...mapState({
      // cards: state => state.cards_array,
      // cards_selected: state => state.cards_selected_array,
      // current_hand_str: state => state.current_hand_str,
      cards: 'cards_array',
      cards_selected: 'cards_selected_array',
      current_hand_str: 'current_hand_str'
    })
  },
}

</script>
