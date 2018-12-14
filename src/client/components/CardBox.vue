<template>
  <div>
    <br><span>{{ current_hand_desc }}</span><br><br>
    <Card
      v-for='card in cards'
      :key='card'
      :card='card'
      :is_selected='cards_selected[card]'
    ></Card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Card from './Card.vue'

export default {

  name: 'CardBox',

  components: {
    Card
  },

  computed: {
    ...mapGetters({
      cards: 'cards_array',
      cards_selected: 'cards_selected_array',
      current_hand_desc: 'current_hand_desc'
    })
  },
}

</script>
